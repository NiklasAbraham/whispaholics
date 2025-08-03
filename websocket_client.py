"""WebSocket client for communication with WhisperLiveKit server."""

import asyncio
import json
import logging
import websockets
import io
from typing import Optional, Callable
from config import Config

logger = logging.getLogger(__name__)


class WebSocketClient:
    """Handles WebSocket communication with the speech recognition server"""
    
    def __init__(self, config: Config):
        self.config = config
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.transcription_callback: Optional[Callable] = None
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.config.websocket_url), 
                timeout=10.0
            )
            self.is_connected = True
            logger.info(f"Connected to WebSocket server at {self.config.websocket_url}")
        except asyncio.TimeoutError:
            logger.error("Connection to WebSocket server timed out")
            self.is_connected = False
            raise
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            self.is_connected = False
            raise
            
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.is_connected = False
        logger.info("Disconnected from WebSocket server")
        
    async def send_audio(self, audio_data: bytes):
        """Send audio data to the server"""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.send(audio_data)
            except Exception as e:
                logger.error(f"Failed to send audio data: {e}")
                self.is_connected = False
                raise
                
    async def send_stop_signal(self):
        """Send empty audio buffer as stop signal"""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.send(b"")
            except Exception as e:
                logger.error(f"Failed to send stop signal: {e}")
                
    async def listen_for_messages(self):
        """Listen for messages from the server"""
        if not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
            self.is_connected = False
            
    async def _handle_message(self, data: dict):
        """Handle incoming messages from the server"""
        message_type = data.get("type", "")
        
        if message_type == "ready_to_stop":
            logger.info("Received ready_to_stop signal")
            if self.transcription_callback:
                # Extract final transcription
                final_text = self._extract_transcription(data)
                if final_text.strip():
                    self.transcription_callback(final_text)
                    # End the typing session
                    if hasattr(self.transcription_callback, '__self__'):
                        if hasattr(self.transcription_callback.__self__, 'end_typing_session'):
                            self.transcription_callback.__self__.end_typing_session()
        else:
            # Handle regular transcription updates
            if self.transcription_callback:
                transcription = self._extract_transcription(data)
                if transcription.strip():
                    self.transcription_callback(transcription)
                
    def _extract_transcription(self, data: dict) -> str:
        """Extract transcription text from server response"""
        lines = data.get("lines", [])
        
        # Only extract stable text from lines (this is finalized and never changes)
        stable_text_parts = []
        for line in lines:
            if line.get("text"):
                stable_text_parts.append(line["text"].strip())
        
        # Join stable parts
        result = " ".join(stable_text_parts).strip() if stable_text_parts else ""
        
        # Normalize multiple spaces to single spaces
        while "  " in result:
            result = result.replace("  ", " ")
            
        return result
        
    def set_transcription_callback(self, callback: Callable[[str], None]):
        """Set callback for transcription results"""
        self.transcription_callback = callback
        
    def create_wav_header(self, sample_rate: int, channels: int, sample_width: int) -> bytes:
        """Create a WAV header for continuous streaming"""
        output = io.BytesIO()
        
        # Calculate values
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        # Write WAV header manually for streaming
        output.write(b'RIFF')
        output.write((0xFFFFFFFF).to_bytes(4, 'little'))  # File size (unknown for streaming)
        output.write(b'WAVE')
        
        # Format chunk
        output.write(b'fmt ')
        output.write((16).to_bytes(4, 'little'))  # Chunk size
        output.write((1).to_bytes(2, 'little'))   # PCM format
        output.write(channels.to_bytes(2, 'little'))
        output.write(sample_rate.to_bytes(4, 'little'))
        output.write(byte_rate.to_bytes(4, 'little'))
        output.write(block_align.to_bytes(2, 'little'))
        output.write((sample_width * 8).to_bytes(2, 'little'))  # Bits per sample
        
        # Data chunk header
        output.write(b'data')
        output.write((0xFFFFFFFF).to_bytes(4, 'little'))  # Data size (unknown for streaming)
        
        return output.getvalue()
