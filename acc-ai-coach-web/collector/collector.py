#!/usr/bin/env python3
"""
ACC AI Coach - Telemetry Collector

Lightweight Python script that runs on your Windows PC to:
1. Read ACC telemetry from shared memory
2. Stream live data to the cloud via Supabase
3. Upload completed sessions

Usage:
    python collector.py --api-key YOUR_API_KEY

Requirements:
    pip install supabase python-dotenv
"""

import argparse
import asyncio
import json
import mmap
import struct
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase: pip install supabase")
    sys.exit(1)


# Configuration
SUPABASE_URL = "YOUR_SUPABASE_URL"  # Replace with your Supabase URL
DEFAULT_HZ = 20  # Telemetry updates per second (lower for network efficiency)


@dataclass
class TelemetryFrame:
    """Single frame of telemetry data"""
    timestamp: float
    position: float
    speed_kmh: float
    throttle: float
    brake: float
    steering: float
    gear: int
    rpm: int
    lap: int
    g_lat: float
    g_lon: float
    temp_fl: float
    temp_fr: float
    temp_rl: float
    temp_rr: float
    
    def to_dict(self):
        return asdict(self)


class ACCSharedMemory:
    """
    Reads ACC telemetry from Windows shared memory.
    
    ACC exposes three memory-mapped files:
    - acpmf_physics: Real-time physics data (~60Hz)
    - acpmf_graphics: Timing and session info
    - acpmf_static: Car and track info (read once)
    """
    
    SHM_PHYSICS = "Local\\acpmf_physics"
    SHM_GRAPHICS = "Local\\acpmf_graphics"
    SHM_STATIC = "Local\\acpmf_static"
    
    def __init__(self):
        self._physics_mmap: Optional[mmap.mmap] = None
        self._graphics_mmap: Optional[mmap.mmap] = None
        self._static_mmap: Optional[mmap.mmap] = None
        self._connected = False
        
        # Session tracking
        self.track = ""
        self.car = ""
        self.current_lap = 0
    
    def connect(self) -> bool:
        """Connect to ACC shared memory"""
        if sys.platform != "win32":
            print("Warning: ACC shared memory only available on Windows")
            return False
        
        try:
            self._physics_mmap = mmap.mmap(-1, 1580, tagname="acpmf_physics", access=mmap.ACCESS_READ)
            self._graphics_mmap = mmap.mmap(-1, 1580, tagname="acpmf_graphics", access=mmap.ACCESS_READ)
            self._static_mmap = mmap.mmap(-1, 820, tagname="acpmf_static", access=mmap.ACCESS_READ)
            self._connected = True
            
            # Read static data
            self._read_static()
            
            print(f"Connected to ACC!")
            print(f"Track: {self.track}")
            print(f"Car: {self.car}")
            
            return True
        except (FileNotFoundError, OSError) as e:
            print(f"Could not connect to ACC: {e}")
            print("Make sure ACC is running and you're in a session.")
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
    
    def _read_static(self):
        """Read static session data (car, track)"""
        if not self._static_mmap:
            return
        
        self._static_mmap.seek(60)  # Skip to car model
        car_bytes = self._static_mmap.read(66)
        self.car = car_bytes.decode('utf-16-le').rstrip('\x00')
        
        track_bytes = self._static_mmap.read(66)
        self.track = track_bytes.decode('utf-16-le').rstrip('\x00')
    
    def read_frame(self) -> Optional[TelemetryFrame]:
        """Read current telemetry frame"""
        if not self._connected:
            return None
        
        try:
            # Read physics data
            self._physics_mmap.seek(0)
            physics_data = self._physics_mmap.read(200)
            
            # Parse physics (simplified - real implementation needs exact offsets)
            offset = 4  # Skip packet ID
            gas = struct.unpack_from("<f", physics_data, offset)[0]
            offset += 4
            brake = struct.unpack_from("<f", physics_data, offset)[0]
            offset += 8  # Skip fuel
            gear = struct.unpack_from("<i", physics_data, offset)[0]
            offset += 4
            rpm = struct.unpack_from("<i", physics_data, offset)[0]
            offset += 4
            steer = struct.unpack_from("<f", physics_data, offset)[0]
            offset += 4
            speed = struct.unpack_from("<f", physics_data, offset)[0]
            
            # Read graphics data
            self._graphics_mmap.seek(0)
            graphics_data = self._graphics_mmap.read(200)
            
            # Parse graphics (simplified)
            completed_laps = struct.unpack_from("<i", graphics_data, 128)[0]
            position = struct.unpack_from("<f", graphics_data, 400)[0] if len(graphics_data) > 400 else 0
            
            return TelemetryFrame(
                timestamp=time.time(),
                position=position,
                speed_kmh=speed,
                throttle=gas,
                brake=brake,
                steering=steer,
                gear=gear,
                rpm=rpm,
                lap=completed_laps,
                g_lat=0,  # Would need proper offset
                g_lon=0,
                temp_fl=85,  # Placeholder
                temp_fr=85,
                temp_rl=82,
                temp_rr=82,
            )
        except Exception as e:
            print(f"Error reading telemetry: {e}")
            return None
    
    def is_connected(self) -> bool:
        return self._connected


class MockACCSharedMemory(ACCSharedMemory):
    """Mock telemetry for testing without ACC"""
    
    def __init__(self):
        super().__init__()
        self.track = "monza"
        self.car = "porsche_991ii_gt3_r"
        self._start_time = time.time()
        self._position = 0
        self._lap = 0
    
    def connect(self) -> bool:
        self._connected = True
        print("Using mock telemetry data")
        print(f"Track: {self.track}")
        print(f"Car: {self.car}")
        return True
    
    def read_frame(self) -> TelemetryFrame:
        import math
        
        t = time.time() - self._start_time
        self._position = (t * 0.01) % 1.0
        
        # Simulate lap completion
        if self._position < 0.01 and t > 10:
            self._lap = int(t / 100)
        
        speed = 180 + 80 * math.sin(t * 0.5)
        throttle = max(0, min(1, 0.5 + 0.5 * math.cos(t * 0.5 + 0.5)))
        brake = max(0, min(1, -0.5 * math.cos(t * 0.5 + 0.5) - 0.3))
        
        return TelemetryFrame(
            timestamp=time.time(),
            position=self._position,
            speed_kmh=speed,
            throttle=throttle,
            brake=brake,
            steering=30 * math.sin(t * 0.3),
            gear=4,
            rpm=int(5000 + 2000 * throttle),
            lap=self._lap,
            g_lat=math.sin(t * 0.3) * 1.5,
            g_lon=math.cos(t * 0.5) * 2,
            temp_fl=85 + (t % 5),
            temp_fr=84 + (t % 5),
            temp_rl=82 + (t % 5),
            temp_rr=81 + (t % 5),
        )


class TelemetryUploader:
    """Uploads telemetry to Supabase"""
    
    def __init__(self, supabase_url: str, api_key: str):
        self.client: Client = create_client(supabase_url, api_key)
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
    
    async def authenticate(self) -> bool:
        """Verify API key and get user ID"""
        try:
            # The API key should be a service role key or user's access token
            # For simplicity, we'll use it directly
            # In production, implement proper auth flow
            print("Authenticating with cloud...")
            self.user_id = "demo-user"  # Would come from auth
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    async def start_session(self, track: str, car: str) -> Optional[str]:
        """Create a new session in the database"""
        try:
            result = self.client.table('sessions').insert({
                'user_id': self.user_id,
                'track': track,
                'car': car,
                'session_type': 'practice',
                'started_at': datetime.now().isoformat(),
            }).execute()
            
            if result.data:
                self.session_id = result.data[0]['id']
                print(f"Session started: {self.session_id}")
                return self.session_id
        except Exception as e:
            print(f"Failed to start session: {e}")
        return None
    
    async def upload_frame(self, frame: TelemetryFrame):
        """Upload a single telemetry frame"""
        if not self.user_id:
            return
        
        try:
            self.client.table('live_telemetry').insert({
                'user_id': self.user_id,
                'data': frame.to_dict(),
            }).execute()
        except Exception as e:
            # Don't spam errors for every frame
            pass
    
    async def end_session(self, total_laps: int, best_lap_ms: Optional[int] = None):
        """End the current session"""
        if not self.session_id:
            return
        
        try:
            self.client.table('sessions').update({
                'ended_at': datetime.now().isoformat(),
                'total_laps': total_laps,
                'best_lap_ms': best_lap_ms,
            }).eq('id', self.session_id).execute()
            
            print(f"Session ended. Total laps: {total_laps}")
        except Exception as e:
            print(f"Failed to end session: {e}")


async def main():
    parser = argparse.ArgumentParser(description='ACC AI Coach Telemetry Collector')
    parser.add_argument('--api-key', required=True, help='Your API key from the web app')
    parser.add_argument('--url', default=SUPABASE_URL, help='Supabase URL')
    parser.add_argument('--hz', type=int, default=DEFAULT_HZ, help='Updates per second')
    parser.add_argument('--mock', action='store_true', help='Use mock data (no ACC needed)')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("ACC AI Coach - Telemetry Collector")
    print("=" * 50)
    
    # Initialize uploader
    uploader = TelemetryUploader(args.url, args.api_key)
    
    if not await uploader.authenticate():
        print("Failed to authenticate. Check your API key.")
        return
    
    # Connect to ACC
    if args.mock:
        shm = MockACCSharedMemory()
    else:
        shm = ACCSharedMemory()
    
    if not shm.connect():
        if not args.mock:
            print("\nTip: Use --mock flag to test without ACC running")
        return
    
    # Start session
    session_id = await uploader.start_session(shm.track, shm.car)
    if not session_id:
        print("Failed to start session in cloud")
        return
    
    print(f"\nStreaming telemetry at {args.hz}Hz...")
    print("Press Ctrl+C to stop\n")
    
    interval = 1.0 / args.hz
    frame_count = 0
    last_lap = 0
    
    try:
        while True:
            start = time.time()
            
            frame = shm.read_frame()
            if frame:
                await uploader.upload_frame(frame)
                frame_count += 1
                
                # Detect lap change
                if frame.lap > last_lap:
                    print(f"Lap {frame.lap} completed!")
                    last_lap = frame.lap
                
                # Status update every second
                if frame_count % args.hz == 0:
                    print(f"\rSpeed: {frame.speed_kmh:6.1f} km/h | "
                          f"Lap: {frame.lap} | "
                          f"Pos: {frame.position*100:5.1f}% | "
                          f"Frames: {frame_count}", end="")
            
            # Maintain target Hz
            elapsed = time.time() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        await uploader.end_session(last_lap)
        shm.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
