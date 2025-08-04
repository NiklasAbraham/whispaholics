# Example configuration file
# Copy this to config.py and modify as needed

from dataclasses import dataclass
from pynput.keyboard import Key
from pynput import keyboard
import pyaudio


@dataclass
class Config:
    """Configuration settings for the speech recognition system"""
    
    # Server settings - CHANGE THIS to match your WhisperLiveKit server
    websocket_url: str = "ws://localhost:8000/asr"  # Default WhisperLiveKit URL
    
    # Audio settings
    channels: int = 1
    rate: int = 16000
    chunk_duration_ms: float = 1000.0  # Duration of each audio chunk in milliseconds
    
    @property
    def chunk_size(self) -> int:
        """Calculate chunk size in samples from duration in milliseconds"""
        return int(self.rate * self.chunk_duration_ms / 1000)
    
    # Hotkey configuration - Choose one of the following:
    
    # Option 1: Ctrl+Alt+R (default)
    hotkey: frozenset = frozenset({Key.ctrl_l, Key.alt_l, keyboard.KeyCode.from_char('r')})
    
    # Option 2: F12 key only
    # hotkey: frozenset = frozenset({Key.f12})
    
    # Option 3: Ctrl+Shift+S
    # hotkey: frozenset = frozenset({Key.ctrl_l, Key.shift, keyboard.KeyCode.from_char('s')})
    
    # Timing settings
    hotkey_cooldown: float = 0.5  # seconds between hotkey activations
    max_wait_time: float = 10.0   # seconds to wait for server processing after stopping
    typing_delay: float = 0.015   # seconds between characters when typing
    
    @property
    def audio_format(self):
        """Get PyAudio format constant"""
        return pyaudio.paInt16
