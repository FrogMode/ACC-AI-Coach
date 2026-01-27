"""
ACC Shared Memory Telemetry Collector

Reads telemetry data from ACC's shared memory on Windows.
The game exposes three memory-mapped files:
- acpmf_physics: Real-time physics data (~60Hz)
- acpmf_graphics: Graphics/timing info
- acpmf_static: Static session data

This collector runs in a loop and yields telemetry frames.
"""

import ctypes
import mmap
import struct
import time
from dataclasses import dataclass, field
from typing import Optional, Generator, Callable
from pathlib import Path
import sys

from .models import ACCPhysics, ACCGraphics, ACCStatic, ACCStatus


# Shared memory names
SHM_PHYSICS = "Local\\acpmf_physics"
SHM_GRAPHICS = "Local\\acpmf_graphics"
SHM_STATIC = "Local\\acpmf_static"

# Shared memory sizes (bytes) - must match ACC's allocation
SHM_PHYSICS_SIZE = 1580
SHM_GRAPHICS_SIZE = 1580
SHM_STATIC_SIZE = 820


@dataclass
class TelemetryFrame:
    """A single frame of telemetry data with timestamp"""
    timestamp: float  # Unix timestamp
    physics: ACCPhysics
    graphics: ACCGraphics
    static: Optional[ACCStatic] = None  # Only included on first frame or when changed


class ACCSharedMemory:
    """
    Reads ACC shared memory telemetry.
    
    Usage:
        shm = ACCSharedMemory()
        if shm.connect():
            for frame in shm.stream():
                print(f"Speed: {frame.physics.speed_kmh} km/h")
    """
    
    def __init__(self):
        self._physics_mmap: Optional[mmap.mmap] = None
        self._graphics_mmap: Optional[mmap.mmap] = None
        self._static_mmap: Optional[mmap.mmap] = None
        self._connected = False
        self._last_static: Optional[ACCStatic] = None
    
    @property
    def is_windows(self) -> bool:
        return sys.platform == "win32"
    
    def connect(self) -> bool:
        """
        Connect to ACC shared memory.
        
        Returns True if successful, False if ACC is not running or
        shared memory is not available.
        """
        if not self.is_windows:
            print("Warning: ACC shared memory is only available on Windows")
            return False
        
        try:
            # On Windows, we use the tagname parameter to access named shared memory
            self._physics_mmap = mmap.mmap(-1, SHM_PHYSICS_SIZE, tagname="acpmf_physics", access=mmap.ACCESS_READ)
            self._graphics_mmap = mmap.mmap(-1, SHM_GRAPHICS_SIZE, tagname="acpmf_graphics", access=mmap.ACCESS_READ)
            self._static_mmap = mmap.mmap(-1, SHM_STATIC_SIZE, tagname="acpmf_static", access=mmap.ACCESS_READ)
            self._connected = True
            return True
        except (FileNotFoundError, OSError) as e:
            print(f"Could not connect to ACC shared memory: {e}")
            print("Make sure ACC is running!")
            return False
    
    def disconnect(self):
        """Close shared memory connections"""
        if self._physics_mmap:
            self._physics_mmap.close()
        if self._graphics_mmap:
            self._graphics_mmap.close()
        if self._static_mmap:
            self._static_mmap.close()
        self._connected = False
    
    def read_physics(self) -> ACCPhysics:
        """Read current physics data from shared memory"""
        if not self._physics_mmap:
            return ACCPhysics()
        
        self._physics_mmap.seek(0)
        data = self._physics_mmap.read(SHM_PHYSICS_SIZE)
        
        return self._parse_physics(data)
    
    def read_graphics(self) -> ACCGraphics:
        """Read current graphics data from shared memory"""
        if not self._graphics_mmap:
            return ACCGraphics()
        
        self._graphics_mmap.seek(0)
        data = self._graphics_mmap.read(SHM_GRAPHICS_SIZE)
        
        return self._parse_graphics(data)
    
    def read_static(self) -> ACCStatic:
        """Read static session data from shared memory"""
        if not self._static_mmap:
            return ACCStatic()
        
        self._static_mmap.seek(0)
        data = self._static_mmap.read(SHM_STATIC_SIZE)
        
        return self._parse_static(data)
    
    def _parse_physics(self, data: bytes) -> ACCPhysics:
        """Parse raw physics data into ACCPhysics dataclass"""
        physics = ACCPhysics()
        
        try:
            # Unpack the beginning of the struct
            # Note: This is a simplified parser - full implementation would
            # unpack all fields according to ACC documentation
            offset = 0
            
            # packetId (int32)
            physics.packet_id = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # gas (float)
            physics.gas = struct.unpack_from("<f", data, offset)[0]
            offset += 4
            
            # brake (float)
            physics.brake = struct.unpack_from("<f", data, offset)[0]
            offset += 4
            
            # fuel (float)
            physics.fuel = struct.unpack_from("<f", data, offset)[0]
            offset += 4
            
            # gear (int32)
            physics.gear = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # rpm (int32)
            physics.rpm = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # steerAngle (float)
            physics.steer_angle = struct.unpack_from("<f", data, offset)[0]
            offset += 4
            
            # speedKmh (float)
            physics.speed_kmh = struct.unpack_from("<f", data, offset)[0]
            offset += 4
            
            # velocity[3] (3 floats)
            physics.velocity = list(struct.unpack_from("<3f", data, offset))
            offset += 12
            
            # accG[3] (3 floats)
            physics.acc_g = list(struct.unpack_from("<3f", data, offset))
            offset += 12
            
            # wheelSlip[4] (4 floats)
            physics.wheel_slip = list(struct.unpack_from("<4f", data, offset))
            offset += 16
            
            # Skip to wheel pressures (simplified - real implementation needs exact offsets)
            # wheelPressure[4] - offset varies by ACC version
            
            # Tire temps would be parsed here with correct offsets
            # tyre_core_temp[4], brake_temp[4], etc.
            
        except struct.error as e:
            print(f"Error parsing physics data: {e}")
        
        return physics
    
    def _parse_graphics(self, data: bytes) -> ACCGraphics:
        """Parse raw graphics data into ACCGraphics dataclass"""
        graphics = ACCGraphics()
        
        try:
            offset = 0
            
            # packetId (int32)
            graphics.packet_id = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # status (int32 -> ACCStatus enum)
            status_val = struct.unpack_from("<i", data, offset)[0]
            graphics.status = ACCStatus(status_val) if status_val in ACCStatus._value2member_map_ else ACCStatus.AC_OFF
            offset += 4
            
            # session (int32 -> ACCSessionType)
            session_val = struct.unpack_from("<i", data, offset)[0]
            graphics.session_type = ACCSessionType(session_val) if session_val in ACCSessionType._value2member_map_ else ACCSessionType.AC_UNKNOWN
            offset += 4
            
            # currentTime (wchar[15] - 30 bytes)
            current_time_bytes = data[offset:offset+30]
            graphics.current_time = current_time_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 30
            
            # lastTime (wchar[15])
            last_time_bytes = data[offset:offset+30]
            graphics.last_time = last_time_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 30
            
            # bestTime (wchar[15])
            best_time_bytes = data[offset:offset+30]
            graphics.best_time = best_time_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 30
            
            # split (wchar[15])
            split_bytes = data[offset:offset+30]
            graphics.split = split_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 30
            
            # completedLaps (int32)
            graphics.completed_laps = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # position (int32)
            graphics.position = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # Skip ahead to normalizedCarPosition
            # (Real implementation needs exact offsets from ACC docs)
            
            # carCoordinates[3] would be parsed here
            
        except (struct.error, UnicodeDecodeError) as e:
            print(f"Error parsing graphics data: {e}")
        
        return graphics
    
    def _parse_static(self, data: bytes) -> ACCStatic:
        """Parse raw static data into ACCStatic dataclass"""
        static = ACCStatic()
        
        try:
            offset = 0
            
            # smVersion (wchar[15] - 30 bytes)
            sm_version_bytes = data[offset:offset+30]
            static.sm_version = sm_version_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 30
            
            # acVersion (wchar[15])
            ac_version_bytes = data[offset:offset+30]
            static.ac_version = ac_version_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 30
            
            # numberOfSessions (int32)
            static.number_of_sessions = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # numCars (int32)
            static.num_cars = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            
            # carModel (wchar[33] - 66 bytes)
            car_model_bytes = data[offset:offset+66]
            static.car_model = car_model_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 66
            
            # track (wchar[33])
            track_bytes = data[offset:offset+66]
            static.track = track_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 66
            
            # playerName (wchar[33])
            player_name_bytes = data[offset:offset+66]
            static.player_name = player_name_bytes.decode('utf-16-le').rstrip('\x00')
            offset += 66
            
            # Additional fields would be parsed here
            
        except (struct.error, UnicodeDecodeError) as e:
            print(f"Error parsing static data: {e}")
        
        return static
    
    def stream(self, 
               hz: int = 60, 
               include_static: bool = True,
               callback: Optional[Callable[[TelemetryFrame], None]] = None
               ) -> Generator[TelemetryFrame, None, None]:
        """
        Stream telemetry frames at the specified rate.
        
        Args:
            hz: Target polling rate in Hz (default 60)
            include_static: Include static data in first frame
            callback: Optional callback function for each frame
            
        Yields:
            TelemetryFrame objects with physics, graphics, and optionally static data
        """
        if not self._connected:
            raise RuntimeError("Not connected to ACC shared memory. Call connect() first.")
        
        interval = 1.0 / hz
        last_static_packet_id = -1
        
        while True:
            start_time = time.time()
            
            physics = self.read_physics()
            graphics = self.read_graphics()
            
            # Only include static if it changed or on first frame
            static = None
            if include_static:
                current_static = self.read_static()
                # Check if static data changed (new session)
                if self._last_static is None or current_static.car_model != self._last_static.car_model:
                    static = current_static
                    self._last_static = current_static
            
            frame = TelemetryFrame(
                timestamp=start_time,
                physics=physics,
                graphics=graphics,
                static=static
            )
            
            if callback:
                callback(frame)
            
            yield frame
            
            # Maintain target Hz
            elapsed = time.time() - start_time
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def is_game_running(self) -> bool:
        """Check if ACC is currently running and in a session"""
        if not self._connected:
            return False
        
        graphics = self.read_graphics()
        return graphics.status == ACCStatus.AC_LIVE


class MockACCSharedMemory(ACCSharedMemory):
    """
    Mock shared memory for testing without ACC running.
    Generates synthetic telemetry data.
    """
    
    def __init__(self, track: str = "monza", car: str = "porsche_991ii_gt3_r"):
        super().__init__()
        self._track = track
        self._car = car
        self._position = 0.0
        self._lap = 0
        self._start_time = time.time()
    
    def connect(self) -> bool:
        self._connected = True
        return True
    
    def read_physics(self) -> ACCPhysics:
        """Generate mock physics data"""
        import math
        
        t = time.time() - self._start_time
        
        # Simulate varying speed (80-280 km/h)
        base_speed = 180 + 100 * math.sin(t * 0.5)
        
        # Simulate inputs based on speed changes
        speed_derivative = 50 * math.cos(t * 0.5)
        throttle = max(0, min(1, 0.5 + speed_derivative / 100))
        brake = max(0, min(1, -speed_derivative / 100))
        
        # Simulate steering
        steering = 30 * math.sin(t * 0.3)
        
        return ACCPhysics(
            packet_id=int(t * 60),
            gas=throttle,
            brake=brake,
            fuel=80.0,
            gear=4,
            rpm=int(5000 + 2000 * throttle),
            steer_angle=steering,
            speed_kmh=base_speed,
            velocity=[base_speed / 3.6, 0, 0],
            acc_g=[speed_derivative / 50, steering / 100, 0],
            wheel_slip=[0.02, 0.02, 0.03, 0.03],
            tyre_core_temp=[85.0, 85.0, 82.0, 82.0],
            brake_temp=[400.0, 400.0, 350.0, 350.0],
        )
    
    def read_graphics(self) -> ACCGraphics:
        """Generate mock graphics data"""
        t = time.time() - self._start_time
        
        # Progress around track
        self._position = (t * 0.01) % 1.0
        
        # Complete lap every ~100 seconds
        new_lap = int(t / 100)
        if new_lap > self._lap:
            self._lap = new_lap
        
        return ACCGraphics(
            packet_id=int(t * 60),
            status=ACCStatus.AC_LIVE,
            session_type=ACCSessionType.AC_PRACTICE,
            current_time="1:45.123",
            last_time="1:48.456",
            best_time="1:44.789",
            completed_laps=self._lap,
            position=1,
            normalised_car_position=self._position,
            is_valid_lap=True,
        )
    
    def read_static(self) -> ACCStatic:
        """Generate mock static data"""
        return ACCStatic(
            sm_version="1.8",
            ac_version="1.9.0",
            car_model=self._car,
            track=self._track,
            player_name="Test",
            player_surname="Driver",
            sector_count=3,
            max_rpm=9000,
            max_fuel=120.0,
        )


# Convenience function for quick testing
def demo():
    """Demo the telemetry collector"""
    print("ACC AI Coach - Telemetry Collector Demo")
    print("=" * 50)
    
    # Use mock data if not on Windows or ACC not running
    shm = ACCSharedMemory()
    if not shm.connect():
        print("Using mock data for demonstration...")
        shm = MockACCSharedMemory()
        shm.connect()
    
    print(f"\nConnected! Reading telemetry...")
    print("-" * 50)
    
    try:
        for i, frame in enumerate(shm.stream(hz=10)):
            print(f"\rSpeed: {frame.physics.speed_kmh:6.1f} km/h | "
                  f"Throttle: {frame.physics.gas*100:5.1f}% | "
                  f"Brake: {frame.physics.brake*100:5.1f}% | "
                  f"Gear: {frame.physics.gear} | "
                  f"Lap: {frame.graphics.completed_laps} | "
                  f"Pos: {frame.graphics.normalised_car_position*100:5.1f}%", end="")
            
            if i > 100:  # Stop after ~10 seconds at 10Hz
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    finally:
        shm.disconnect()
        print("\nDisconnected from shared memory")


if __name__ == "__main__":
    demo()
