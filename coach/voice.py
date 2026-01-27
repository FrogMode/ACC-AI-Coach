"""
Voice Synthesis for Real-Time Coaching

Uses edge-tts (Microsoft) or Coqui TTS for text-to-speech.
Designed for low-latency real-time callouts.
"""

import asyncio
import tempfile
import os
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
import threading
import queue


@dataclass
class VoiceConfig:
    """Voice synthesis configuration"""
    voice: str = "en-US-GuyNeural"  # Microsoft voice
    rate: str = "+10%"  # Speak faster for racing
    pitch: str = "+0Hz"
    volume: str = "+0%"


class VoiceCoach:
    """
    Real-time voice coaching using TTS.
    
    Usage:
        coach = VoiceCoach()
        coach.speak("Brake later at turn one")
    """
    
    def __init__(self, 
                 config: Optional[VoiceConfig] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialize the voice coach.
        
        Args:
            config: Voice configuration
            cache_dir: Directory to cache generated audio
        """
        self.config = config or VoiceConfig()
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "acc_coach_audio"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio playback queue
        self._queue: queue.Queue = queue.Queue()
        self._playback_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Cache for frequently used phrases
        self._audio_cache: dict = {}
    
    def start(self):
        """Start the voice coach (background thread for playback)"""
        self._running = True
        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()
    
    def stop(self):
        """Stop the voice coach"""
        self._running = False
        if self._playback_thread:
            self._playback_thread.join(timeout=1)
    
    def speak(self, text: str, priority: bool = False):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            priority: If True, clear queue and speak immediately
        """
        if priority:
            # Clear existing queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
        
        self._queue.put(text)
    
    def speak_sync(self, text: str):
        """Synchronously speak text (blocks until complete)"""
        audio_path = self._get_audio(text)
        if audio_path:
            self._play_audio(audio_path)
    
    def _get_audio(self, text: str) -> Optional[Path]:
        """Get audio file for text (from cache or generate)"""
        # Check cache
        cache_key = hash(text + self.config.voice)
        if cache_key in self._audio_cache:
            return self._audio_cache[cache_key]
        
        # Generate audio
        audio_path = self.cache_dir / f"{cache_key}.mp3"
        
        if not audio_path.exists():
            try:
                asyncio.run(self._generate_audio(text, audio_path))
            except Exception as e:
                print(f"TTS error: {e}")
                return None
        
        self._audio_cache[cache_key] = audio_path
        return audio_path
    
    async def _generate_audio(self, text: str, output_path: Path):
        """Generate audio using edge-tts"""
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(
                text,
                voice=self.config.voice,
                rate=self.config.rate,
                pitch=self.config.pitch,
                volume=self.config.volume,
            )
            
            await communicate.save(str(output_path))
            
        except ImportError:
            print("edge-tts not installed. Install with: pip install edge-tts")
            raise
    
    def _play_audio(self, audio_path: Path):
        """Play audio file"""
        try:
            # Try different playback methods
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                os.system(f'afplay "{audio_path}"')
            elif system == "Windows":
                import winsound
                # Convert mp3 to wav if needed, or use alternative
                os.system(f'start /min "" "{audio_path}"')
            else:  # Linux
                os.system(f'mpg123 -q "{audio_path}" 2>/dev/null || aplay "{audio_path}" 2>/dev/null')
                
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    def _playback_loop(self):
        """Background thread for audio playback"""
        while self._running:
            try:
                text = self._queue.get(timeout=0.1)
                audio_path = self._get_audio(text)
                if audio_path:
                    self._play_audio(audio_path)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Playback error: {e}")
    
    def preload_phrases(self, phrases: list):
        """Pre-generate audio for common phrases"""
        for phrase in phrases:
            self._get_audio(phrase)
    
    @staticmethod
    def list_voices() -> list:
        """List available voices"""
        try:
            import asyncio
            import edge_tts
            
            async def get_voices():
                voices = await edge_tts.list_voices()
                return [v["ShortName"] for v in voices if v["Locale"].startswith("en-")]
            
            return asyncio.run(get_voices())
        except ImportError:
            return ["edge-tts not installed"]


# Common racing callouts to preload
COMMON_CALLOUTS = [
    "Brake",
    "Brake later",
    "Brake earlier", 
    "More speed",
    "Lift",
    "Flat out",
    "Good corner",
    "Focus here",
    "Watch the kerb",
    "Smooth inputs",
    "Trail brake",
    "Earlier throttle",
    "Later throttle",
    "Tighter line",
    "Wider line",
]


def demo():
    """Demo the voice coach"""
    print("Voice Coach Demo")
    print("=" * 40)
    
    coach = VoiceCoach()
    
    print("Available voices (English):")
    voices = coach.list_voices()
    for v in voices[:10]:
        print(f"  - {v}")
    
    print("\nSpeaking test phrases...")
    
    test_phrases = [
        "Welcome to ACC AI Coach",
        "Turn one coming up, brake at the 100 meter board",
        "Good lap! You gained 2 tenths in sector 2",
    ]
    
    for phrase in test_phrases:
        print(f"Speaking: {phrase}")
        coach.speak_sync(phrase)
    
    print("\nDone!")


if __name__ == "__main__":
    demo()
