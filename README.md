# whispaholics

A Python application that provides system-wide speech recognition with global hotkey control. The transcribed text is automatically typed at the current cursor position, making it work in any application.
Uses the server of this project: https://github.com/QuentinFuxa/WhisperLiveKit

## Features

- **Global hotkey**: Toggle recording with `Ctrl+Alt+R` (customizable)
- **Universal text insertion**: Works in any application where you can type
- **Real-time transcription**: Uses WhisperLiveKit for accurate speech recognition
- **Modular design**: Clean, maintainable code structure
- **Configurable**: Easy to customize hotkeys and settings

## Prerequisites
WhisperLiveKit
- Python 3.7+
- [WhisperLiveKit server](https://github.com/QuentinFuxa/WhisperLiveKit)
- Microphone access
- X11 session (Linux)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd whispaholics
   ```

2. **Install system dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt-get install portaudio19-dev python3-dev
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration**:
   ```bash
   # Copy the example configuration file
   cp config.example.py config.py
   
   # Edit config.py to match your setup
   nano config.py  # or use your preferred editor
   ```
   
   **Important**: The `config.py` file is git-ignored for security and personalization. You must create it from the example file and configure it for your environment.

## Usage

1. **Start WhisperLiveKit server** (configure the server URL in `config.py`):
   ```bash
   # Example - adjust based on your WhisperLiveKit setup
   python -m whisperlivekit.basic_server
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **Use the hotkey**:
   - Position your cursor where you want text to appear
   - Press `Ctrl+Alt+R` to start recording
   - Speak clearly into your microphone
   - Press `Ctrl+Alt+R` again to stop recording
   - Transcribed text will be automatically typed

## Configuration

**Setup**: Copy `config.example.py` to `config.py` and customize your settings:

```bash
cp config.example.py config.py
```

Then edit `config.py` to customize settings:

### Server Configuration
```python
websocket_url: str = "ws://your-server:port/asr"
```

### Hotkey Configuration
```python
# Default: Ctrl+Alt+R
hotkey: frozenset = frozenset({Key.ctrl_l, Key.alt_l, keyboard.KeyCode.from_char('r')})

# Alternative examples:
# F12 key only
hotkey: frozenset = frozenset({Key.f12})

# Ctrl+Shift+S
hotkey: frozenset = frozenset({Key.ctrl_l, Key.shift, keyboard.KeyCode.from_char('s')})
```

### Audio Settings
```python
rate: int = 16000                    # Sample rate
channels: int = 1                    # Mono audio  
chunk_duration_ms: float = 256.0     # Audio chunk duration in milliseconds
# chunk_size is calculated automatically: int(rate * chunk_duration_ms / 1000)
```

### Timing Settings
```python
hotkey_cooldown: float = 0.5    # Seconds between hotkey activations
max_wait_time: float = 10.0     # Seconds to wait for server processing
typing_delay: float = 0.015     # Seconds between characters when typing
```

## Project Structure

```
whispaholics/
├── main.py                    # Entry point
├── config.example.py          # Example configuration (copy to config.py)
├── config.py                  # Your configuration settings (git-ignored)
├── speech_recognition_app.py  # Main application logic
├── audio_recorder.py          # Audio recording functionality
├── websocket_client.py        # WebSocket communication
├── text_inserter.py          # Text insertion logic
├── setup.sh                  # Installation script
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

**Note**: `config.py` is git-ignored to keep your personal settings private. Always use `config.example.py` as your starting point.

## Troubleshooting

### Configuration Issues
- **"No module named 'config'"**: You need to create `config.py` from the example:
  ```bash
  cp config.example.py config.py
  ```
- **Connection issues**: Check the `websocket_url` in your `config.py`
- **Import errors**: Make sure you've installed all dependencies with `pip install -r requirements.txt`

### Connection Issues
- Ensure WhisperLiveKit server is running and accessible
- Check the `websocket_url` in `config.py`
- Verify no firewall is blocking the connection

### Audio Issues
- Grant microphone permissions to your terminal/Python
- Check if another application is using the microphone
- Verify your microphone is working with other applications

### PyAudio Installation Issues

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-dev
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Audio Device Permissions (Linux):**
```bash
sudo usermod -a -G audio $USER
# Log out and log back in
```

### Hotkey Not Working
- Ensure you're running on an X11 session (not Wayland)
- Check if other applications are capturing the same hotkey
- Try running with elevated permissions if necessary

## System Requirements

- **Linux**: Tested on Ubuntu 20.04+ with X11
- **macOS**: Should work with Homebrew-installed dependencies
- **Windows**: Not currently supported

## How It Works

1. **Hotkey Detection**: Uses `pynput` to detect global hotkey presses
2. **Audio Recording**: Uses `pyaudio` to capture microphone input in real-time
3. **WebSocket Communication**: Sends audio data to WhisperLiveKit server via WebSocket
4. **Speech Recognition**: WhisperLiveKit processes audio and returns transcription
5. **Text Insertion**: Uses `pynput` to simulate keyboard typing at cursor position

## Privacy

- Audio is only recorded when you actively press the hotkey
- Audio data is sent to your configured WhisperLiveKit server
- No data is sent to external services by default
- You have full control over where your audio is processed

## License

This project is provided as-is for use with WhisperLiveKit.
