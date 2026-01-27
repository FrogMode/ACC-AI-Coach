"""
Session Recorder

Records telemetry sessions to disk for later analysis.
Uses SQLite for metadata and Parquet for high-frequency telemetry data.
"""

import sqlite3
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .collector import TelemetryFrame, ACCSharedMemory, MockACCSharedMemory
from .models import ACCPhysics, ACCGraphics, ACCStatic, ACCStatus


@dataclass
class SessionInfo:
    """Metadata about a recorded session"""
    session_id: str
    track: str
    car: str
    player_name: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_laps: int = 0
    best_lap_ms: int = 0
    total_frames: int = 0


@dataclass 
class LapInfo:
    """Information about a single lap"""
    lap_number: int
    lap_time_ms: int
    sector1_ms: int = 0
    sector2_ms: int = 0
    sector3_ms: int = 0
    is_valid: bool = True
    fuel_used: float = 0.0
    tyre_wear_fl: float = 0.0
    tyre_wear_fr: float = 0.0
    tyre_wear_rl: float = 0.0
    tyre_wear_rr: float = 0.0


class SessionRecorder:
    """
    Records telemetry sessions to disk.
    
    Data structure:
        /data/sessions/{session_id}/
            session.db      # SQLite: metadata, laps, events
            telemetry.parquet  # High-frequency telemetry
    """
    
    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._session_dir: Optional[Path] = None
        self._db: Optional[sqlite3.Connection] = None
        self._session_info: Optional[SessionInfo] = None
        self._frames: List[Dict[str, Any]] = []
        self._current_lap = 0
        self._lap_start_fuel = 0.0
        self._recording = False
    
    def start_session(self, static: ACCStatic, session_type: str = "practice") -> str:
        """
        Start recording a new session.
        
        Args:
            static: Static session data from ACC
            session_type: Type of session (practice, qualify, race)
            
        Returns:
            Session ID string
        """
        # Generate session ID
        timestamp = datetime.now()
        session_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{static.track}_{static.car_model}"
        
        # Create session directory
        self._session_dir = self.data_dir / session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session info
        self._session_info = SessionInfo(
            session_id=session_id,
            track=static.track,
            car=static.car_model,
            player_name=f"{static.player_name} {static.player_surname}".strip(),
            session_type=session_type,
            start_time=timestamp,
        )
        
        # Initialize SQLite database
        self._init_database()
        
        # Save session info
        self._save_session_info()
        
        # Save static data as JSON
        static_path = self._session_dir / "static.json"
        with open(static_path, "w") as f:
            json.dump(asdict(static), f, indent=2)
        
        self._frames = []
        self._current_lap = 0
        self._recording = True
        
        print(f"Started recording session: {session_id}")
        return session_id
    
    def _init_database(self):
        """Initialize the SQLite database schema"""
        db_path = self._session_dir / "session.db"
        self._db = sqlite3.connect(str(db_path))
        
        cursor = self._db.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session (
                session_id TEXT PRIMARY KEY,
                track TEXT,
                car TEXT,
                player_name TEXT,
                session_type TEXT,
                start_time TEXT,
                end_time TEXT,
                total_laps INTEGER,
                best_lap_ms INTEGER,
                total_frames INTEGER
            )
        """)
        
        # Laps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS laps (
                lap_number INTEGER PRIMARY KEY,
                lap_time_ms INTEGER,
                sector1_ms INTEGER,
                sector2_ms INTEGER,
                sector3_ms INTEGER,
                is_valid INTEGER,
                fuel_used REAL,
                tyre_wear_fl REAL,
                tyre_wear_fr REAL,
                tyre_wear_rl REAL,
                tyre_wear_rr REAL
            )
        """)
        
        # Events table (pit stops, penalties, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                lap_number INTEGER,
                event_type TEXT,
                event_data TEXT
            )
        """)
        
        self._db.commit()
    
    def _save_session_info(self):
        """Save session info to database"""
        if not self._db or not self._session_info:
            return
        
        cursor = self._db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO session 
            (session_id, track, car, player_name, session_type, start_time, 
             end_time, total_laps, best_lap_ms, total_frames)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self._session_info.session_id,
            self._session_info.track,
            self._session_info.car,
            self._session_info.player_name,
            self._session_info.session_type,
            self._session_info.start_time.isoformat(),
            self._session_info.end_time.isoformat() if self._session_info.end_time else None,
            self._session_info.total_laps,
            self._session_info.best_lap_ms,
            self._session_info.total_frames,
        ))
        self._db.commit()
    
    def record_frame(self, frame: TelemetryFrame):
        """
        Record a single telemetry frame.
        
        Call this for each frame from the telemetry collector.
        """
        if not self._recording:
            return
        
        physics = frame.physics
        graphics = frame.graphics
        
        # Create flat dictionary for Parquet
        frame_data = {
            "timestamp": frame.timestamp,
            "lap": graphics.completed_laps,
            "position": graphics.normalised_car_position,
            
            # Inputs
            "throttle": physics.gas,
            "brake": physics.brake,
            "steering": physics.steer_angle,
            "clutch": physics.clutch,
            "gear": physics.gear,
            
            # Speed/RPM
            "speed_kmh": physics.speed_kmh,
            "rpm": physics.rpm,
            
            # G-forces
            "g_lat": physics.acc_g[0] if physics.acc_g else 0,
            "g_lon": physics.acc_g[1] if len(physics.acc_g) > 1 else 0,
            "g_vert": physics.acc_g[2] if len(physics.acc_g) > 2 else 0,
            
            # Tires - slip
            "slip_fl": physics.wheel_slip[0] if physics.wheel_slip else 0,
            "slip_fr": physics.wheel_slip[1] if len(physics.wheel_slip) > 1 else 0,
            "slip_rl": physics.wheel_slip[2] if len(physics.wheel_slip) > 2 else 0,
            "slip_rr": physics.wheel_slip[3] if len(physics.wheel_slip) > 3 else 0,
            
            # Tires - core temp
            "temp_fl": physics.tyre_core_temp[0] if physics.tyre_core_temp else 0,
            "temp_fr": physics.tyre_core_temp[1] if len(physics.tyre_core_temp) > 1 else 0,
            "temp_rl": physics.tyre_core_temp[2] if len(physics.tyre_core_temp) > 2 else 0,
            "temp_rr": physics.tyre_core_temp[3] if len(physics.tyre_core_temp) > 3 else 0,
            
            # Brakes - temp
            "brake_temp_fl": physics.brake_temp[0] if physics.brake_temp else 0,
            "brake_temp_fr": physics.brake_temp[1] if len(physics.brake_temp) > 1 else 0,
            "brake_temp_rl": physics.brake_temp[2] if len(physics.brake_temp) > 2 else 0,
            "brake_temp_rr": physics.brake_temp[3] if len(physics.brake_temp) > 3 else 0,
            
            # Fuel
            "fuel": physics.fuel,
            
            # TC/ABS
            "tc": physics.tc,
            "abs": physics.abs,
            
            # Lap validity
            "is_valid_lap": graphics.is_valid_lap,
            
            # Position in world (if available)
            "world_x": graphics.car_coordinates[0] if graphics.car_coordinates else 0,
            "world_y": graphics.car_coordinates[1] if len(graphics.car_coordinates) > 1 else 0,
            "world_z": graphics.car_coordinates[2] if len(graphics.car_coordinates) > 2 else 0,
        }
        
        self._frames.append(frame_data)
        
        # Detect lap completion
        if graphics.completed_laps > self._current_lap and self._current_lap > 0:
            self._on_lap_complete(graphics)
        
        self._current_lap = graphics.completed_laps
        
        # Flush to disk periodically (every 1000 frames ≈ 17 seconds at 60Hz)
        if len(self._frames) >= 1000:
            self._flush_frames()
    
    def _on_lap_complete(self, graphics: ACCGraphics):
        """Called when a lap is completed"""
        from .models import parse_laptime
        
        lap_time_ms = parse_laptime(graphics.last_time)
        
        if lap_time_ms > 0:
            lap_info = LapInfo(
                lap_number=self._current_lap,
                lap_time_ms=lap_time_ms,
                is_valid=graphics.is_valid_lap,
            )
            
            # Save to database
            cursor = self._db.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO laps 
                (lap_number, lap_time_ms, sector1_ms, sector2_ms, sector3_ms, 
                 is_valid, fuel_used, tyre_wear_fl, tyre_wear_fr, tyre_wear_rl, tyre_wear_rr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lap_info.lap_number,
                lap_info.lap_time_ms,
                lap_info.sector1_ms,
                lap_info.sector2_ms,
                lap_info.sector3_ms,
                1 if lap_info.is_valid else 0,
                lap_info.fuel_used,
                lap_info.tyre_wear_fl,
                lap_info.tyre_wear_fr,
                lap_info.tyre_wear_rl,
                lap_info.tyre_wear_rr,
            ))
            self._db.commit()
            
            # Update session info
            self._session_info.total_laps = self._current_lap
            if lap_info.is_valid:
                if self._session_info.best_lap_ms == 0 or lap_time_ms < self._session_info.best_lap_ms:
                    self._session_info.best_lap_ms = lap_time_ms
            
            print(f"Lap {self._current_lap}: {graphics.last_time} {'(invalid)' if not graphics.is_valid_lap else ''}")
    
    def _flush_frames(self):
        """Write accumulated frames to Parquet file"""
        if not self._frames:
            return
        
        df = pd.DataFrame(self._frames)
        
        parquet_path = self._session_dir / "telemetry.parquet"
        
        # Append to existing or create new
        if parquet_path.exists():
            existing = pd.read_parquet(parquet_path)
            df = pd.concat([existing, df], ignore_index=True)
        
        df.to_parquet(parquet_path, index=False)
        
        self._session_info.total_frames += len(self._frames)
        self._frames = []
    
    def end_session(self) -> Optional[str]:
        """
        End the current recording session.
        
        Returns:
            Path to the session directory, or None if no session was active
        """
        if not self._recording:
            return None
        
        # Flush remaining frames
        self._flush_frames()
        
        # Update session end time
        self._session_info.end_time = datetime.now()
        self._save_session_info()
        
        # Close database
        if self._db:
            self._db.close()
            self._db = None
        
        self._recording = False
        
        session_path = str(self._session_dir)
        print(f"Session saved to: {session_path}")
        print(f"Total laps: {self._session_info.total_laps}")
        print(f"Total frames: {self._session_info.total_frames}")
        
        return session_path


class SessionLoader:
    """Load and query recorded sessions"""
    
    def __init__(self, session_path: str):
        self.session_path = Path(session_path)
        self._db: Optional[sqlite3.Connection] = None
        self._telemetry: Optional[pd.DataFrame] = None
    
    def load(self) -> bool:
        """Load session data"""
        db_path = self.session_path / "session.db"
        parquet_path = self.session_path / "telemetry.parquet"
        
        if not db_path.exists():
            print(f"Session database not found: {db_path}")
            return False
        
        self._db = sqlite3.connect(str(db_path))
        
        if parquet_path.exists():
            self._telemetry = pd.read_parquet(parquet_path)
        
        return True
    
    def get_session_info(self) -> Optional[Dict]:
        """Get session metadata"""
        if not self._db:
            return None
        
        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM session LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_laps(self) -> List[Dict]:
        """Get all lap data"""
        if not self._db:
            return []
        
        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM laps ORDER BY lap_number")
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def get_lap_telemetry(self, lap_number: int) -> Optional[pd.DataFrame]:
        """Get telemetry for a specific lap"""
        if self._telemetry is None:
            return None
        
        return self._telemetry[self._telemetry["lap"] == lap_number].copy()
    
    def get_telemetry(self) -> Optional[pd.DataFrame]:
        """Get all telemetry data"""
        return self._telemetry
    
    def close(self):
        """Close database connection"""
        if self._db:
            self._db.close()
            self._db = None


# Demo recording function
def demo_recording():
    """Demo the session recorder with mock data"""
    print("ACC AI Coach - Session Recorder Demo")
    print("=" * 50)
    
    # Use mock telemetry
    shm = MockACCSharedMemory(track="monza", car="porsche_991ii_gt3_r")
    shm.connect()
    
    # Create recorder
    recorder = SessionRecorder()
    
    # Start session
    static = shm.read_static()
    session_id = recorder.start_session(static, session_type="practice")
    
    print(f"\nRecording for 5 seconds...")
    
    try:
        start = time.time()
        for frame in shm.stream(hz=60):
            recorder.record_frame(frame)
            
            # Record for 5 seconds
            if time.time() - start > 5:
                break
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        session_path = recorder.end_session()
        shm.disconnect()
    
    # Load and display session
    print("\n" + "=" * 50)
    print("Loading recorded session...")
    
    loader = SessionLoader(session_path)
    if loader.load():
        info = loader.get_session_info()
        print(f"Session ID: {info['session_id']}")
        print(f"Track: {info['track']}")
        print(f"Car: {info['car']}")
        print(f"Total frames: {info['total_frames']}")
        
        telemetry = loader.get_telemetry()
        if telemetry is not None:
            print(f"\nTelemetry shape: {telemetry.shape}")
            print(f"Columns: {list(telemetry.columns)}")
            print(f"\nSpeed stats:")
            print(f"  Min: {telemetry['speed_kmh'].min():.1f} km/h")
            print(f"  Max: {telemetry['speed_kmh'].max():.1f} km/h")
            print(f"  Avg: {telemetry['speed_kmh'].mean():.1f} km/h")
        
        loader.close()


if __name__ == "__main__":
    demo_recording()
