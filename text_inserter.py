"""Text insertion functionality for typing transcribed text."""

import time
import logging
from pynput import keyboard

logger = logging.getLogger(__name__)


class TextInserter:
    """Handles typing text at the cursor position"""
    
    def __init__(self, typing_delay: float = 0.015):
        self.controller = keyboard.Controller()
        self.typing_delay = typing_delay
        self.last_typed_text = ""
        self.is_typing_session_active = False
        
    def insert_text(self, text: str):
        """Insert text at the current cursor position"""
        if not text:
            return
            
        # Clean up the text
        cleaned_text = self._clean_text(text)
        
        if not cleaned_text:
            return
        
        # Check if this is new content we haven't typed yet
        if cleaned_text == self.last_typed_text:
            return
            
        # Check if this is additional content (new text contains our previous text)
        if self.last_typed_text and cleaned_text.startswith(self.last_typed_text.rstrip()):
            # This is additional content - type only the new part
            new_part = cleaned_text[len(self.last_typed_text.rstrip()):]
            if new_part.strip():
                self._type_text_slowly(new_part)
                self.last_typed_text = cleaned_text
                logger.info(f"Added text continuation: {new_part}")
        else:
            # This is completely new text or a replacement
            self._type_text_slowly(cleaned_text)
            self.last_typed_text = cleaned_text
            logger.info(f"Inserted new text: {cleaned_text}")
    
    def _type_text_slowly(self, text: str):
        """Type text with a small delay between characters to ensure reliability"""
        for char in text:
            self.controller.type(char)
            time.sleep(self.typing_delay)
        
    def start_typing_session(self):
        """Mark the start of a new typing session"""
        self.last_typed_text = ""
        self.is_typing_session_active = True
        
    def end_typing_session(self):
        """Mark the end of a typing session"""
        self.is_typing_session_active = False
        
    def _clean_text(self, text: str) -> str:
        """Clean and format the text for insertion"""
        # Split into words and rejoin with single spaces
        words = text.split()
        if not words:
            return ""
            
        # Join words with single spaces
        cleaned = " ".join(words)
        
        # Add space at the end if the original text suggests it
        if text.endswith(" ") or any(text.endswith(p + " ") for p in [".", "!", "?", ","]):
            if not cleaned.endswith(" "):
                cleaned += " "
            
        return cleaned
