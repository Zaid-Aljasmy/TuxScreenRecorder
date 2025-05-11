import sys
import os
import subprocess
import signal
import time
import datetime
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox,
    QHBoxLayout, QCheckBox, QTabWidget, QProgressBar, QGroupBox,
    QLineEdit, QFileDialog, QRadioButton
)
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QGuiApplication, QPixmap, QImage
import numpy as np
import cv2

class ScreenRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tux Screen Recorder")
        self.setGeometry(100, 100, 700, 650) # Increased height to accommodate new elements

        # Default output file path
        self.output_file = os.path.expanduser("~/Videos/TuxScreenRecorder")
        self.recording_region = "full_screen" # Default recording region

        # Initialize preview_frame_rate BEFORE calling setup_info_tab
        self.preview_frame_rate = 10 # Default preview frame rate

        # Create a tab widget with two tabs: Recorder and Information
        self.tabs = QTabWidget()
        self.recorder_tab = QWidget()
        self.info_tab = QWidget()
        self.tabs.addTab(self.recorder_tab, "Recorder")
        self.tabs.addTab(self.info_tab, "Information")

        # Setup UI for both tabs
        self.setup_recorder_tab()
        self.setup_info_tab()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        self.process = None
        self.start_time = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_info)

        # Timer for live preview updates (screen capture)
        self.live_preview_timer = QTimer()
        self.live_preview_timer.timeout.connect(self.update_live_preview)
        self.live_preview_running = False

    def setup_recorder_tab(self):
        layout = QVBoxLayout()

        # Recording region selection
        recording_region_group = QGroupBox("Recording Region")
        recording_region_layout = QVBoxLayout()
        self.full_screen_radio = QRadioButton("Full Screen")
        self.full_screen_radio.setChecked(True)
        self.full_screen_radio.toggled.connect(lambda: self.set_recording_region("full_screen"))
        recording_region_layout.addWidget(self.full_screen_radio)
        self.window_radio = QRadioButton("Select Window (Soon!)")
        self.window_radio.toggled.connect(lambda: self.set_recording_region("window"))
        recording_region_layout.addWidget(self.window_radio)
        recording_region_group.setLayout(recording_region_layout)
        layout.addWidget(recording_region_group)

        # Frame rate selection
        self.label_fps = QLabel("Select Frame Rate (FPS):")
        layout.addWidget(self.label_fps)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60", "30", "24", "Unlimited"])
        layout.addWidget(self.fps_combo)

        # Video container selection with warning
        self.label_container = QLabel("Select Video Container:")
        layout.addWidget(self.label_container)
        self.container_combo = QComboBox()
        self.container_combo.addItems(["mp4", "mkv"])
        layout.addWidget(self.container_combo)
        self.label_container_warning = QLabel(
            "Warning: this format will produce unreadable files if the recording is interrupted!!\nConsider using MKV instead."
        )
        self.label_container_warning.setStyleSheet("color: red;")
        layout.addWidget(self.label_container_warning)

        # Audio recording option
        self.audio_checkbox = QCheckBox("Record Audio")
        self.audio_checkbox.toggled.connect(self.update_audio_controls_state)
        layout.addWidget(self.audio_checkbox)

        # Audio source selection
        self.label_audio_source = QLabel("Select Audio Input Source:")
        layout.addWidget(self.label_audio_source)
        self.audio_source_combo = QComboBox()
        self.audio_source_combo.addItems([
            "Monitor of built-in audio analog stereo",
            "Built-in audio analog stereo"
        ])
        layout.addWidget(self.audio_source_combo)

        # Audio codec selection
        self.label_audio_codec = QLabel("Select Audio Codec:")
        layout.addWidget(self.label_audio_codec)
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["mp3", "aac", "vorbis"])
        layout.addWidget(self.audio_codec_combo)

        # Initialize audio controls state
        self.update_audio_controls_state(self.audio_checkbox.isChecked())

        # Output path selection
        output_path_layout = QHBoxLayout()
        self.output_path_label = QLabel("Output Path:")
        output_path_layout.addWidget(self.output_path_label)
        self.output_path_edit = QLineEdit(self.output_file)
        output_path_layout.addWidget(self.output_path_edit)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_output_path)
        output_path_layout.addWidget(self.browse_button)
        layout.addLayout(output_path_layout)

        # Start/Stop/Cancel buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self.start_recording)
        button_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        self.cancel_button = QPushButton("Cancel Record")
        self.cancel_button.clicked.connect(self.cancel_recording)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.recorder_tab.setLayout(layout)

    def update_audio_controls_state(self, checked):
        """Enable or disable audio controls based on the audio checkbox state"""
        self.audio_source_combo.setEnabled(checked)
        self.audio_codec_combo.setEnabled(checked)

    def set_recording_region(self, region):
        """Sets the recording region based on user selection."""
        self.recording_region = region
        if region == "window":
            print("Window selection not yet implemented.") # Placeholder for future functionality

    def generate_timestamped_filename(self, base_path):
        """Generates a unique filename with timestamp to prevent overwriting existing files."""
        # Get the directory and base filename without extension
        directory = os.path.dirname(base_path)
        filename = os.path.basename(base_path)
        name, ext = os.path.splitext(filename)
        
        # If no extension is provided, use the currently selected container
        if not ext:
            ext = f".{self.container_combo.currentText()}"
        
        # Generate timestamp in format YYYY-MM-DD_HH-MM-SS
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Create new filename with timestamp
        new_filename = f"{name}_{timestamp}{ext}"
        
        # Return the full path with the new filename
        return os.path.join(directory, new_filename)

    def browse_output_path(self):
        """Opens a file dialog for the user to select the output file path."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Select Output File", os.path.expanduser("~/Videos"),
            f"Video Files (*.{self.container_combo.currentText()})"
        )
        if file_path:
            self.output_path_edit.setText(file_path)
            self.output_file = file_path # Update the output_file variable

    def setup_info_tab(self):
        layout = QVBoxLayout()

        # Recording Information Group
        info_group = QGroupBox("Recording Information")
        info_layout = QVBoxLayout()
        self.label_file_name = QLabel(f"File Name: {os.path.basename(self.output_file)}")
        info_layout.addWidget(self.label_file_name)
        self.label_total_time = QLabel("Total Time: 0 s")
        info_layout.addWidget(self.label_total_time)
        self.label_fbs_in = QLabel("FBS In: 0")
        info_layout.addWidget(self.label_fbs_in)
        self.label_fbs_out = QLabel("FBS Out: 0")
        info_layout.addWidget(self.label_fbs_out)
        self.label_file_size = QLabel("File Size: 0 MB")
        info_layout.addWidget(self.label_file_size)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Live Preview Section for Screen Capture
        live_group = QGroupBox("Live Preview")
        live_layout = QVBoxLayout()
        self.live_preview_display = QLabel("Live preview not running")
        self.live_preview_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_preview_display.setMinimumSize(300, 400)
        live_layout.addWidget(self.live_preview_display)
        self.toggle_live_preview_button = QPushButton("Start Live Preview")
        self.toggle_live_preview_button.clicked.connect(self.toggle_live_preview)
        live_layout.addWidget(self.toggle_live_preview_button)

        # Preview Frame Rate Selection
        preview_rate_layout = QHBoxLayout()
        preview_rate_label = QLabel("Preview Frame Rate (FPS):")
        preview_rate_layout.addWidget(preview_rate_label)
        self.preview_fps_combo = QComboBox()
        self.preview_fps_combo.addItems([str(i) for i in range(10, 31)]) # Options from 10 to 30
        preview_rate_layout.addWidget(self.preview_fps_combo)
        live_layout.addLayout(preview_rate_layout)

        # Set the current text and connect the signal AFTER the combo box is added to the layout
        self.preview_fps_combo.setCurrentText(str(self.preview_frame_rate))
        self.preview_fps_combo.currentIndexChanged.connect(self.set_preview_frame_rate)

        self.preview_note_label = QLabel("Note: previewing requires extra CPU time (especially at high frame rates).")
        self.preview_note_label.setStyleSheet("font-size: 14px; color: yellow;")
        live_layout.addWidget(self.preview_note_label)

        live_group.setLayout(live_layout)
        layout.addWidget(live_group)

        # Initialize preview controls state
        self.preview_fps_combo.setEnabled(False)

        self.info_tab.setLayout(layout)

    def set_preview_frame_rate(self, index):
        """Sets the preview frame rate based on user selection."""
        self.preview_frame_rate = int(self.preview_fps_combo.currentText())
        if self.live_preview_running:
            self.live_preview_timer.setInterval(int(1000 / self.preview_frame_rate))

    def start_recording(self):
        """Starts the screen recording process with selected parameters and timestamped filename."""
        resolution = "1920x1080" # Default resolution for full screen recording
        if self.recording_region == "window":
            print("Window recording resolution needs to be determined.") # Future implementation
            return # Prevent recording if window selection isn't implemented

        fps = self.fps_combo.currentText()
        container = self.container_combo.currentText()
        
        # Get base output path from text edit
        base_output_path = self.output_path_edit.text()
        
        # Generate a timestamped filename to prevent overwriting existing files
        self.output_file = self.generate_timestamped_filename(base_output_path)
        
        # Update the UI to show the actual filename being used
        self.label_file_name.setText(f"File Name: {os.path.basename(self.output_file)}")

        # Setup audio input if recording audio
        if self.audio_checkbox.isChecked():
            selected_source = self.audio_source_combo.currentText()
            if selected_source == "Monitor of built-in audio analog stereo":
                audio_device = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
            else:
                audio_device = "alsa_input.pci-0000_00_1b.0.analog-stereo"
            audio_input = f"-f pulse -i {audio_device}"
            selected_codec = self.audio_codec_combo.currentText()
            codec_mapping = {
                "mp3": "libmp3lame",
                "aac": "aac",
                "vorbis": "libvorbis"
            }
            audio_codec = codec_mapping.get(selected_codec, "aac")
            audio_codec_option = f"-c:a {audio_codec}"
        else:
            audio_input = ""
            audio_codec_option = ""

        # Build the ffmpeg command with proper encoding options
        command = (
            f"ffmpeg -y -video_size {resolution} -framerate {fps} "
            f"-f x11grab -i :0.0 {audio_input} "
            f"-c:v libx264 -preset ultrafast -crf 23 {audio_codec_option} \"{self.output_file}\""
        )
        # Start ffmpeg process in its own process group
        self.process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
        self.start_time = time.time()  # Record start time
        self.update_timer.start(1000)  # Update recording information every second
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.cancel_button.setEnabled(True)  # Enable cancel button when recording starts

    def stop_recording(self):
        """Stops the recording and saves the output file."""
        if self.process:
            # Send SIGINT to allow ffmpeg to finish writing the file cleanly
            os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
            self.process.wait()
            self.process = None
        self.update_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.cancel_button.setEnabled(False)  # Disable cancel button when recording stops
        # Here you can add any post-recording actions if needed

    def cancel_recording(self):
        """Cancels the recording without saving the output file."""
        if self.process:
            # Send SIGTERM to terminate the process immediately
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()
            self.process = None
            
            # Remove the output file if it exists
            if os.path.exists(self.output_file):
                try:
                    os.remove(self.output_file)
                    print(f"Recording canceled. File {self.output_file} has been deleted.")
                except OSError as e:
                    print(f"Error deleting file: {e}")
        
        self.update_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        # Reset recording information
        self.label_total_time.setText("Total Time: 0 s")
        self.label_fbs_in.setText("FBS In: 0")
        self.label_fbs_out.setText("FBS Out: 0")
        self.label_file_size.setText("File Size: 0 MB")

    def update_info(self):
        """Updates recording information display in real-time."""
        if self.start_time is None:
            return
        # Update total recording time
        elapsed = int(time.time() - self.start_time)
        self.label_total_time.setText(f"Total Time: {elapsed} s")
        # Simulate frames in/out using FPS and elapsed time
        try:
            fps = int(self.fps_combo.currentText())
        except ValueError:
            fps = 30
        frames = fps * elapsed
        self.label_fbs_in.setText(f"FBS In: {frames}")
        self.label_fbs_out.setText(f"FBS Out: {frames}")
        # Update file size if file exists
        if os.path.exists(self.output_file):
            size = os.path.getsize(self.output_file)
            # Convert bytes to MB for display
            size_mb = size / (1024 * 1024)
            self.label_file_size.setText(f"File Size: {size_mb:.2f} MB")

    def toggle_live_preview(self):
        """Toggles the live preview functionality on and off."""
        if self.live_preview_running:
            self.live_preview_timer.stop()
            self.live_preview_running = False
            self.toggle_live_preview_button.setText("Start Live Preview")
            self.live_preview_display.setText("Live preview stopped")
            # Disable preview frame rate combo box when preview is stopped
            self.preview_fps_combo.setEnabled(False)
        else:
            self.live_preview_timer.start(int(1000 / self.preview_frame_rate))
            self.live_preview_running = True
            self.toggle_live_preview_button.setText("Stop Live Preview")
            # Enable preview frame rate combo box when preview is running
            self.preview_fps_combo.setEnabled(True)

    def update_live_preview(self):
        """Updates the live preview display with current screen capture."""
        # Grab the primary screen and update the live preview display
        screen = QGuiApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0)
            # Scale pixmap to fit the preview area while keeping aspect ratio
            scaled_pixmap = pixmap.scaled(self.live_preview_display.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.live_preview_display.setPixmap(scaled_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenRecorder()
    window.show()
    sys.exit(app.exec())
