"""
Track Animation Module

Provides animated top-down track visualization with:
- Progressive line drawing around the track
- Ghost comparison (your lap vs reference)
- Speed-colored racing lines
- Corner zoom and analysis
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class TrackConfig:
    """Configuration for a track's visualization"""
    name: str
    display_name: str
    image_path: Optional[str] = None  # Path to track image
    
    # Image bounds (for mapping coordinates to image)
    # These map world coordinates to image pixel coordinates
    x_min: float = 0
    x_max: float = 1000
    y_min: float = 0
    y_max: float = 1000
    
    # Image dimensions
    img_width: int = 800
    img_height: int = 600
    
    # Track direction (for proper animation)
    clockwise: bool = True
    
    # Start/finish line position (normalized 0-1)
    start_finish_pos: float = 0.0
    
    # Corner positions for labels
    corners: List[Dict] = None
    
    def __post_init__(self):
        if self.corners is None:
            self.corners = []


# Pre-configured tracks (can be expanded)
TRACK_CONFIGS = {
    "monza": TrackConfig(
        name="monza",
        display_name="Monza",
        x_min=-500, x_max=1500,
        y_min=-200, y_max=1200,
        clockwise=True,
        corners=[
            {"name": "T1", "x": 0.08, "y": 0.3},
            {"name": "Curva Grande", "x": 0.15, "y": 0.6},
            {"name": "Lesmo 1", "x": 0.4, "y": 0.8},
            {"name": "Lesmo 2", "x": 0.45, "y": 0.75},
            {"name": "Ascari", "x": 0.62, "y": 0.5},
            {"name": "Parabolica", "x": 0.85, "y": 0.2},
        ]
    ),
    "spa": TrackConfig(
        name="spa",
        display_name="Spa-Francorchamps",
        x_min=-1000, x_max=2000,
        y_min=-500, y_max=1500,
        clockwise=True,
        corners=[
            {"name": "La Source", "x": 0.02, "y": 0.5},
            {"name": "Eau Rouge", "x": 0.08, "y": 0.3},
            {"name": "Les Combes", "x": 0.2, "y": 0.8},
            {"name": "Pouhon", "x": 0.4, "y": 0.6},
            {"name": "Stavelot", "x": 0.58, "y": 0.4},
            {"name": "Blanchimont", "x": 0.75, "y": 0.7},
            {"name": "Bus Stop", "x": 0.9, "y": 0.5},
        ]
    ),
    "nurburgring": TrackConfig(
        name="nurburgring",
        display_name="Nürburgring GP",
        x_min=-400, x_max=800,
        y_min=-200, y_max=600,
        clockwise=True,
        corners=[
            {"name": "T1", "x": 0.05, "y": 0.4},
            {"name": "Mercedes Arena", "x": 0.15, "y": 0.6},
            {"name": "Ford Kurve", "x": 0.35, "y": 0.7},
            {"name": "Dunlop", "x": 0.45, "y": 0.5},
            {"name": "Schumacher S", "x": 0.7, "y": 0.3},
            {"name": "Coca Cola", "x": 0.85, "y": 0.5},
        ]
    ),
}


def get_track_config(track_name: str) -> TrackConfig:
    """Get track configuration by name"""
    track_lower = track_name.lower()
    for key, config in TRACK_CONFIGS.items():
        if key in track_lower:
            return config
    # Return default config
    return TrackConfig(name=track_name, display_name=track_name)


class TrackAnimator:
    """
    Creates animated track visualizations.
    
    Usage:
        animator = TrackAnimator(track_config)
        fig = animator.create_animation(your_lap, reference_lap)
    """
    
    def __init__(self, track_config: TrackConfig):
        self.config = track_config
        
    def create_static_comparison(self, 
                                  lap1: pd.DataFrame, 
                                  lap2: Optional[pd.DataFrame] = None,
                                  color_by: str = "speed") -> go.Figure:
        """
        Create a static track map with racing lines.
        
        Args:
            lap1: Your lap telemetry (needs world_x, world_y or position)
            lap2: Reference lap (optional)
            color_by: "speed", "throttle", "brake", or "delta"
        """
        fig = go.Figure()
        
        # Get coordinates
        x1, y1, colors1 = self._extract_coordinates(lap1, color_by)
        
        # Plot your line
        fig.add_trace(go.Scatter(
            x=x1, y=y1,
            mode='lines+markers',
            marker=dict(
                size=4,
                color=colors1,
                colorscale='RdYlGn' if color_by == "delta" else 'Viridis',
                colorbar=dict(title=color_by.title()),
                showscale=True,
            ),
            line=dict(width=2, color='rgba(100,100,100,0.3)'),
            name='Your Lap',
            hovertemplate=f'{color_by}: %{{marker.color:.1f}}<extra></extra>',
        ))
        
        # Plot reference line if provided
        if lap2 is not None:
            x2, y2, colors2 = self._extract_coordinates(lap2, color_by)
            fig.add_trace(go.Scatter(
                x=x2, y=y2,
                mode='lines',
                line=dict(width=3, color='rgba(0,255,0,0.5)', dash='dash'),
                name='Reference',
            ))
        
        # Add corner labels
        self._add_corner_labels(fig, x1, y1)
        
        # Layout
        fig.update_layout(
            title=f"{self.config.display_name} - Racing Line",
            template="plotly_dark",
            showlegend=True,
            xaxis=dict(
                scaleanchor="y",
                scaleratio=1,
                showgrid=False,
                zeroline=False,
                showticklabels=False,
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
            ),
            height=700,
        )
        
        return fig
    
    def create_animation(self,
                         lap1: pd.DataFrame,
                         lap2: Optional[pd.DataFrame] = None,
                         fps: int = 30,
                         duration_seconds: float = 10.0) -> go.Figure:
        """
        Create an animated track visualization.
        
        Shows progressive line drawing with optional ghost comparison.
        
        Args:
            lap1: Your lap telemetry
            lap2: Reference lap (ghost)
            fps: Animation frames per second
            duration_seconds: Total animation duration
        """
        # Get coordinates
        x1, y1, speeds1 = self._extract_coordinates(lap1, "speed")
        
        if lap2 is not None:
            x2, y2, speeds2 = self._extract_coordinates(lap2, "speed")
        else:
            x2, y2, speeds2 = None, None, None
        
        # Calculate number of frames
        n_frames = int(fps * duration_seconds)
        n_points = len(x1)
        points_per_frame = max(1, n_points // n_frames)
        
        # Create figure with initial empty state
        fig = go.Figure()
        
        # Add track outline (from first lap's full path, faded)
        fig.add_trace(go.Scatter(
            x=x1, y=y1,
            mode='lines',
            line=dict(width=1, color='rgba(100,100,100,0.2)'),
            name='Track',
            hoverinfo='skip',
        ))
        
        # Add animated line (your lap) - starts empty
        fig.add_trace(go.Scatter(
            x=[x1[0]], y=[y1[0]],
            mode='lines+markers',
            line=dict(width=3, color='#ff4444'),
            marker=dict(size=12, color='#ff4444', symbol='circle'),
            name='Your Lap',
        ))
        
        # Add ghost line if reference provided
        if x2 is not None:
            fig.add_trace(go.Scatter(
                x=[x2[0]], y=[y2[0]],
                mode='lines+markers',
                line=dict(width=3, color='#44ff44'),
                marker=dict(size=12, color='#44ff44', symbol='circle'),
                name='Reference',
            ))
        
        # Create animation frames
        frames = []
        for i in range(n_frames):
            idx = min((i + 1) * points_per_frame, n_points)
            
            frame_data = [
                # Track outline (unchanged)
                go.Scatter(x=x1, y=y1),
                # Your lap progress
                go.Scatter(
                    x=x1[:idx], 
                    y=y1[:idx],
                    marker=dict(size=[4]*(idx-1) + [12] if idx > 0 else [12]),
                ),
            ]
            
            if x2 is not None:
                idx2 = min((i + 1) * points_per_frame, len(x2))
                frame_data.append(go.Scatter(
                    x=x2[:idx2],
                    y=y2[:idx2],
                    marker=dict(size=[4]*(idx2-1) + [12] if idx2 > 0 else [12]),
                ))
            
            frames.append(go.Frame(data=frame_data, name=str(i)))
        
        fig.frames = frames
        
        # Add play/pause buttons
        fig.update_layout(
            title=f"{self.config.display_name} - Lap Animation",
            template="plotly_dark",
            showlegend=True,
            xaxis=dict(
                scaleanchor="y",
                scaleratio=1,
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[min(x1) - 50, max(x1) + 50],
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[min(y1) - 50, max(y1) + 50],
            ),
            height=700,
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    y=1.15,
                    x=0.5,
                    xanchor="center",
                    buttons=[
                        dict(
                            label="▶ Play",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=1000/fps, redraw=True),
                                    fromcurrent=True,
                                    mode="immediate",
                                )
                            ],
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                dict(
                                    frame=dict(duration=0, redraw=False),
                                    mode="immediate",
                                )
                            ],
                        ),
                        dict(
                            label="↺ Reset",
                            method="animate",
                            args=[
                                [str(0)],
                                dict(
                                    frame=dict(duration=0, redraw=True),
                                    mode="immediate",
                                )
                            ],
                        ),
                    ],
                ),
            ],
            sliders=[
                dict(
                    active=0,
                    yanchor="top",
                    xanchor="left",
                    currentvalue=dict(
                        prefix="Progress: ",
                        visible=True,
                        xanchor="center",
                    ),
                    pad=dict(b=10, t=50),
                    len=0.9,
                    x=0.05,
                    y=0,
                    steps=[
                        dict(
                            args=[[str(i)], dict(frame=dict(duration=0, redraw=True), mode="immediate")],
                            label=f"{int(100*i/n_frames)}%",
                            method="animate",
                        )
                        for i in range(0, n_frames, max(1, n_frames // 20))
                    ],
                ),
            ],
        )
        
        return fig
    
    def create_corner_zoom(self,
                           lap1: pd.DataFrame,
                           corner_position: float,
                           window: float = 0.05,
                           lap2: Optional[pd.DataFrame] = None) -> go.Figure:
        """
        Create a zoomed view of a specific corner.
        
        Args:
            lap1: Your lap telemetry
            corner_position: Normalized track position (0-1)
            window: How much track to show (0.05 = 5% of track)
            lap2: Reference lap (optional)
        """
        # Filter to corner region
        mask1 = (lap1['position'] >= corner_position - window) & \
                (lap1['position'] <= corner_position + window)
        corner_data1 = lap1[mask1]
        
        x1, y1, speeds1 = self._extract_coordinates(corner_data1, "speed")
        
        fig = go.Figure()
        
        # Your line with speed coloring
        fig.add_trace(go.Scatter(
            x=x1, y=y1,
            mode='lines+markers',
            marker=dict(
                size=8,
                color=speeds1,
                colorscale='Viridis',
                colorbar=dict(title='Speed (km/h)'),
            ),
            line=dict(width=3, color='rgba(255,100,100,0.5)'),
            name='Your Line',
            hovertemplate='Speed: %{marker.color:.0f} km/h<extra></extra>',
        ))
        
        # Reference line
        if lap2 is not None:
            mask2 = (lap2['position'] >= corner_position - window) & \
                    (lap2['position'] <= corner_position + window)
            corner_data2 = lap2[mask2]
            x2, y2, _ = self._extract_coordinates(corner_data2, "speed")
            
            fig.add_trace(go.Scatter(
                x=x2, y=y2,
                mode='lines',
                line=dict(width=4, color='#44ff44', dash='dash'),
                name='Ideal Line',
            ))
        
        # Mark entry, apex, exit
        if len(corner_data1) > 0:
            # Apex = minimum speed point
            apex_idx = corner_data1['speed_kmh'].idxmin() if 'speed_kmh' in corner_data1.columns else len(corner_data1) // 2
            
            fig.add_trace(go.Scatter(
                x=[x1[len(x1)//2]], y=[y1[len(y1)//2]],
                mode='markers+text',
                marker=dict(size=15, color='yellow', symbol='star'),
                text=['APEX'],
                textposition='top center',
                name='Apex',
            ))
        
        fig.update_layout(
            title="Corner Detail",
            template="plotly_dark",
            xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False),
            yaxis=dict(showgrid=False),
            height=500,
        )
        
        return fig
    
    def _extract_coordinates(self, 
                             telemetry: pd.DataFrame,
                             color_by: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract x, y coordinates and color values from telemetry"""
        
        # Try world coordinates first
        if 'world_x' in telemetry.columns and 'world_z' in telemetry.columns:
            x = telemetry['world_x'].values
            y = telemetry['world_z'].values  # Z is typically the "forward" axis
        elif 'world_x' in telemetry.columns and 'world_y' in telemetry.columns:
            x = telemetry['world_x'].values
            y = telemetry['world_y'].values
        else:
            # Generate from position (circular approximation)
            positions = telemetry['position'].values
            # Create a rough track shape
            x = np.cos(positions * 2 * np.pi) * 500 + np.sin(positions * 6 * np.pi) * 100
            y = np.sin(positions * 2 * np.pi) * 300 + np.cos(positions * 4 * np.pi) * 50
        
        # Get color values
        if color_by == "speed" and 'speed_kmh' in telemetry.columns:
            colors = telemetry['speed_kmh'].values
        elif color_by == "throttle" and 'throttle' in telemetry.columns:
            colors = telemetry['throttle'].values * 100
        elif color_by == "brake" and 'brake' in telemetry.columns:
            colors = telemetry['brake'].values * 100
        else:
            colors = np.linspace(0, 100, len(x))
        
        return x, y, colors
    
    def _add_corner_labels(self, fig: go.Figure, x: np.ndarray, y: np.ndarray):
        """Add corner labels to the track"""
        for corner in self.config.corners:
            # Approximate position on track
            idx = int(corner.get('x', 0.5) * len(x))
            if idx < len(x):
                fig.add_annotation(
                    x=x[idx],
                    y=y[idx],
                    text=corner['name'],
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    ax=20,
                    ay=-20,
                    font=dict(size=10, color='white'),
                )


def create_lap_comparison_animation(lap1: pd.DataFrame,
                                     lap2: pd.DataFrame,
                                     track_name: str) -> go.Figure:
    """
    Convenience function to create a ghost comparison animation.
    
    Args:
        lap1: Your lap
        lap2: Reference lap
        track_name: Name of the track
        
    Returns:
        Plotly figure with animation
    """
    config = get_track_config(track_name)
    animator = TrackAnimator(config)
    return animator.create_animation(lap1, lap2)


def create_racing_line_map(lap: pd.DataFrame,
                           track_name: str,
                           color_by: str = "speed") -> go.Figure:
    """
    Convenience function to create a static racing line map.
    
    Args:
        lap: Lap telemetry
        track_name: Name of the track
        color_by: What to color the line by
        
    Returns:
        Plotly figure
    """
    config = get_track_config(track_name)
    animator = TrackAnimator(config)
    return animator.create_static_comparison(lap, color_by=color_by)
