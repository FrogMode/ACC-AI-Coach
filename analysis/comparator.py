"""
Lap Comparison Engine

Compares two laps to identify where time is gained or lost.
Aligns laps by track position (not time) for accurate comparison.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import numpy as np
import pandas as pd

from .segmenter import Corner, CornerSegmenter


@dataclass
class CornerDelta:
    """Time delta analysis for a single corner"""
    corner: Corner
    
    # Time deltas (positive = slower than reference)
    entry_delta_ms: float = 0.0
    apex_delta_ms: float = 0.0
    exit_delta_ms: float = 0.0
    total_delta_ms: float = 0.0
    
    # Speed deltas (positive = faster than reference)
    entry_speed_delta: float = 0.0
    apex_speed_delta: float = 0.0
    exit_speed_delta: float = 0.0
    
    # Key differences
    brake_point_delta: float = 0.0  # Positive = later braking
    throttle_point_delta: float = 0.0  # Positive = earlier throttle
    
    # Diagnosis
    issues: List[str] = field(default_factory=list)


@dataclass
class LapDelta:
    """Complete lap comparison results"""
    total_delta_ms: float = 0.0
    
    # Per-corner analysis
    corner_deltas: List[CornerDelta] = field(default_factory=list)
    
    # Sector deltas
    sector_deltas: List[float] = field(default_factory=list)
    
    # Position-aligned delta trace
    delta_trace: Optional[pd.DataFrame] = None
    
    # Summary
    time_gained_corners: List[str] = field(default_factory=list)
    time_lost_corners: List[str] = field(default_factory=list)
    biggest_time_loss: Optional[str] = None
    biggest_time_gain: Optional[str] = None


class LapComparator:
    """
    Compares two laps to identify performance differences.
    
    Usage:
        comparator = LapComparator()
        delta = comparator.compare(my_lap, reference_lap)
        
        print(f"Total delta: {delta.total_delta_ms:+.0f}ms")
        for corner in delta.corner_deltas:
            print(f"{corner.corner.name}: {corner.total_delta_ms:+.0f}ms")
    """
    
    def __init__(self, position_resolution: float = 0.001):
        """
        Args:
            position_resolution: Resolution for position-based alignment
        """
        self.position_resolution = position_resolution
        self.segmenter = CornerSegmenter()
    
    def compare(self, lap1: pd.DataFrame, lap2: pd.DataFrame,
                corners: Optional[List[Corner]] = None) -> LapDelta:
        """
        Compare two laps.
        
        Args:
            lap1: "My" lap telemetry
            lap2: Reference lap telemetry
            corners: Pre-detected corners (optional, will auto-detect if None)
            
        Returns:
            LapDelta with detailed comparison
        """
        # Align laps by position
        aligned = self._align_by_position(lap1, lap2)
        
        # Calculate cumulative time delta
        delta_trace = self._calculate_delta_trace(aligned)
        
        # Detect corners if not provided
        if corners is None:
            corners = self.segmenter.detect_corners(lap2)  # Use reference for corners
        
        # Analyze each corner
        corner_deltas = []
        for corner in corners:
            corner_delta = self._analyze_corner(aligned, corner)
            corner_deltas.append(corner_delta)
        
        # Calculate total delta
        total_delta = delta_trace["time_delta_ms"].iloc[-1] if not delta_trace.empty else 0
        
        # Find biggest gains/losses
        time_gained = [(cd.corner.name, cd.total_delta_ms) for cd in corner_deltas if cd.total_delta_ms < -10]
        time_lost = [(cd.corner.name, cd.total_delta_ms) for cd in corner_deltas if cd.total_delta_ms > 10]
        
        time_gained.sort(key=lambda x: x[1])
        time_lost.sort(key=lambda x: x[1], reverse=True)
        
        return LapDelta(
            total_delta_ms=total_delta,
            corner_deltas=corner_deltas,
            delta_trace=delta_trace,
            time_gained_corners=[c[0] for c in time_gained],
            time_lost_corners=[c[0] for c in time_lost],
            biggest_time_loss=time_lost[0][0] if time_lost else None,
            biggest_time_gain=time_gained[0][0] if time_gained else None,
        )
    
    def _align_by_position(self, lap1: pd.DataFrame, lap2: pd.DataFrame) -> pd.DataFrame:
        """
        Align two laps by track position using interpolation.
        
        Creates a unified dataframe with both laps' data at consistent positions.
        """
        # Create position grid
        positions = np.arange(0, 1, self.position_resolution)
        
        # Sort both laps by position
        lap1_sorted = lap1.sort_values("position")
        lap2_sorted = lap2.sort_values("position")
        
        # Interpolate lap1 data
        lap1_interp = {}
        for col in ["speed_kmh", "throttle", "brake", "steering", "gear"]:
            if col in lap1_sorted.columns:
                lap1_interp[f"{col}_1"] = np.interp(
                    positions, 
                    lap1_sorted["position"].values,
                    lap1_sorted[col].values
                )
        
        # Calculate time from speed (distance / speed)
        # Assuming constant position intervals
        track_length_m = 5793  # Monza default, should be parameterized
        segment_length = track_length_m * self.position_resolution
        
        speeds_1 = lap1_interp.get("speed_kmh_1", np.ones(len(positions)) * 100)
        speeds_1 = np.maximum(speeds_1, 1)  # Avoid division by zero
        times_1 = segment_length / (speeds_1 / 3.6)  # Convert to m/s
        lap1_interp["cum_time_1"] = np.cumsum(times_1)
        
        # Interpolate lap2 data
        lap2_interp = {}
        for col in ["speed_kmh", "throttle", "brake", "steering", "gear"]:
            if col in lap2_sorted.columns:
                lap2_interp[f"{col}_2"] = np.interp(
                    positions,
                    lap2_sorted["position"].values,
                    lap2_sorted[col].values
                )
        
        speeds_2 = lap2_interp.get("speed_kmh_2", np.ones(len(positions)) * 100)
        speeds_2 = np.maximum(speeds_2, 1)
        times_2 = segment_length / (speeds_2 / 3.6)
        lap2_interp["cum_time_2"] = np.cumsum(times_2)
        
        # Combine into single dataframe
        aligned = pd.DataFrame({
            "position": positions,
            **lap1_interp,
            **lap2_interp,
        })
        
        # Calculate deltas
        aligned["speed_delta"] = aligned["speed_kmh_1"] - aligned["speed_kmh_2"]
        aligned["time_delta"] = aligned["cum_time_1"] - aligned["cum_time_2"]
        
        return aligned
    
    def _calculate_delta_trace(self, aligned: pd.DataFrame) -> pd.DataFrame:
        """Calculate cumulative time delta trace"""
        delta_trace = aligned[["position"]].copy()
        
        # Time delta in milliseconds
        if "cum_time_1" in aligned.columns and "cum_time_2" in aligned.columns:
            delta_trace["time_delta_ms"] = (aligned["cum_time_1"] - aligned["cum_time_2"]) * 1000
        else:
            delta_trace["time_delta_ms"] = 0
        
        # Speed delta
        if "speed_kmh_1" in aligned.columns and "speed_kmh_2" in aligned.columns:
            delta_trace["speed_delta"] = aligned["speed_kmh_1"] - aligned["speed_kmh_2"]
        else:
            delta_trace["speed_delta"] = 0
        
        return delta_trace
    
    def _analyze_corner(self, aligned: pd.DataFrame, corner: Corner) -> CornerDelta:
        """Analyze time delta for a specific corner"""
        # Get data for corner region
        mask = (aligned["position"] >= corner.entry_position) & \
               (aligned["position"] <= corner.exit_position)
        corner_data = aligned[mask]
        
        if corner_data.empty:
            return CornerDelta(corner=corner)
        
        # Find apex position
        apex_mask = (aligned["position"] >= corner.apex_position - 0.01) & \
                    (aligned["position"] <= corner.apex_position + 0.01)
        apex_data = aligned[apex_mask]
        
        # Calculate deltas at key points
        entry_row = corner_data.iloc[0] if not corner_data.empty else None
        exit_row = corner_data.iloc[-1] if not corner_data.empty else None
        apex_row = apex_data.iloc[len(apex_data)//2] if not apex_data.empty else None
        
        # Time deltas (comparing cumulative time at each point)
        entry_delta = entry_row["time_delta"] * 1000 if entry_row is not None and "time_delta" in corner_data.columns else 0
        exit_delta = exit_row["time_delta"] * 1000 if exit_row is not None and "time_delta" in corner_data.columns else 0
        apex_delta = apex_row["time_delta"] * 1000 if apex_row is not None and "time_delta" in apex_data.columns else 0
        
        total_delta = exit_delta - entry_delta
        
        # Speed deltas
        entry_speed_delta = entry_row["speed_delta"] if entry_row is not None and "speed_delta" in corner_data.columns else 0
        exit_speed_delta = exit_row["speed_delta"] if exit_row is not None and "speed_delta" in corner_data.columns else 0
        apex_speed_delta = apex_row["speed_delta"] if apex_row is not None and "speed_delta" in apex_data.columns else 0
        
        # Diagnose issues
        issues = []
        
        if total_delta > 50:  # Lost more than 50ms
            if entry_speed_delta < -5:
                issues.append("Entering too slow")
            if apex_speed_delta < -5:
                issues.append("Apex speed too low")
            if exit_speed_delta < -5:
                issues.append("Exit speed too low")
            
            # Check brake point (would need brake column analysis)
            # Check throttle application point
        
        return CornerDelta(
            corner=corner,
            entry_delta_ms=entry_delta,
            apex_delta_ms=apex_delta,
            exit_delta_ms=exit_delta,
            total_delta_ms=total_delta,
            entry_speed_delta=entry_speed_delta,
            apex_speed_delta=apex_speed_delta,
            exit_speed_delta=exit_speed_delta,
            issues=issues,
        )
    
    def generate_comparison_summary(self, delta: LapDelta) -> str:
        """Generate a text summary of the lap comparison"""
        lines = []
        lines.append(f"Total delta: {delta.total_delta_ms:+.0f}ms")
        lines.append("")
        
        if delta.biggest_time_loss:
            loss_corner = next((cd for cd in delta.corner_deltas if cd.corner.name == delta.biggest_time_loss), None)
            if loss_corner:
                lines.append(f"Biggest time loss: {delta.biggest_time_loss} ({loss_corner.total_delta_ms:+.0f}ms)")
                for issue in loss_corner.issues:
                    lines.append(f"  - {issue}")
        
        if delta.biggest_time_gain:
            gain_corner = next((cd for cd in delta.corner_deltas if cd.corner.name == delta.biggest_time_gain), None)
            if gain_corner:
                lines.append(f"Biggest time gain: {delta.biggest_time_gain} ({gain_corner.total_delta_ms:+.0f}ms)")
        
        lines.append("")
        lines.append("Corner-by-corner:")
        for cd in delta.corner_deltas:
            status = "✓" if cd.total_delta_ms <= 0 else "✗"
            lines.append(f"  {status} {cd.corner.name}: {cd.total_delta_ms:+.0f}ms")
        
        return "\n".join(lines)
