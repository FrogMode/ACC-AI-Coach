#!/usr/bin/env python3
"""
ACC AI Coach - Main Entry Point

Usage:
    python main.py record     # Record a session (requires ACC running)
    python main.py dashboard  # Launch the analysis dashboard
    python main.py demo       # Run with demo/mock data
"""

import sys
import argparse
from pathlib import Path


def cmd_record(args):
    """Record a telemetry session"""
    from telemetry.collector import ACCSharedMemory, MockACCSharedMemory
    from telemetry.recorder import SessionRecorder
    import time
    
    print("ACC AI Coach - Session Recorder")
    print("=" * 50)
    
    # Try to connect to ACC
    shm = ACCSharedMemory()
    
    if not shm.connect():
        if args.mock:
            print("Using mock data (--mock flag)")
            shm = MockACCSharedMemory(track="monza", car="porsche_991ii_gt3_r")
            shm.connect()
        else:
            print("\nCould not connect to ACC.")
            print("Make sure ACC is running and you're in a session.")
            print("\nOr use --mock flag to record with simulated data.")
            return 1
    
    # Get static data
    static = shm.read_static()
    print(f"\nTrack: {static.track}")
    print(f"Car: {static.car_model}")
    print(f"Driver: {static.player_name}")
    
    # Create recorder
    recorder = SessionRecorder(data_dir=str(Path("data/sessions")))
    
    # Start recording
    print("\n" + "-" * 50)
    print("Recording... Press Ctrl+C to stop")
    print("-" * 50 + "\n")
    
    session_id = recorder.start_session(static)
    
    try:
        for frame in shm.stream(hz=60):
            recorder.record_frame(frame)
            
            # Print status
            print(f"\rSpeed: {frame.physics.speed_kmh:6.1f} km/h | "
                  f"Lap: {frame.graphics.completed_laps} | "
                  f"Pos: {frame.graphics.normalised_car_position*100:5.1f}% | "
                  f"Time: {frame.graphics.current_time}", end="")
            
    except KeyboardInterrupt:
        print("\n\nStopping recording...")
    finally:
        session_path = recorder.end_session()
        shm.disconnect()
        
    print(f"\nSession saved to: {session_path}")
    return 0


def cmd_dashboard(args):
    """Launch the Streamlit dashboard"""
    import subprocess
    import os
    
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    
    print("Launching ACC AI Coach Dashboard...")
    print("Open http://localhost:8501 in your browser")
    print("Press Ctrl+C to stop")
    
    # Run streamlit
    env = os.environ.copy()
    subprocess.run(
        ["streamlit", "run", str(dashboard_path), "--server.headless", "true"],
        env=env,
    )
    return 0


def cmd_demo(args):
    """Run a demo with mock data"""
    from telemetry.collector import MockACCSharedMemory
    from telemetry.recorder import SessionRecorder, SessionLoader
    from analysis.segmenter import CornerSegmenter
    from analysis.comparator import LapComparator
    from analysis.metrics import MetricsCalculator, format_laptime_ms
    import time
    
    print("ACC AI Coach - Demo Mode")
    print("=" * 50)
    
    # Create mock telemetry
    print("\n1. Generating mock telemetry...")
    shm = MockACCSharedMemory(track="monza", car="porsche_991ii_gt3_r")
    shm.connect()
    
    recorder = SessionRecorder(data_dir="data/sessions")
    static = shm.read_static()
    session_id = recorder.start_session(static)
    
    # Record 5 seconds
    start = time.time()
    frame_count = 0
    for frame in shm.stream(hz=60):
        recorder.record_frame(frame)
        frame_count += 1
        if time.time() - start > 5:
            break
    
    session_path = recorder.end_session()
    shm.disconnect()
    
    print(f"   Recorded {frame_count} frames")
    
    # Load and analyze
    print("\n2. Loading session...")
    loader = SessionLoader(session_path)
    loader.load()
    
    info = loader.get_session_info()
    telemetry = loader.get_telemetry()
    
    print(f"   Track: {info['track']}")
    print(f"   Car: {info['car']}")
    print(f"   Frames: {info['total_frames']}")
    
    # Analyze
    print("\n3. Running analysis...")
    
    if telemetry is not None and len(telemetry) > 0:
        # Corner detection
        segmenter = CornerSegmenter()
        corners = segmenter.detect_corners(telemetry)
        print(f"   Detected {len(corners)} corners")
        
        # Metrics
        calculator = MetricsCalculator()
        metrics = calculator.calculate_lap_metrics(telemetry)
        print(f"   Smoothness score: {metrics.smoothness_score:.1f}/100")
        print(f"   Speed score: {metrics.speed_score:.1f}/100")
    
    loader.close()
    
    print("\n4. Launch dashboard to visualize:")
    print(f"   python main.py dashboard")
    
    print("\n" + "=" * 50)
    print("Demo complete!")
    
    return 0


def cmd_analyze(args):
    """Analyze a recorded session"""
    from telemetry.recorder import SessionLoader
    from analysis.segmenter import CornerSegmenter
    from analysis.metrics import MetricsCalculator, format_laptime_ms
    from coach.llm_coach import LLMCoach
    
    print("ACC AI Coach - Session Analysis")
    print("=" * 50)
    
    # Find session
    session_path = Path(args.session)
    if not session_path.exists():
        # Try in data directory
        session_path = Path("data/sessions") / args.session
    
    if not session_path.exists():
        print(f"Session not found: {args.session}")
        return 1
    
    # Load
    print(f"\nLoading session: {session_path.name}")
    loader = SessionLoader(str(session_path))
    if not loader.load():
        print("Failed to load session")
        return 1
    
    info = loader.get_session_info()
    laps = loader.get_laps()
    telemetry = loader.get_telemetry()
    
    print(f"\nTrack: {info['track']}")
    print(f"Car: {info['car']}")
    print(f"Laps: {info['total_laps']}")
    
    if info['best_lap_ms'] > 0:
        print(f"Best Lap: {format_laptime_ms(info['best_lap_ms'])}")
    
    # Analyze
    if telemetry is not None:
        print("\n" + "-" * 50)
        print("Analysis")
        print("-" * 50)
        
        calculator = MetricsCalculator()
        metrics = calculator.calculate_lap_metrics(telemetry)
        
        print(f"\nPerformance Scores:")
        print(f"  Smoothness: {metrics.smoothness_score:.1f}/100")
        print(f"  Speed: {metrics.speed_score:.1f}/100")
        
        segmenter = CornerSegmenter()
        corners = segmenter.detect_corners(telemetry)
        
        if corners:
            print(f"\nCorner Analysis ({len(corners)} corners detected):")
            for corner in corners[:5]:
                print(f"  {corner.name}: "
                      f"Entry {corner.entry_speed_kmh:.0f} → "
                      f"Apex {corner.min_speed_kmh:.0f} → "
                      f"Exit {corner.exit_speed_kmh:.0f} km/h "
                      f"({corner.corner_type})")
    
    loader.close()
    print("\nAnalysis complete!")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="ACC AI Coach - Your personal racing engineer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py record              Record a session from ACC
    python main.py record --mock       Record with mock/demo data
    python main.py dashboard           Launch the analysis dashboard
    python main.py demo                Run full demo with mock data
    python main.py analyze SESSION_ID  Analyze a specific session
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record a telemetry session")
    record_parser.add_argument("--mock", action="store_true", 
                               help="Use mock data instead of live ACC")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch analysis dashboard")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo with mock data")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a recorded session")
    analyze_parser.add_argument("session", help="Session ID or path")
    
    args = parser.parse_args()
    
    if args.command == "record":
        return cmd_record(args)
    elif args.command == "dashboard":
        return cmd_dashboard(args)
    elif args.command == "demo":
        return cmd_demo(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
