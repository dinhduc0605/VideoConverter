#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import time
import cv2  # Import OpenCV for video property detection
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QListWidget, QFileDialog, QProgressBar, 
                            QFrame, QSplitter, QGroupBox, QGridLayout, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QSize, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QIcon, QFont

class VideoConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("MTS to MP4 Video Converter - Portrait Mode")
        self.setMinimumSize(900, 600)
        
        # Initialize variables
        self.video_files = []
        self.video_properties = {}  # Dictionary to store properties for each video file
        self.current_preview_file = None
        self.preview_running = False
        self.output_directory = os.path.expanduser("~/Desktop/VideoConverter")
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (file selection and conversion)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        splitter.addWidget(left_panel)
        
        # Right panel (video preview)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)
        
        # Set initial sizes
        splitter.setSizes([300, 600])
        
        # File selection section
        file_group = QGroupBox("Video Files")
        file_layout = QVBoxLayout(file_group)
        
        # File selection buttons
        file_buttons_layout = QHBoxLayout()
        self.select_btn = QPushButton("Select Videos")
        self.select_btn.clicked.connect(self.select_videos)
        file_buttons_layout.addWidget(self.select_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_videos)
        file_buttons_layout.addWidget(self.clear_btn)
        
        file_layout.addLayout(file_buttons_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.currentRowChanged.connect(self.on_file_select)
        file_layout.addWidget(self.file_list)
        
        # Video properties section
        props_group = QGroupBox("Video Properties")
        props_layout = QGridLayout(props_group)
        
        # File size
        props_layout.addWidget(QLabel("File Size:"), 0, 0)
        self.file_size_label = QLabel("-")
        props_layout.addWidget(self.file_size_label, 0, 1)
        
        # Resolution
        props_layout.addWidget(QLabel("Resolution:"), 1, 0)
        self.resolution_label = QLabel("-")
        props_layout.addWidget(self.resolution_label, 1, 1)
        
        # FPS
        props_layout.addWidget(QLabel("FPS:"), 2, 0)
        self.fps_label = QLabel("-")
        props_layout.addWidget(self.fps_label, 2, 1)
        
        # Duration
        props_layout.addWidget(QLabel("Duration:"), 3, 0)
        self.duration_label = QLabel("-")
        props_layout.addWidget(self.duration_label, 3, 1)
        
        # Add video properties to file layout
        file_layout.addWidget(props_group)
        
        # Conversion section
        convert_group = QGroupBox("Conversion")
        convert_layout = QVBoxLayout(convert_group)
        
        # Output directory
        dir_layout = QVBoxLayout()
        dir_layout.addWidget(QLabel("Output Directory:"))
        
        dir_input_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit(self.output_directory)
        dir_input_layout.addWidget(self.output_dir_input)
        
        self.browse_btn = QPushButton("Select Output Directory")
        self.browse_btn.clicked.connect(self.select_output_dir)
        dir_input_layout.addWidget(self.browse_btn)
        
        dir_layout.addLayout(dir_input_layout)
        convert_layout.addLayout(dir_layout)
        
        # Convert button
        self.convert_btn = QPushButton("Convert Selected Videos")
        self.convert_btn.clicked.connect(self.convert_videos)
        convert_layout.addWidget(self.convert_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        convert_layout.addWidget(self.progress_bar)
        
        # Conversion options
        options_layout = QVBoxLayout()
        
        # Rotation checkbox
        self.rotate_checkbox = QCheckBox("Rotate video 90° counterclockwise")
        self.rotate_checkbox.setChecked(False)  # Default to checked
        options_layout.addWidget(self.rotate_checkbox)
        
        convert_layout.addLayout(options_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        convert_layout.addWidget(self.status_label)
        
        # Add all sections to left panel
        left_layout.addWidget(file_group)
        left_layout.addWidget(convert_group)
        
        # Video preview section
        preview_group = QGroupBox("Video Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Video player
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(300)
        preview_layout.addWidget(self.video_widget)
        
        # Media player (PyQt6 has separate audio output)
        # Create with larger buffer size to reduce crackling
        self.media_player = QMediaPlayer()
        
        # Configure audio output with optimized settings
        self.audio_output = QAudioOutput()
        # Set a moderate volume to reduce potential distortion
        self.audio_output.setVolume(0.7)
        
        # Connect components
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.toggle_preview)
        controls_layout.addWidget(self.preview_btn)
        
        # Add spacer to push controls to the left
        controls_layout.addStretch()
        
        preview_layout.addLayout(controls_layout)
        
        # Add preview section to right panel
        right_layout.addWidget(preview_group)
        
        # Set the status bar
        self.statusBar().showMessage("Ready")
    
    def select_videos(self):
        """Open file dialog to select MTS video files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MTS Videos", "",
            "MTS Files (*.MTS);;All Files (*.*)"
        )
        
        if files:
            # Add new files to the list (avoid duplicates)
            for file in files:
                if file not in self.video_files:
                    self.video_files.append(file)
                    filename = os.path.basename(file)
                    self.file_list.addItem(filename)
            
            # Select the first file if none is selected
            if not self.current_preview_file and self.video_files:
                self.file_list.setCurrentRow(0)
    
    def clear_videos(self):
        """Clear all selected videos"""
        self.video_files = []
        self.file_list.clear()
        self.current_preview_file = None
        self.stop_preview()
        self.update_video_properties(None)
    
    def on_file_select(self, row):
        """Handle file selection from the list"""
        if row >= 0 and row < len(self.video_files):
            self.current_preview_file = self.video_files[row]
            self.stop_preview()
            self.update_video_properties(self.current_preview_file)
        else:
            self.current_preview_file = None
            self.update_video_properties(None)
    
    def update_video_properties(self, video_path):
        """Update the video properties display with information about the selected video"""
        if video_path is None:
            self.file_size_label.setText("-")
            self.resolution_label.setText("-")
            self.fps_label.setText("-")
            self.duration_label.setText("-")
            return
        
        try:
            # Get file size
            file_size = os.path.getsize(video_path)
            if file_size < 1024 * 1024:  # Less than 1MB
                size_str = f"{file_size / 1024:.1f} KB"
            else:  # MB or larger
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            self.file_size_label.setText(size_str)
            
            # Use ffprobe to get video properties
            # Get duration
            duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            try:
                duration = float(subprocess.check_output(duration_cmd, universal_newlines=True).strip())
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.duration_label.setText(f"{minutes}m {seconds}s")
            except:
                self.duration_label.setText("Unknown")
            
            # Get resolution and FPS using OpenCV (which worked well in the Tkinter version)
            try:
                # Open the video file with OpenCV
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    # Get resolution
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    if width > 0 and height > 0:
                        self.resolution_label.setText(f"{width}x{height}")
                    else:
                        self.resolution_label.setText("Unknown")
                    
                    # Get FPS
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if fps > 0:
                        self.fps_label.setText(f"{fps:.2f}")
                        # Store FPS in video properties dictionary
                        if video_path not in self.video_properties:
                            self.video_properties[video_path] = {}
                        self.video_properties[video_path]['fps'] = fps
                    else:
                        self.fps_label.setText("Unknown")
                    
                    # Release the video capture
                    cap.release()
                else:
                    # If OpenCV can't open the file, fall back to ffprobe
                    self._get_video_properties_with_ffprobe(video_path)
            except Exception as e:
                print(f"Error getting video properties with OpenCV: {str(e)}")
                # Fall back to ffprobe if OpenCV fails
                self._get_video_properties_with_ffprobe(video_path)
                
        except Exception as e:
            # Reset properties on error
            self.file_size_label.setText("Error")
            self.resolution_label.setText("Error")
            self.fps_label.setText("Error")
            self.duration_label.setText("Error")
    
    def _get_video_properties_with_ffprobe(self, video_path):
        """Fallback method to get video properties using ffprobe"""
        # Get resolution
        try:
            resolution_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            output = subprocess.check_output(resolution_cmd, universal_newlines=True).strip()
            lines = output.split('\n')
            if len(lines) >= 2:
                width = int(lines[0])
                height = int(lines[1])
                self.resolution_label.setText(f"{width}x{height}")
            else:
                self.resolution_label.setText("Unknown")
        except Exception as e:
            print(f"Error getting resolution with ffprobe: {str(e)}")
            self.resolution_label.setText("Unknown")
        
        # Get FPS
        try:
            fps_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            fps_output = subprocess.check_output(fps_cmd, universal_newlines=True).strip()
            
            # Parse frame rate (which may be a fraction like "30000/1001")
            if '/' in fps_output:
                num, den = fps_output.split('/')
                fps = float(num) / float(den)
                self.fps_label.setText(f"{fps:.2f}")
                # Store FPS in video properties dictionary
                if video_path not in self.video_properties:
                    self.video_properties[video_path] = {}
                self.video_properties[video_path]['fps'] = fps
            elif fps_output.replace('.', '', 1).isdigit():  # Check if it's a valid number
                fps = float(fps_output)
                self.fps_label.setText(f"{fps:.2f}")
                # Store FPS in video properties dictionary
                if video_path not in self.video_properties:
                    self.video_properties[video_path] = {}
                self.video_properties[video_path]['fps'] = fps
            else:
                self.fps_label.setText("Unknown")
        except Exception as e:
            print(f"Error getting FPS with ffprobe: {str(e)}")
            self.fps_label.setText("Unknown")
    
    def select_output_dir(self):
        """Open dialog to select output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_directory
        )
        if directory:
            self.output_directory = directory
            self.output_dir_input.setText(directory)
    
    def toggle_preview(self):
        """Toggle video preview"""
        if self.preview_running:
            self.stop_preview()
            self.preview_btn.setText("Preview")
        else:
            if self.current_preview_file:
                self.start_preview()
                self.preview_btn.setText("Stop Preview")
    
    def start_preview(self):
        """Start video preview"""
        if self.current_preview_file and not self.preview_running:
            self.preview_running = True
            self.status_label.setText("Preparing preview...")
            
            # For MTS files, create a temporary preview file with optimized audio
            if self.current_preview_file.lower().endswith('.mts'):
                try:
                    # Create a temporary file for the preview
                    import tempfile
                    fd, temp_preview_file = tempfile.mkstemp(suffix='.mp4')
                    os.close(fd)
                    
                    # Convert a small portion with optimized audio settings
                    cmd = [
                        "ffmpeg", "-i", self.current_preview_file,
                        "-t", "30",  # First 30 seconds for preview
                        "-c:v", "libx264", "-preset", "ultrafast",
                        "-c:a", "aac", "-b:a", "192k",  # Higher audio bitrate
                        "-ar", "48000",  # Standard audio sample rate
                        "-y", temp_preview_file
                    ]
                
                    # Run the conversion process
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    
                    # Wait for the process to complete
                    process.communicate()
                    
                    if process.returncode == 0:
                        # Use the temporary file for preview
                        self.temp_preview_file = temp_preview_file
                        preview_file = temp_preview_file
                    else:
                        # If conversion fails, use the original file
                        self.temp_preview_file = None
                        preview_file = self.current_preview_file
                except Exception as e:
                    # If there's an error, fall back to the original file
                    self.temp_preview_file = None
                    preview_file = self.current_preview_file
                    print(f"Preview preparation error: {str(e)}")
            else:
                # For non-MTS files, use the original file
                self.temp_preview_file = None
                preview_file = self.current_preview_file
                
            # Start playing the video
            self.media_player.setSource(QUrl.fromLocalFile(preview_file))
            self.status_label.setText("Ready")
            self.media_player.play()
    
    def stop_preview(self):
        """Stop the video preview"""
        if self.preview_running:
            self.preview_running = False
            self.media_player.stop()
            
            # Clean up temporary preview file if it exists
            if hasattr(self, 'temp_preview_file') and self.temp_preview_file and os.path.exists(self.temp_preview_file):
                try:
                    os.unlink(self.temp_preview_file)
                    self.temp_preview_file = None
                except Exception as e:
                    print(f"Error removing temporary file: {str(e)}")
    
    def convert_videos(self):
        """Convert selected MTS videos to MP4 format"""
        if not self.video_files:
            self.statusBar().showMessage("Please select at least one video to convert.")
            return
        
        # Get rotation setting
        rotate_video = self.rotate_checkbox.isChecked()
        
        output_dir = self.output_dir_input.text()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.statusBar().showMessage(f"Could not create output directory: {str(e)}")
                return
        
        # Stop any preview that might be running
        self.stop_preview()
        
        # Start conversion in a separate thread
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Converting...")
        
        # Create and start the conversion thread
        self.conversion_thread = ConversionThread(self.video_files, output_dir, self.video_properties, rotate_video)
        self.conversion_thread.progress_update.connect(self.update_progress)
        self.conversion_thread.status_update.connect(self.update_status)
        self.conversion_thread.conversion_complete.connect(self.conversion_completed)
        self.conversion_thread.conversion_error.connect(self.conversion_error)
        self.conversion_thread.start()
    
    @pyqtSlot(int)
    def update_progress(self, progress):
        """Update progress bar with current progress"""
        self.progress_bar.setValue(progress)
    
    @pyqtSlot(str)
    def update_status(self, status):
        """Update status label with current status"""
        self.status_label.setText(status)
    
    @pyqtSlot()
    def conversion_completed(self):
        """Handle conversion completion"""
        self.convert_btn.setEnabled(True)
        self.status_label.setText("Conversion completed")
        self.statusBar().showMessage("All videos have been converted successfully.")
    
    @pyqtSlot(str, str)
    def conversion_error(self, filename, error):
        """Handle conversion error"""
        self.statusBar().showMessage(f"Error converting {filename}: {error}")


class ConversionThread(QThread):
    """Thread for handling video conversion"""
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    conversion_complete = pyqtSignal()
    conversion_error = pyqtSignal(str, str)
    
    def __init__(self, video_files, output_dir, video_properties=None, rotate_video=True):
        super().__init__()
        self.video_files = video_files
        self.output_dir = output_dir
        self.video_properties = video_properties or {}
        self.rotate_video = rotate_video
    
    def run(self):
        """Run the conversion process"""
        total_files = len(self.video_files)
        completed = 0
        
        for input_file in self.video_files:
            try:
                # Update status
                filename = os.path.basename(input_file)
                self.status_update.emit(f"Converting {filename}...")
                
                # Create output filename
                output_name = os.path.splitext(filename)[0] + ".mp4"
                output_path = os.path.join(self.output_dir, output_name)
                
                # Get video duration for progress calculation
                probe_cmd = [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", input_file
                ]
                
                try:
                    duration = float(subprocess.check_output(probe_cmd, universal_newlines=True).strip())
                except:
                    duration = 0  # If we can't get duration, we'll use file-based progress
                
                # Run ffmpeg conversion with progress monitoring
                # Check if we have stored FPS for this file
                fps = 0
                if input_file in self.video_properties and 'fps' in self.video_properties[input_file]:
                    fps = self.video_properties[input_file]['fps']
                    self.status_update.emit(f"Using stored FPS: {fps:.2f} for {filename}")
                
                # If no stored FPS, get it using ffprobe
                if fps <= 0:
                    fps_cmd = [
                        "ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1",
                        input_file
                    ]
                    
                    try:
                        fps_output = subprocess.check_output(fps_cmd, universal_newlines=True).strip()
                        # r_frame_rate is returned as a fraction (e.g., "30000/1001")
                        fps_parts = fps_output.split('/')
                        if len(fps_parts) == 2:
                            fps = float(fps_parts[0]) / float(fps_parts[1])
                        else:
                            fps = float(fps_output)
                        self.status_update.emit(f"Detected FPS: {fps:.2f} for {filename}")
                    except:
                        fps = 0  # If we can't get FPS, ffmpeg will use the source FPS by default
                
                # Run ffmpeg conversion with progress monitoring
                cmd = [
                    "ffmpeg", "-i", input_file
                ]
                
                # If rotation is enabled, we need to re-encode the video
                if self.rotate_video:
                    # Use high-quality encoding settings with rotation
                    cmd.extend([
                        "-c:v", "libx264", "-preset", "slow", "-crf", "18",  # Higher quality encoding
                        "-c:a", "aac", "-b:a", "192k",  # Better audio quality
                        # Rotate 90 degrees counterclockwise and change aspect ratio from 16:9 to 9:16
                        "-vf", "transpose=2",
                        "-aspect", "9:16"
                    ])
                else:
                    # If no rotation, use -vcodec copy to preserve original quality
                    # Use -ss 0.04 to skip the first frame (approximately)
                    cmd.extend([
                        "-vcodec", "copy",  # Copy video stream without re-encoding
                        "-c:a", "aac", "-b:a", "192k"  # Convert audio to AAC for compatibility
                    ])
                
                
                # Add FPS parameter if we successfully retrieved it
                if fps > 0:
                    cmd.extend(["-r", str(fps)])
                
                # Add progress and output parameters
                cmd.extend([
                    "-progress", "pipe:1",  # Output progress to stdout
                    "-y", output_path
                ])
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1  # Line buffered
                )
                
                # Monitor the conversion progress
                current_time = 0
                file_progress = 0
                
                while process.poll() is None:
                    output_line = process.stdout.readline().strip()
                    
                    if output_line.startswith("out_time_ms="):
                        try:
                            # Extract time in milliseconds
                            time_ms = int(output_line.split("=")[1])
                            current_time = time_ms / 1000000  # Convert to seconds
                            
                            if duration > 0:
                                # Calculate progress based on video duration
                                file_progress = min(100, (current_time / duration) * 100)
                                
                                # Calculate overall progress
                                overall_progress = int(((completed / total_files) * 100) + (file_progress / total_files))
                                self.progress_update.emit(overall_progress)
                                
                                # Update status with percentage
                                status_text = f"Converting {filename}... {file_progress:.1f}%"
                                self.status_update.emit(status_text)
                        except:
                            pass
                
                # Get the final output
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    self.conversion_error.emit(filename, stderr)
                
                # Update progress
                completed += 1
                progress = int((completed / total_files) * 100)
                self.progress_update.emit(progress)
                
            except Exception as e:
                self.conversion_error.emit(filename, str(e))
        
        # Signal completion
        self.conversion_complete.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont()
    font.setPointSize(12)
    app.setFont(font)
    
    window = VideoConverter()
    window.show()
    
    sys.exit(app.exec())
