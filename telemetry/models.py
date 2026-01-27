"""
ACC Shared Memory Data Structures

These models map to the ACC shared memory structures:
- acpmf_physics: Real-time physics data (60Hz)
- acpmf_graphics: Graphics/timing data
- acpmf_static: Static session info (read once)

Reference: ACC Shared Memory Documentation v1.8+
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional
import struct


class ACCStatus(IntEnum):
    """Game status enum"""
    AC_OFF = 0
    AC_REPLAY = 1
    AC_LIVE = 2
    AC_PAUSE = 3


class ACCSessionType(IntEnum):
    """Session type enum"""
    AC_UNKNOWN = -1
    AC_PRACTICE = 0
    AC_QUALIFY = 1
    AC_RACE = 2
    AC_HOTLAP = 3
    AC_TIME_ATTACK = 4
    AC_DRIFT = 5
    AC_DRAG = 6
    AC_HOTSTINT = 7
    AC_HOTLAPSUPERPOLE = 8


class ACCFlagType(IntEnum):
    """Flag type enum"""
    AC_NO_FLAG = 0
    AC_BLUE_FLAG = 1
    AC_YELLOW_FLAG = 2
    AC_BLACK_FLAG = 3
    AC_WHITE_FLAG = 4
    AC_CHECKERED_FLAG = 5
    AC_PENALTY_FLAG = 6
    AC_GREEN_FLAG = 7
    AC_ORANGE_FLAG = 8


class ACCPenaltyType(IntEnum):
    """Penalty type enum"""
    NONE = 0
    DRIVE_THROUGH_CUTTING = 1
    STOP_AND_GO_10_CUTTING = 2
    STOP_AND_GO_20_CUTTING = 3
    STOP_AND_GO_30_CUTTING = 4
    DISQUALIFIED_CUTTING = 5
    REMOVE_BEST_LAPTIME_CUTTING = 6
    DRIVE_THROUGH_PIT_SPEEDING = 7
    STOP_AND_GO_10_PIT_SPEEDING = 8
    STOP_AND_GO_20_PIT_SPEEDING = 9
    STOP_AND_GO_30_PIT_SPEEDING = 10
    DISQUALIFIED_PIT_SPEEDING = 11
    REMOVE_BEST_LAPTIME_PIT_SPEEDING = 12
    DISQUALIFIED_IGNORED_MANDATORY_PIT = 13
    POST_RACE_PENALTY = 14
    DISQUALIFIED_TROLLING = 15
    DISQUALIFIED_PIT_ENTRY = 16
    DISQUALIFIED_PIT_EXIT = 17
    DISQUALIFIED_WRONG_WAY = 18
    DRIVE_THROUGH_IGNORED_DRIVER_STINT = 19
    DISQUALIFIED_IGNORED_DRIVER_STINT = 20
    DISQUALIFIED_EXCEEDED_DRIVER_STINT_LIMIT = 21


@dataclass
class ACCPhysics:
    """
    Physics telemetry data - updated at ~60Hz
    
    This is the core data for driving analysis:
    - Driver inputs (gas, brake, steering)
    - Vehicle state (speed, rpm, gear)
    - Tire data (temps, pressure, wear, slip)
    - Suspension and aero
    """
    # Packet identification
    packet_id: int = 0
    
    # Driver inputs (0.0 - 1.0)
    gas: float = 0.0
    brake: float = 0.0
    fuel: float = 0.0
    gear: int = 0  # 0=R, 1=N, 2=1st, etc.
    rpm: int = 0
    steer_angle: float = 0.0  # Degrees
    
    # Vehicle dynamics
    speed_kmh: float = 0.0
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])  # World velocity [x, y, z]
    acc_g: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])  # G-forces [x, y, z]
    
    # Wheel data [FL, FR, RL, RR]
    wheel_slip: List[float] = field(default_factory=lambda: [0.0] * 4)
    wheel_pressure: List[float] = field(default_factory=lambda: [0.0] * 4)  # PSI
    wheel_angular_speed: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Tire temperatures [FL, FR, RL, RR] - inner, middle, outer for each
    tyre_temp_inner: List[float] = field(default_factory=lambda: [0.0] * 4)
    tyre_temp_middle: List[float] = field(default_factory=lambda: [0.0] * 4)
    tyre_temp_outer: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Tire wear (0.0 = new, increases with wear)
    tyre_wear: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Brake temperatures
    brake_temp: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Suspension travel
    suspension_travel: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Damage
    car_damage: List[float] = field(default_factory=lambda: [0.0] * 5)  # Front, rear, left, right, center
    
    # Pit limiter
    pit_limiter_on: bool = False
    
    # ABS and TC
    abs: float = 0.0  # ABS vibration
    tc: float = 0.0   # TC action
    
    # Turbo boost (bar)
    turbo_boost: float = 0.0
    
    # Air and track temps
    air_temp: float = 0.0
    road_temp: float = 0.0
    
    # Local angular velocity
    local_angular_vel: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    
    # Final force feedback
    final_ff: float = 0.0
    
    # Brake bias (0-1, front-biased)
    brake_bias: float = 0.0
    
    # DRS
    drs_available: bool = False
    drs_enabled: bool = False
    
    # Tire core temps
    tyre_core_temp: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Clutch
    clutch: float = 0.0
    
    # Is AI controlled
    is_ai_controlled: bool = False
    
    # Tire contact point positions
    tyre_contact_point: List[List[float]] = field(default_factory=lambda: [[0.0] * 3 for _ in range(4)])
    tyre_contact_normal: List[List[float]] = field(default_factory=lambda: [[0.0] * 3 for _ in range(4)])
    tyre_contact_heading: List[List[float]] = field(default_factory=lambda: [[0.0] * 3 for _ in range(4)])
    
    # Brake pressure
    brake_pressure: float = 0.0
    
    # Front/rear brake bias
    front_brake_compound: int = 0
    rear_brake_compound: int = 0
    
    # Pad life
    pad_life: List[float] = field(default_factory=lambda: [0.0] * 4)
    disc_life: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Ignition/starter
    ignition_on: bool = False
    starter_engine_on: bool = False
    is_engine_running: bool = False
    
    # Kerb vibration
    kerb_vibration: float = 0.0
    slip_vibrations: float = 0.0
    g_vibrations: float = 0.0
    abs_vibrations: float = 0.0


@dataclass
class ACCGraphics:
    """
    Graphics/timing data
    
    Contains lap times, positions, session info, and flags.
    """
    packet_id: int = 0
    status: ACCStatus = ACCStatus.AC_OFF
    session_type: ACCSessionType = ACCSessionType.AC_UNKNOWN
    
    # Timing
    current_time: str = ""  # Current lap time (string format)
    last_time: str = ""     # Last lap time
    best_time: str = ""     # Best lap time
    split: str = ""         # Split time
    
    # Timing in milliseconds
    current_time_ms: int = 0
    last_time_ms: int = 0
    best_time_ms: int = 0
    delta_lap_time_ms: int = 0
    estimated_lap_time_ms: int = 0
    
    # Position
    completed_laps: int = 0
    position: int = 0
    current_sector_index: int = 0
    
    # Sector times (ms)
    last_sector_time_ms: int = 0
    
    # Car info
    number_of_laps: int = 0
    
    # Track info
    normalised_car_position: float = 0.0  # 0.0-1.0 around the track
    track_grip_status: int = 0  # 0=Green, 1=Fast, 2=Optimum, 3=Greasy, 4=Damp, 5=Wet, 6=Flooded
    rain_intensity: int = 0  # 0=No rain, 1=Drizzle, 2=Light, 3=Medium, 4=Heavy, 5=Thunderstorm
    rain_intensity_in_10: int = 0
    rain_intensity_in_30: int = 0
    
    # Flags
    flag: ACCFlagType = ACCFlagType.AC_NO_FLAG
    penalty: ACCPenaltyType = ACCPenaltyType.NONE
    
    # Ideal line
    ideal_line_on: bool = False
    
    # Pit status
    is_in_pit: bool = False
    is_in_pit_lane: bool = False
    
    # Mandatory pit
    mandatory_pit_done: bool = False
    
    # Wind
    wind_speed: float = 0.0
    wind_direction: float = 0.0
    
    # Car coordinates
    car_coordinates: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    
    # Is valid lap
    is_valid_lap: bool = True
    
    # Fuel estimate
    fuel_estimated_laps: float = 0.0
    
    # Missing mandatory pits
    missing_mandatory_pits: int = 0
    
    # Clock
    clock: float = 0.0  # Time of day
    
    # Direction lights
    direction_lights_left: bool = False
    direction_lights_right: bool = False
    
    # Global flags (yellow/white in sectors)
    global_yellow: bool = False
    global_yellow_s1: bool = False
    global_yellow_s2: bool = False
    global_yellow_s3: bool = False
    global_white: bool = False
    global_green: bool = False
    global_chequered: bool = False
    global_red: bool = False
    
    # Mfd pages
    mfd_tyre_set: int = 0
    mfd_fuel_to_add: float = 0.0
    mfd_tyre_pressure_lf: float = 0.0
    mfd_tyre_pressure_rf: float = 0.0
    mfd_tyre_pressure_lr: float = 0.0
    mfd_tyre_pressure_rr: float = 0.0
    
    # Track status
    track_status: str = ""
    
    # Session time left
    session_time_left_ms: int = 0


@dataclass
class ACCStatic:
    """
    Static session data - only changes when entering a new session
    """
    sm_version: str = ""
    ac_version: str = ""
    
    # Session
    number_of_sessions: int = 0
    num_cars: int = 0
    
    # Car info
    car_model: str = ""
    track: str = ""
    player_name: str = ""
    player_surname: str = ""
    player_nick: str = ""
    
    # Sector count
    sector_count: int = 0
    
    # Car specs
    max_torque: float = 0.0
    max_power: float = 0.0
    max_rpm: int = 0
    max_fuel: float = 0.0
    
    # Suspension (max travel)
    suspension_max_travel: List[float] = field(default_factory=lambda: [0.0] * 4)
    tyre_radius: List[float] = field(default_factory=lambda: [0.0] * 4)
    
    # Max turbo boost
    max_turbo_boost: float = 0.0
    
    # Penalties enabled
    penalties_enabled: bool = True
    
    # Aid settings
    aid_fuel_rate: float = 1.0
    aid_tyre_rate: float = 1.0
    aid_mechanical_damage: float = 1.0
    aid_allow_tyre_blankets: bool = True
    aid_stability: float = 0.0
    aid_auto_clutch: bool = True
    aid_auto_blip: bool = True
    
    # Pit window
    pit_window_start: int = 0
    pit_window_end: int = 0
    
    # Is online
    is_online: bool = False
    
    # Dry/wet tyres
    dry_tyres_name: str = ""
    wet_tyres_name: str = ""


# Struct format strings for unpacking shared memory
# These match the ACC shared memory layout

PHYSICS_STRUCT_FORMAT = "<" + "".join([
    "i",      # packetId
    "f",      # gas
    "f",      # brake
    "f",      # fuel
    "i",      # gear
    "i",      # rpm
    "f",      # steerAngle
    "f",      # speedKmh
    "3f",     # velocity[3]
    "3f",     # accG[3]
    "4f",     # wheelSlip[4]
    # ... more fields would be added
])


def format_laptime(ms: int) -> str:
    """Convert milliseconds to MM:SS.mmm format"""
    if ms <= 0:
        return "--:--.---"
    
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


def parse_laptime(time_str: str) -> int:
    """Parse MM:SS.mmm format to milliseconds"""
    try:
        if ":" in time_str:
            parts = time_str.split(":")
            minutes = int(parts[0])
            sec_parts = parts[1].split(".")
            seconds = int(sec_parts[0])
            millis = int(sec_parts[1]) if len(sec_parts) > 1 else 0
            return minutes * 60000 + seconds * 1000 + millis
    except (ValueError, IndexError):
        pass
    return 0
