"""
Performance Metrics

Calculates various performance metrics from telemetry data.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np
import pandas as pd


@dataclass
class ConsistencyMetrics:
    """Lap-to-lap consistency metrics"""
    lap_count: int = 0
    best_lap_ms: int = 0
    average_lap_ms: float = 0.0
    std_dev_ms: float = 0.0
    consistency_score: float = 0.0  # 0-100, higher is more consistent


@dataclass
class InputMetrics:
    """Driver input analysis"""
    # Smoothness (lower = smoother)
    throttle_smoothness: float = 0.0
    brake_smoothness: float = 0.0
    steering_smoothness: float = 0.0
    
    # Trail braking score (0-100)
    trail_braking_score: float = 0.0
    
    # Throttle application
    avg_throttle_on_straights: float = 0.0
    throttle_lift_count: int = 0  # Times lifting off throttle on straights


@dataclass
class TireMetrics:
    """Tire usage analysis"""
    # Average temps
    avg_temp_fl: float = 0.0
    avg_temp_fr: float = 0.0
    avg_temp_rl: float = 0.0
    avg_temp_rr: float = 0.0
    
    # Temp balance
    front_rear_balance: float = 0.0  # Positive = front hotter
    left_right_balance: float = 0.0  # Positive = left hotter
    
    # Slip analysis
    avg_slip: float = 0.0
    max_slip: float = 0.0
    slip_events: int = 0  # Times slip exceeded threshold


@dataclass
class PerformanceMetrics:
    """Complete performance analysis for a lap or session"""
    consistency: ConsistencyMetrics = field(default_factory=ConsistencyMetrics)
    inputs: InputMetrics = field(default_factory=InputMetrics)
    tires: TireMetrics = field(default_factory=TireMetrics)
    
    # Overall scores (0-100)
    overall_score: float = 0.0
    speed_score: float = 0.0
    smoothness_score: float = 0.0
    consistency_score: float = 0.0


class MetricsCalculator:
    """Calculates performance metrics from telemetry"""
    
    def __init__(self):
        self.slip_threshold = 0.15  # Threshold for counting slip events
        self.straight_speed_threshold = 200  # km/h to consider "on a straight"
    
    def calculate_lap_metrics(self, telemetry: pd.DataFrame) -> PerformanceMetrics:
        """Calculate metrics for a single lap"""
        metrics = PerformanceMetrics()
        
        # Input smoothness
        metrics.inputs = self._calculate_input_metrics(telemetry)
        
        # Tire metrics
        metrics.tires = self._calculate_tire_metrics(telemetry)
        
        # Overall scores
        metrics.smoothness_score = self._calculate_smoothness_score(metrics.inputs)
        metrics.speed_score = self._calculate_speed_score(telemetry)
        
        return metrics
    
    def calculate_session_metrics(self, laps: List[pd.DataFrame], 
                                   lap_times_ms: List[int]) -> PerformanceMetrics:
        """Calculate metrics for an entire session"""
        metrics = PerformanceMetrics()
        
        # Consistency
        metrics.consistency = self._calculate_consistency(lap_times_ms)
        
        # Average metrics across all laps
        if laps:
            all_inputs = [self._calculate_input_metrics(lap) for lap in laps]
            all_tires = [self._calculate_tire_metrics(lap) for lap in laps]
            
            # Average input metrics
            metrics.inputs = InputMetrics(
                throttle_smoothness=np.mean([i.throttle_smoothness for i in all_inputs]),
                brake_smoothness=np.mean([i.brake_smoothness for i in all_inputs]),
                steering_smoothness=np.mean([i.steering_smoothness for i in all_inputs]),
                trail_braking_score=np.mean([i.trail_braking_score for i in all_inputs]),
            )
            
            # Average tire metrics
            metrics.tires = TireMetrics(
                avg_temp_fl=np.mean([t.avg_temp_fl for t in all_tires]),
                avg_temp_fr=np.mean([t.avg_temp_fr for t in all_tires]),
                avg_temp_rl=np.mean([t.avg_temp_rl for t in all_tires]),
                avg_temp_rr=np.mean([t.avg_temp_rr for t in all_tires]),
            )
        
        # Overall scores
        metrics.consistency_score = metrics.consistency.consistency_score
        metrics.smoothness_score = self._calculate_smoothness_score(metrics.inputs)
        metrics.overall_score = (
            metrics.consistency_score * 0.4 +
            metrics.smoothness_score * 0.3 +
            100 * 0.3  # Placeholder for other factors
        )
        
        return metrics
    
    def _calculate_input_metrics(self, telemetry: pd.DataFrame) -> InputMetrics:
        """Calculate driver input metrics"""
        metrics = InputMetrics()
        
        # Smoothness = standard deviation of derivative (rate of change)
        if "throttle" in telemetry.columns:
            throttle_diff = telemetry["throttle"].diff().abs()
            metrics.throttle_smoothness = throttle_diff.std() * 100
        
        if "brake" in telemetry.columns:
            brake_diff = telemetry["brake"].diff().abs()
            metrics.brake_smoothness = brake_diff.std() * 100
        
        if "steering" in telemetry.columns:
            steering_diff = telemetry["steering"].diff().abs()
            metrics.steering_smoothness = steering_diff.std()
        
        # Trail braking analysis
        if "brake" in telemetry.columns and "steering" in telemetry.columns:
            # Trail braking = braking while turning
            trail_braking_mask = (telemetry["brake"] > 0.1) & (telemetry["steering"].abs() > 10)
            trail_braking_ratio = trail_braking_mask.sum() / max(1, (telemetry["brake"] > 0.1).sum())
            metrics.trail_braking_score = trail_braking_ratio * 100
        
        # Throttle on straights
        if "throttle" in telemetry.columns and "speed_kmh" in telemetry.columns:
            straight_mask = telemetry["speed_kmh"] > self.straight_speed_threshold
            if straight_mask.any():
                metrics.avg_throttle_on_straights = telemetry.loc[straight_mask, "throttle"].mean()
                
                # Count throttle lifts on straights
                straight_throttle = telemetry.loc[straight_mask, "throttle"]
                lifts = (straight_throttle < 0.9) & (straight_throttle.shift() >= 0.9)
                metrics.throttle_lift_count = lifts.sum()
        
        return metrics
    
    def _calculate_tire_metrics(self, telemetry: pd.DataFrame) -> TireMetrics:
        """Calculate tire usage metrics"""
        metrics = TireMetrics()
        
        # Average temps
        temp_cols = ["temp_fl", "temp_fr", "temp_rl", "temp_rr"]
        for col in temp_cols:
            if col in telemetry.columns:
                setattr(metrics, f"avg_{col}", telemetry[col].mean())
        
        # Balance
        front_avg = (metrics.avg_temp_fl + metrics.avg_temp_fr) / 2
        rear_avg = (metrics.avg_temp_rl + metrics.avg_temp_rr) / 2
        metrics.front_rear_balance = front_avg - rear_avg
        
        left_avg = (metrics.avg_temp_fl + metrics.avg_temp_rl) / 2
        right_avg = (metrics.avg_temp_fr + metrics.avg_temp_rr) / 2
        metrics.left_right_balance = left_avg - right_avg
        
        # Slip analysis
        slip_cols = ["slip_fl", "slip_fr", "slip_rl", "slip_rr"]
        slip_data = []
        for col in slip_cols:
            if col in telemetry.columns:
                slip_data.append(telemetry[col])
        
        if slip_data:
            all_slip = pd.concat(slip_data)
            metrics.avg_slip = all_slip.mean()
            metrics.max_slip = all_slip.max()
            metrics.slip_events = (all_slip > self.slip_threshold).sum()
        
        return metrics
    
    def _calculate_consistency(self, lap_times_ms: List[int]) -> ConsistencyMetrics:
        """Calculate lap time consistency"""
        if not lap_times_ms:
            return ConsistencyMetrics()
        
        valid_times = [t for t in lap_times_ms if t > 0]
        if not valid_times:
            return ConsistencyMetrics()
        
        best = min(valid_times)
        avg = np.mean(valid_times)
        std = np.std(valid_times)
        
        # Consistency score: how close laps are to each other and to the best
        # Lower std and closer to best = higher score
        if avg > 0:
            # Coefficient of variation (CV) - lower is better
            cv = std / avg
            # Convert to 0-100 score (CV of 0 = 100, CV of 0.05 = 0)
            consistency_score = max(0, 100 * (1 - cv * 20))
        else:
            consistency_score = 0
        
        return ConsistencyMetrics(
            lap_count=len(valid_times),
            best_lap_ms=best,
            average_lap_ms=avg,
            std_dev_ms=std,
            consistency_score=consistency_score,
        )
    
    def _calculate_smoothness_score(self, inputs: InputMetrics) -> float:
        """Calculate overall smoothness score"""
        # Combine individual smoothness metrics
        # Lower raw smoothness = smoother = higher score
        
        throttle_score = max(0, 100 - inputs.throttle_smoothness * 10)
        brake_score = max(0, 100 - inputs.brake_smoothness * 10)
        steering_score = max(0, 100 - inputs.steering_smoothness * 2)
        
        return (throttle_score + brake_score + steering_score) / 3
    
    def _calculate_speed_score(self, telemetry: pd.DataFrame) -> float:
        """Calculate speed utilization score"""
        if "speed_kmh" not in telemetry.columns:
            return 0
        
        # Compare average speed to theoretical max
        # This is a simplified metric - real version would compare to reference
        avg_speed = telemetry["speed_kmh"].mean()
        max_speed = telemetry["speed_kmh"].max()
        
        if max_speed > 0:
            # Higher average relative to max = better
            return (avg_speed / max_speed) * 100
        return 0


def format_laptime_ms(ms: int) -> str:
    """Format milliseconds as MM:SS.mmm"""
    if ms <= 0:
        return "--:--.---"
    
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    
    return f"{minutes}:{seconds:02d}.{millis:03d}"
