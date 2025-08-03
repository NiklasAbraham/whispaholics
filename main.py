#!/usr/bin/env python3
"""
Global Speech Recognition with Hotkey Control

Entry point for the global speech recognition application.
"""

import logging
import sys
from config import Config
from speech_recognition_app import SpeechRecognitionApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    try:
        # Create configuration
        config = Config()
        
        # Create and start the application
        app = SpeechRecognitionApp(config)
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
