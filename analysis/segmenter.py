"""
Corner Segmentation

Automatically detects corners in telemetry data using:
- Steering angle changes
- Speed minima (apex detection)
- Braking zones
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class Corner:
    """Represents a detected corner"""
    corner_id: int
    name: str = ""  # e.g., "T1", "Variante del Rettifilo"
    
    # Track positions (0-1 normalized)
    entry_position: float = 0.0
    apex_position: float = 0.0
    exit_position: float = 0.0
    
    # Key metrics
    brake_point: float = 0.0      # Position where braking starts
    min_speed_kmh: float = 0.0    # Apex speed
    entry_speed_kmh: float = 0.0  # Speed at entry
    exit_speed_kmh: float = 0.0   # Speed at exit
    
    # Steering
    max_steering_angle: float = 0.0  # Peak steering input
    
    # Classification
    corner_type: str = "medium"  # slow, medium, fast, chicane


@dataclass
class CornerSegmenter:
    """
    Detects corners in lap telemetry data.
    
    Algorithm:
    1. Find braking zones (brake > threshold)
    2. Find speed minima within braking zones
    3. Detect entry (brake point) and exit (throttle > threshold)
    4. Classify corner type based on min speed
    """
    
    # Detection parameters
    brake_threshold: float = 0.1      # Minimum brake input to consider
    throttle_threshold: float = 0.8   # Throttle level indicating corner exit
    steering_threshold: float = 5.0   # Minimum steering to consider (degrees)
    min_corner_length: float = 0.01   # Minimum track distance for a corner
    smoothing_window: int = 5         # Rolling average window for noise reduction
    
    def detect_corners(self, telemetry: pd.DataFrame) -> List[Corner]:
        """
        Detect corners in lap telemetry.
        
        Args:
            telemetry: DataFrame with columns:
                - position: normalized track position (0-1)
                - speed_kmh: speed in km/h
                - brake: brake input (0-1)
                - throttle: throttle input (0-1)
                - steering: steering angle (degrees)
                
        Returns:
            List of detected Corner objects
        """
        if telemetry.empty:
            return []
        
        # Sort by position
        df = telemetry.sort_values("position").copy()
        
        # Smooth the data
        df["speed_smooth"] = df["speed_kmh"].rolling(
            self.smoothing_window, center=True, min_periods=1
        ).mean()
        df["brake_smooth"] = df["brake"].rolling(
            self.smoothing_window, center=True, min_periods=1
        ).mean()
        
        # Find braking zones
        braking_zones = self._find_braking_zones(df)
        
        # Detect corners from braking zones
        corners = []
        for zone_idx, (start_idx, end_idx) in enumerate(braking_zones):
            corner = self._analyze_corner(df, start_idx, end_idx, zone_idx + 1)
            if corner:
                corners.append(corner)
        
        return corners
    
    def _find_braking_zones(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        """Find contiguous braking zones in the data"""
        zones = []
        in_zone = False
        zone_start = 0
        
        brake_values = df["brake_smooth"].values
        
        for i, brake in enumerate(brake_values):
            if brake > self.brake_threshold:
                if not in_zone:
                    zone_start = i
                    in_zone = True
            else:
                if in_zone:
                    # End of braking zone - extend to find full corner
                    zone_end = self._find_corner_exit(df, i)
                    zones.append((zone_start, zone_end))
                    in_zone = False
        
        # Handle zone at end of lap
        if in_zone:
            zones.append((zone_start, len(df) - 1))
        
        return zones
    
    def _find_corner_exit(self, df: pd.DataFrame, brake_end_idx: int) -> int:
        """Find where the corner ends (full throttle application)"""
        throttle_values = df["throttle"].values
        
        for i in range(brake_end_idx, len(throttle_values)):
            if throttle_values[i] > self.throttle_threshold:
                return i
        
        return len(df) - 1
    
    def _analyze_corner(self, df: pd.DataFrame, start_idx: int, end_idx: int, 
                        corner_id: int) -> Optional[Corner]:
        """Analyze a detected corner zone"""
        if end_idx <= start_idx:
            return None
        
        corner_data = df.iloc[start_idx:end_idx + 1]
        
        # Check minimum length
        pos_delta = corner_data["position"].iloc[-1] - corner_data["position"].iloc[0]
        if pos_delta < self.min_corner_length:
            return None
        
        # Find apex (minimum speed point)
        apex_idx = corner_data["speed_smooth"].idxmin()
        apex_row = df.loc[apex_idx]
        
        # Entry and exit
        entry_row = corner_data.iloc[0]
        exit_row = corner_data.iloc[-1]
        
        # Find brake point (where heavy braking starts)
        brake_point_pos = entry_row["position"]
        for _, row in corner_data.iterrows():
            if row["brake"] > 0.5:  # Significant braking
                brake_point_pos = row["position"]
                break
        
        # Max steering
        max_steering = corner_data["steering"].abs().max()
        
        # Classify corner
        min_speed = apex_row["speed_smooth"]
        if min_speed < 80:
            corner_type = "slow"
        elif min_speed < 150:
            corner_type = "medium"
        else:
            corner_type = "fast"
        
        return Corner(
            corner_id=corner_id,
            name=f"T{corner_id}",
            entry_position=entry_row["position"],
            apex_position=apex_row["position"],
            exit_position=exit_row["position"],
            brake_point=brake_point_pos,
            min_speed_kmh=min_speed,
            entry_speed_kmh=entry_row["speed_smooth"],
            exit_speed_kmh=exit_row["speed_smooth"],
            max_steering_angle=max_steering,
            corner_type=corner_type,
        )
    
    def get_corner_telemetry(self, telemetry: pd.DataFrame, corner: Corner,
                              padding: float = 0.02) -> pd.DataFrame:
        """
        Extract telemetry for a specific corner with padding.
        
        Args:
            telemetry: Full lap telemetry
            corner: Corner to extract
            padding: Track position padding before/after corner
            
        Returns:
            DataFrame with corner telemetry
        """
        start_pos = max(0, corner.entry_position - padding)
        end_pos = min(1, corner.exit_position + padding)
        
        mask = (telemetry["position"] >= start_pos) & (telemetry["position"] <= end_pos)
        return telemetry[mask].copy()


# Track corner databases (can be expanded)
TRACK_CORNERS = {
    "monza": [
        {"name": "T1 - Variante del Rettifilo", "position": 0.08},
        {"name": "T2 - Curva Grande", "position": 0.15},
        {"name": "T3 - Variante della Roggia", "position": 0.28},
        {"name": "T4 - Curve di Lesmo 1", "position": 0.40},
        {"name": "T5 - Curve di Lesmo 2", "position": 0.45},
        {"name": "T6 - Curva del Serraglio", "position": 0.55},
        {"name": "T7 - Variante Ascari", "position": 0.62},
        {"name": "T8 - Curva Parabolica", "position": 0.85},
    ],
    "spa": [
        {"name": "T1 - La Source", "position": 0.02},
        {"name": "T3 - Eau Rouge", "position": 0.08},
        {"name": "T5 - Raidillon", "position": 0.10},
        {"name": "T7 - Les Combes", "position": 0.20},
        {"name": "T9 - Bruxelles", "position": 0.30},
        {"name": "T10 - Pouhon", "position": 0.40},
        {"name": "T12 - Fagnes", "position": 0.50},
        {"name": "T13 - Stavelot", "position": 0.58},
        {"name": "T15 - Blanchimont", "position": 0.75},
        {"name": "T17 - Bus Stop", "position": 0.90},
    ],
    "nurburgring": [
        {"name": "T1 - Yokohama S", "position": 0.05},
        {"name": "T3 - Mercedes Arena", "position": 0.15},
        {"name": "T5 - Ford Kurve", "position": 0.35},
        {"name": "T6 - Dunlop Kehre", "position": 0.45},
        {"name": "T8 - RTL Kurve", "position": 0.55},
        {"name": "T10 - Bit Kurve", "position": 0.70},
        {"name": "T13 - Coca Cola Kurve", "position": 0.85},
    ],
}


def get_track_corners(track_name: str) -> List[dict]:
    """Get predefined corners for a track"""
    # Normalize track name
    track_lower = track_name.lower()
    
    for key in TRACK_CORNERS:
        if key in track_lower:
            return TRACK_CORNERS[key]
    
    return []
