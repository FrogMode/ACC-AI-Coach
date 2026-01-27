"""
ACC AI Coach - Streamlit Dashboard

Interactive telemetry visualization and analysis.

Run with: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from telemetry.recorder import SessionLoader
from telemetry.models import format_laptime
from analysis.segmenter import CornerSegmenter, get_track_corners
from analysis.comparator import LapComparator
from analysis.metrics import MetricsCalculator, format_laptime_ms


# Page config
st.set_page_config(
    page_title="ACC AI Coach",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .big-number {
        font-size: 2.5em;
        font-weight: bold;
        color: #00ff88;
    }
    .delta-positive { color: #ff4444; }
    .delta-negative { color: #44ff44; }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🏎️ ACC AI Coach")
    st.markdown("---")
    
    # Sidebar - Session selection
    with st.sidebar:
        st.header("Session")
        
        # Find available sessions
        data_dir = Path("data/sessions")
        if data_dir.exists():
            sessions = sorted([d.name for d in data_dir.iterdir() if d.is_dir()], reverse=True)
        else:
            sessions = []
        
        if sessions:
            selected_session = st.selectbox("Select Session", sessions)
            session_path = data_dir / selected_session
        else:
            st.warning("No sessions found. Record a session first!")
            
            # Demo mode
            if st.button("Load Demo Data"):
                st.session_state["demo_mode"] = True
            
            if st.session_state.get("demo_mode"):
                show_demo_dashboard()
            return
        
        # Load session
        loader = SessionLoader(str(session_path))
        if not loader.load():
            st.error("Failed to load session")
            return
        
        session_info = loader.get_session_info()
        laps = loader.get_laps()
        telemetry = loader.get_telemetry()
        
        # Session info
        st.subheader("Session Info")
        st.write(f"**Track:** {session_info['track']}")
        st.write(f"**Car:** {session_info['car']}")
        st.write(f"**Laps:** {session_info['total_laps']}")
        
        if session_info['best_lap_ms'] > 0:
            st.write(f"**Best Lap:** {format_laptime_ms(session_info['best_lap_ms'])}")
        
        # Lap selection
        st.subheader("Lap Selection")
        lap_numbers = [lap['lap_number'] for lap in laps if lap['lap_time_ms'] > 0]
        
        if lap_numbers:
            selected_lap = st.selectbox("Analyze Lap", lap_numbers)
            
            # Reference lap selection
            reference_options = ["Best Lap"] + [f"Lap {n}" for n in lap_numbers if n != selected_lap]
            reference_choice = st.selectbox("Compare To", reference_options)
            
            if reference_choice == "Best Lap":
                best_lap = min(laps, key=lambda x: x['lap_time_ms'] if x['lap_time_ms'] > 0 else float('inf'))
                reference_lap = best_lap['lap_number']
            else:
                reference_lap = int(reference_choice.split()[-1])
        else:
            st.warning("No valid laps recorded")
            return
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Telemetry", "🔄 Comparison", "🎯 Analysis"])
    
    with tab1:
        show_overview(session_info, laps, telemetry)
    
    with tab2:
        lap_telemetry = loader.get_lap_telemetry(selected_lap)
        if lap_telemetry is not None and not lap_telemetry.empty:
            show_telemetry(lap_telemetry, selected_lap)
        else:
            st.warning("No telemetry data for selected lap")
    
    with tab3:
        lap_telemetry = loader.get_lap_telemetry(selected_lap)
        ref_telemetry = loader.get_lap_telemetry(reference_lap)
        if lap_telemetry is not None and ref_telemetry is not None:
            show_comparison(lap_telemetry, ref_telemetry, selected_lap, reference_lap)
        else:
            st.warning("Missing telemetry data for comparison")
    
    with tab4:
        lap_telemetry = loader.get_lap_telemetry(selected_lap)
        if lap_telemetry is not None:
            show_analysis(lap_telemetry, session_info['track'])
    
    loader.close()


def show_overview(session_info: dict, laps: list, telemetry: pd.DataFrame):
    """Show session overview"""
    st.header("Session Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    valid_laps = [lap for lap in laps if lap['lap_time_ms'] > 0]
    
    with col1:
        st.metric("Total Laps", len(valid_laps))
    
    with col2:
        if valid_laps:
            best_time = min(lap['lap_time_ms'] for lap in valid_laps)
            st.metric("Best Lap", format_laptime_ms(best_time))
    
    with col3:
        if valid_laps:
            avg_time = sum(lap['lap_time_ms'] for lap in valid_laps) / len(valid_laps)
            st.metric("Average Lap", format_laptime_ms(int(avg_time)))
    
    with col4:
        valid_count = len([lap for lap in valid_laps if lap.get('is_valid', 1)])
        st.metric("Valid Laps", valid_count)
    
    st.markdown("---")
    
    # Lap times chart
    if valid_laps:
        st.subheader("Lap Times")
        
        lap_data = pd.DataFrame(valid_laps)
        lap_data['lap_time_sec'] = lap_data['lap_time_ms'] / 1000
        lap_data['validity'] = lap_data['is_valid'].map({1: 'Valid', 0: 'Invalid'})
        
        fig = px.bar(
            lap_data,
            x='lap_number',
            y='lap_time_sec',
            color='validity',
            color_discrete_map={'Valid': '#00ff88', 'Invalid': '#ff4444'},
            labels={'lap_number': 'Lap', 'lap_time_sec': 'Time (s)'},
        )
        
        # Add best lap line
        best_time_sec = min(lap_data['lap_time_sec'])
        fig.add_hline(y=best_time_sec, line_dash="dash", line_color="yellow",
                      annotation_text=f"Best: {format_laptime_ms(int(best_time_sec*1000))}")
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Speed histogram
    if telemetry is not None and 'speed_kmh' in telemetry.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Speed Distribution")
            fig = px.histogram(
                telemetry, 
                x='speed_kmh',
                nbins=50,
                labels={'speed_kmh': 'Speed (km/h)'},
            )
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Throttle vs Brake")
            fig = px.scatter(
                telemetry.sample(min(1000, len(telemetry))),  # Sample for performance
                x='throttle',
                y='brake',
                color='speed_kmh',
                color_continuous_scale='Viridis',
                labels={'throttle': 'Throttle', 'brake': 'Brake', 'speed_kmh': 'Speed'},
            )
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)


def show_telemetry(telemetry: pd.DataFrame, lap_number: int):
    """Show detailed telemetry for a single lap"""
    st.header(f"Lap {lap_number} Telemetry")
    
    # Sort by position
    df = telemetry.sort_values('position').copy()
    
    # Create main telemetry plot
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Speed', 'Throttle & Brake', 'Steering', 'G-Forces'),
        row_heights=[0.3, 0.25, 0.2, 0.25],
    )
    
    # Speed
    fig.add_trace(
        go.Scatter(x=df['position'], y=df['speed_kmh'], name='Speed', 
                   line=dict(color='#00ff88', width=2)),
        row=1, col=1
    )
    
    # Throttle & Brake
    fig.add_trace(
        go.Scatter(x=df['position'], y=df['throttle']*100, name='Throttle',
                   line=dict(color='#44ff44', width=2)),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['position'], y=df['brake']*100, name='Brake',
                   line=dict(color='#ff4444', width=2)),
        row=2, col=1
    )
    
    # Steering
    fig.add_trace(
        go.Scatter(x=df['position'], y=df['steering'], name='Steering',
                   line=dict(color='#ffaa00', width=2)),
        row=3, col=1
    )
    
    # G-Forces
    if 'g_lat' in df.columns and 'g_lon' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['position'], y=df['g_lat'], name='G Lateral',
                       line=dict(color='#ff00ff', width=2)),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['position'], y=df['g_lon'], name='G Longitudinal',
                       line=dict(color='#00ffff', width=2)),
            row=4, col=1
        )
    
    # Update layout
    fig.update_layout(
        template="plotly_dark",
        height=800,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    
    fig.update_xaxes(title_text="Track Position", row=4, col=1)
    fig.update_yaxes(title_text="km/h", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    fig.update_yaxes(title_text="deg", row=3, col=1)
    fig.update_yaxes(title_text="G", row=4, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tire temps
    st.subheader("Tire Temperatures")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tire temp line chart
        temp_cols = ['temp_fl', 'temp_fr', 'temp_rl', 'temp_rr']
        available_temps = [col for col in temp_cols if col in df.columns]
        
        if available_temps:
            fig_temps = go.Figure()
            colors = {'temp_fl': '#ff6666', 'temp_fr': '#66ff66', 
                      'temp_rl': '#6666ff', 'temp_rr': '#ffff66'}
            names = {'temp_fl': 'FL', 'temp_fr': 'FR', 'temp_rl': 'RL', 'temp_rr': 'RR'}
            
            for col in available_temps:
                fig_temps.add_trace(go.Scatter(
                    x=df['position'], y=df[col],
                    name=names[col], line=dict(color=colors[col])
                ))
            
            fig_temps.update_layout(
                template="plotly_dark",
                height=300,
                title="Tire Core Temperatures",
            )
            st.plotly_chart(fig_temps, use_container_width=True)
    
    with col2:
        # Current tire temps display
        if available_temps:
            latest = df.iloc[-1]
            
            st.markdown("""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; text-align: center;">
                <div style="background: #333; padding: 20px; border-radius: 10px;">
                    <div style="font-size: 12px; color: #888;">FL</div>
                    <div style="font-size: 24px; font-weight: bold;">{:.1f}°C</div>
                </div>
                <div style="background: #333; padding: 20px; border-radius: 10px;">
                    <div style="font-size: 12px; color: #888;">FR</div>
                    <div style="font-size: 24px; font-weight: bold;">{:.1f}°C</div>
                </div>
                <div style="background: #333; padding: 20px; border-radius: 10px;">
                    <div style="font-size: 12px; color: #888;">RL</div>
                    <div style="font-size: 24px; font-weight: bold;">{:.1f}°C</div>
                </div>
                <div style="background: #333; padding: 20px; border-radius: 10px;">
                    <div style="font-size: 12px; color: #888;">RR</div>
                    <div style="font-size: 24px; font-weight: bold;">{:.1f}°C</div>
                </div>
            </div>
            """.format(
                latest.get('temp_fl', 0),
                latest.get('temp_fr', 0),
                latest.get('temp_rl', 0),
                latest.get('temp_rr', 0),
            ), unsafe_allow_html=True)


def show_comparison(lap1: pd.DataFrame, lap2: pd.DataFrame, 
                    lap1_num: int, lap2_num: int):
    """Show lap comparison"""
    st.header(f"Lap {lap1_num} vs Lap {lap2_num}")
    
    # Initialize comparator
    comparator = LapComparator()
    delta = comparator.compare(lap1, lap2)
    
    # Delta summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_color = "red" if delta.total_delta_ms > 0 else "green"
        st.metric(
            "Total Delta",
            f"{delta.total_delta_ms/1000:+.3f}s",
            delta_color=("inverse" if delta.total_delta_ms > 0 else "normal"),
        )
    
    with col2:
        if delta.biggest_time_loss:
            st.metric("Biggest Loss", delta.biggest_time_loss)
    
    with col3:
        if delta.biggest_time_gain:
            st.metric("Biggest Gain", delta.biggest_time_gain)
    
    st.markdown("---")
    
    # Delta trace
    if delta.delta_trace is not None and not delta.delta_trace.empty:
        st.subheader("Time Delta Around Lap")
        
        fig = go.Figure()
        
        # Delta line
        fig.add_trace(go.Scatter(
            x=delta.delta_trace['position'],
            y=delta.delta_trace['time_delta_ms'] / 1000,
            name='Time Delta',
            fill='tozeroy',
            line=dict(color='#ffaa00', width=2),
            fillcolor='rgba(255, 170, 0, 0.3)',
        ))
        
        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="white")
        
        fig.update_layout(
            template="plotly_dark",
            height=300,
            xaxis_title="Track Position",
            yaxis_title="Delta (s)",
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Speed comparison
    st.subheader("Speed Comparison")
    
    lap1_sorted = lap1.sort_values('position')
    lap2_sorted = lap2.sort_values('position')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=lap1_sorted['position'],
        y=lap1_sorted['speed_kmh'],
        name=f'Lap {lap1_num}',
        line=dict(color='#00ff88', width=2),
    ))
    
    fig.add_trace(go.Scatter(
        x=lap2_sorted['position'],
        y=lap2_sorted['speed_kmh'],
        name=f'Lap {lap2_num} (ref)',
        line=dict(color='#ff8800', width=2),
    ))
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        xaxis_title="Track Position",
        yaxis_title="Speed (km/h)",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Corner analysis
    if delta.corner_deltas:
        st.subheader("Corner-by-Corner Analysis")
        
        corner_data = []
        for cd in delta.corner_deltas:
            corner_data.append({
                'Corner': cd.corner.name,
                'Delta (ms)': f"{cd.total_delta_ms:+.0f}",
                'Entry Speed Δ': f"{cd.entry_speed_delta:+.1f}",
                'Apex Speed Δ': f"{cd.apex_speed_delta:+.1f}",
                'Exit Speed Δ': f"{cd.exit_speed_delta:+.1f}",
                'Issues': ', '.join(cd.issues) if cd.issues else '-',
            })
        
        st.dataframe(
            pd.DataFrame(corner_data),
            use_container_width=True,
            hide_index=True,
        )


def show_analysis(telemetry: pd.DataFrame, track_name: str):
    """Show detailed analysis"""
    st.header("Performance Analysis")
    
    # Calculate metrics
    calculator = MetricsCalculator()
    metrics = calculator.calculate_lap_metrics(telemetry)
    
    # Scores
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Smoothness Score", f"{metrics.smoothness_score:.0f}/100")
    
    with col2:
        st.metric("Speed Score", f"{metrics.speed_score:.0f}/100")
    
    with col3:
        if metrics.inputs.trail_braking_score > 0:
            st.metric("Trail Braking Score", f"{metrics.inputs.trail_braking_score:.0f}/100")
    
    st.markdown("---")
    
    # Corner detection
    st.subheader("Corner Analysis")
    
    segmenter = CornerSegmenter()
    corners = segmenter.detect_corners(telemetry)
    
    if corners:
        # Corner stats
        corner_data = []
        for corner in corners:
            corner_data.append({
                'Corner': corner.name,
                'Type': corner.corner_type.title(),
                'Entry (km/h)': f"{corner.entry_speed_kmh:.0f}",
                'Apex (km/h)': f"{corner.min_speed_kmh:.0f}",
                'Exit (km/h)': f"{corner.exit_speed_kmh:.0f}",
                'Max Steer (°)': f"{corner.max_steering_angle:.1f}",
            })
        
        st.dataframe(
            pd.DataFrame(corner_data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No corners detected. This may be due to limited telemetry data.")
    
    # G-G diagram
    st.subheader("G-G Diagram (Friction Circle)")
    
    if 'g_lat' in telemetry.columns and 'g_lon' in telemetry.columns:
        fig = go.Figure()
        
        # Scatter of actual G forces
        fig.add_trace(go.Scatter(
            x=telemetry['g_lat'],
            y=telemetry['g_lon'],
            mode='markers',
            marker=dict(
                size=3,
                color=telemetry['speed_kmh'],
                colorscale='Viridis',
                colorbar=dict(title='Speed'),
            ),
            name='G-Forces',
        ))
        
        # Add friction circle reference
        theta = np.linspace(0, 2*np.pi, 100)
        for r in [1, 1.5, 2]:
            fig.add_trace(go.Scatter(
                x=r * np.cos(theta),
                y=r * np.sin(theta),
                mode='lines',
                line=dict(color='rgba(255,255,255,0.2)', dash='dash'),
                showlegend=False,
            ))
        
        fig.update_layout(
            template="plotly_dark",
            height=500,
            xaxis_title="Lateral G",
            yaxis_title="Longitudinal G",
            xaxis=dict(scaleanchor="y", scaleratio=1),
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Input analysis
    st.subheader("Input Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Smoothness Metrics**")
        st.write(f"- Throttle smoothness: {metrics.inputs.throttle_smoothness:.2f}")
        st.write(f"- Brake smoothness: {metrics.inputs.brake_smoothness:.2f}")
        st.write(f"- Steering smoothness: {metrics.inputs.steering_smoothness:.2f}")
    
    with col2:
        st.write("**Throttle Application**")
        st.write(f"- Avg throttle on straights: {metrics.inputs.avg_throttle_on_straights*100:.1f}%")
        st.write(f"- Throttle lifts: {metrics.inputs.throttle_lift_count}")


def show_demo_dashboard():
    """Show dashboard with demo/mock data"""
    st.header("Demo Mode")
    st.info("This is a demonstration with synthetic data. Record a real session to see your telemetry!")
    
    # Generate demo data
    np.random.seed(42)
    positions = np.linspace(0, 1, 1000)
    
    # Simulate speed (with corners)
    base_speed = 200 + 50 * np.sin(positions * 2 * np.pi * 5)  # 5 "corners"
    speed = np.clip(base_speed + np.random.normal(0, 5, len(positions)), 60, 300)
    
    # Simulate inputs
    throttle = np.clip(0.5 + 0.5 * np.cos(positions * 2 * np.pi * 5 + 0.5), 0, 1)
    brake = np.clip(-0.5 * np.cos(positions * 2 * np.pi * 5 + 0.5) - 0.3, 0, 1)
    steering = 30 * np.sin(positions * 2 * np.pi * 5)
    
    demo_telemetry = pd.DataFrame({
        'position': positions,
        'speed_kmh': speed,
        'throttle': throttle,
        'brake': brake,
        'steering': steering,
        'g_lat': np.random.normal(0, 0.5, len(positions)),
        'g_lon': np.random.normal(0, 0.8, len(positions)),
        'temp_fl': 85 + np.random.normal(0, 3, len(positions)),
        'temp_fr': 84 + np.random.normal(0, 3, len(positions)),
        'temp_rl': 82 + np.random.normal(0, 3, len(positions)),
        'temp_rr': 81 + np.random.normal(0, 3, len(positions)),
    })
    
    # Show telemetry
    show_telemetry(demo_telemetry, lap_number=1)


if __name__ == "__main__":
    main()
