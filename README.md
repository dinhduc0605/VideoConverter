# MTS to MP4 Video Converter

A Python application that allows you to convert MTS video files to MP4 format with a modern PyQt6-based GUI interface.

## Features

- Select and convert multiple MTS videos to MP4 format
- Preview videos before conversion with smooth playback
- Display video properties (file size, resolution, FPS, duration)
- Select custom output directory
- Modern and responsive user interface
- Real-time conversion progress tracking

## Requirements

- Python 3.7+
- **FFmpeg** (must be installed on your system - this is essential for the app to work)
- PyQt6 (for the modern GUI interface)
- OpenCV (for video property detection)
- Required Python packages (see requirements.txt)

## Installation

1. **IMPORTANT**: You must install FFmpeg on your system first:
   ```
   brew install ffmpeg
   ```
   If you don't have Homebrew installed, you can get it from https://brew.sh/

2. Set up a Python virtual environment and install the required packages:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python src/app.py
   ```

2. Use the "Select Videos" button to choose MTS video files for conversion
3. Select a video from the list to preview it
4. Click the "Preview" button to view the selected video
5. Choose an output directory for the converted MP4 files
6. Click "Convert Selected Videos" to start the conversion process

## Notes

- The preview feature creates a temporary MP4 file for MTS files to enable smooth preview with optimized audio settings
- The application uses FFmpeg for video conversion with good quality presets
- Real-time progress is shown during conversion with percentage updates
- Video properties are extracted using a combination of OpenCV and FFmpeg for reliability
- The PyQt6-based interface provides a more responsive and modern user experience compared to the previous Tkinter version
