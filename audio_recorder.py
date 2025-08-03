"""Audio recording functionality for speech recognition."""

import pyaudio
import logging
from queue import Queue, Empty
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Handles audio recording and streaming"""
    
    def __init__(self, config: Config):
        self.config = config
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.audio_queue = Queue()
        
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            return
            
        try:
            self.stream = self.audio.open(
                format=self.config.audio_format,
                channels=self.config.channels,
                rate=self.config.rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback
            )
            self.stream.start_stream()
            self.is_recording = True
            logger.info("Audio recording started")
        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
            raise
            
    def stop_recording(self):
        """Stop audio recording"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        logger.info("Audio recording stopped")
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for streaming"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
        
    def get_audio_chunk(self) -> Optional[bytes]:
        """Get the next audio chunk"""
        try:
            return self.audio_queue.get_nowait()
        except Empty:
            return None
            
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_recording()
        self.audio.terminate()
