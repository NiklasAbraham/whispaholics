#!/bin/bash

# Setup script for Global Speech Recognition

echo "Setting up Global Speech Recognition..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This setup script is designed for Linux. You may need to install dependencies manually."
fi

# Install system dependencies (Ubuntu/Debian)
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev python3-pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Set up configuration file
echo "Setting up configuration..."
if [ ! -f config.py ]; then
    cp config.example.py config.py
    echo "Created config.py from example. Please edit it to match your setup."
else
    echo "config.py already exists. Skipping configuration setup."
fi

echo "Setup complete!"
echo ""
echo "To use the application:"
echo "1. Edit config.py to configure your WhisperLiveKit server URL"
echo "2. Start your WhisperLiveKit server"
echo "3. Run: python3 main.py"
echo "4. Press Ctrl+Alt+R to start/stop recording"
