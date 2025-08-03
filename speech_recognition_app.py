"""Main speech recognition application."""

import asyncio
import threading
import time
import logging
import os
import struct
from typing import Optional
from pynput.keyboard import Listener
from config import Config
from audio_recorder import AudioRecorder
from websocket_client import WebSocketClient
from text_inserter import TextInserter

logger = logging.getLogger(__name__)


class SpeechRecognitionApp:
    """Main application class that coordinates all components"""
    
    def __init__(self, config: Config):
        self.config = config
        self.recorder = AudioRecorder(config)
        self.websocket_client = WebSocketClient(config)
        self.text_inserter = TextInserter(config.typing_delay)
        
        self.is_recording = False
        self.hotkey_pressed = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.audio_task: Optional[asyncio.Task] = None
        self.listen_task: Optional[asyncio.Task] = None
        
        # Prevent multiple rapid hotkey activations
        self.last_hotkey_time = 0
        self.hotkey_lock = threading.Lock()
        
        # Set up transcription callback
        self.websocket_client.set_transcription_callback(self.text_inserter.insert_text)
        
        # Detect system type for information only
        self.session_type = os.environ.get('XDG_SESSION_TYPE', 'unknown')
        
    def start(self):
        """Start the speech recognition application"""
        logger.info("Starting Global Speech Recognition")
        logger.info(f"Session type: {self.session_type}")
        logger.info(f"Hotkey: {self._format_hotkey()}")
        
        # Start global hotkey detection
        logger.info("Starting global hotkey detection...")
        self._start_hotkey_mode()
            
    def _start_hotkey_mode(self):
        """Start with global hotkey detection"""
        # Start the asyncio event loop in a separate thread
        self.loop_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait a moment for the event loop to start
        time.sleep(0.1)
        
        # Start global hotkey listener
        try:
            with Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
                suppress=False  # Don't suppress keys, we want global detection
            ) as listener:
                logger.info("Global hotkey detection active - Press Ctrl+Alt+R to start/stop recording")
                print("Press Ctrl+Alt+R to start/stop recording...")
                listener.join()
        except Exception as e:
            logger.error(f"Failed to start keyboard listener: {e}")
            raise
        finally:
            logger.info("Shutting down...")
            self.cleanup()
                
    def _run_async_loop(self):
        """Run the asyncio event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def _on_key_press(self, key):
        """Handle key press events"""
        self.hotkey_pressed.add(key)
        
        # Check if hotkey combination is pressed
        if self.hotkey_pressed >= self.config.hotkey:
            current_time = time.time()
            with self.hotkey_lock:
                # Prevent rapid multiple activations
                if current_time - self.last_hotkey_time < self.config.hotkey_cooldown:
                    return
                    
                self.last_hotkey_time = current_time
                
                # Schedule the async operation safely
                if self.loop and not self.loop.is_closed():
                    asyncio.run_coroutine_threadsafe(self._toggle_recording(), self.loop)
            
    def _on_key_release(self, key):
        """Handle key release events"""
        self.hotkey_pressed.discard(key)
        
    async def _toggle_recording(self):
        """Toggle recording on/off"""
        # Prevent multiple simultaneous operations
        if hasattr(self, '_toggling') and self._toggling:
            return
            
        self._toggling = True
        try:
            if self.is_recording:
                await self._stop_recording()
            else:
                await self._start_recording()
        finally:
            self._toggling = False
            
    async def _start_recording(self):
        """Start recording and transcription"""
        if self.is_recording:
            return
            
        logger.info("Starting speech recognition...")
        
        # Start a new typing session
        self.text_inserter.start_typing_session()
        
        try:
            # Connect to WebSocket server
            await self.websocket_client.connect()
            if not self.websocket_client.is_connected:
                logger.error("Failed to connect to server")
                return
                
            # Start audio recording
            self.recorder.start_recording()
            self.is_recording = True
            
            # Start audio streaming and message listening tasks
            self.audio_task = asyncio.create_task(self._stream_audio())
            self.listen_task = asyncio.create_task(self.websocket_client.listen_for_messages())
            
            logger.info("Recording started - speak now!")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            await self._stop_recording()
            
    async def _stop_recording(self):
        """Stop recording and transcription"""
        if not self.is_recording:
            return
            
        logger.info("Stopping speech recognition...")
        self.is_recording = False
        
        # Stop audio recording first
        self.recorder.stop_recording()
        
        # Send stop signal to server
        await self.websocket_client.send_stop_signal()
        
        # Cancel audio streaming task since we're no longer recording
        if self.audio_task:
            self.audio_task.cancel()
            self.audio_task = None
        
        # Keep the WebSocket connection open and continue listening for any remaining transcriptions
        logger.info("Waiting for server to finish processing remaining audio...")
        
        # Wait for up to specified time for the server to process remaining audio
        wait_start_time = time.time()
        
        while time.time() - wait_start_time < self.config.max_wait_time:
            # Check if we received any new transcription updates
            await asyncio.sleep(0.1)
            
            # If we get a "ready_to_stop" message, we can exit early
            if not self.text_inserter.is_typing_session_active:
                logger.info("Received final transcription, stopping early")
                break
        
        # Cancel the listening task
        if self.listen_task:
            self.listen_task.cancel()
            self.listen_task = None
        
        # End the typing session if it hasn't been ended already
        self.text_inserter.end_typing_session()
        
        # Disconnect from server
        await self.websocket_client.disconnect()
        
        logger.info("Recording stopped")
        
    async def _stream_audio(self):
        """Stream audio data to the server"""
        accumulated_audio = b''
        last_send_time = time.time()
        wav_header_sent = False
        
        while self.is_recording:
            audio_data = self.recorder.get_audio_chunk()
            if audio_data:
                # Accumulate audio data
                accumulated_audio += audio_data
                
                # Check if it's time to send (every 1 second)
                current_time = time.time()
                if current_time - last_send_time >= 1.0:
                    if accumulated_audio:
                        if not wav_header_sent:
                            # Send WAV header only once at the beginning
                            sample_width = self.recorder.audio.get_sample_size(self.config.audio_format)
                            wav_header = self.websocket_client.create_wav_header(
                                self.config.rate, self.config.channels, sample_width
                            )
                            await self.websocket_client.send_audio(wav_header)
                            wav_header_sent = True
                            
                        # Send just the raw PCM audio data
                        await self.websocket_client.send_audio(accumulated_audio)
                        
                        # Reset for next chunk
                        accumulated_audio = b''
                        last_send_time = current_time
            else:
                await asyncio.sleep(0.01)  # Small delay if no audio available
        
        # Send any remaining audio as raw PCM
        if accumulated_audio:
            await self.websocket_client.send_audio(accumulated_audio)
        
    def _format_hotkey(self) -> str:
        """Format hotkey for display"""
        key_names = []
        for key in self.config.hotkey:
            if hasattr(key, 'name'):
                key_names.append(key.name.replace('_l', '').replace('_r', '').title())
            else:
                key_names.append(str(key).replace("'", ""))
        return '+'.join(key_names)
        
    def cleanup(self):
        """Clean up resources"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._stop_recording(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.recorder.cleanup()
