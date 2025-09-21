import sys
import os
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QComboBox, 
                              QSpinBox, QFileDialog, QMessageBox, QFrame, QSizePolicy,
                              QProgressBar, QSlider, QCheckBox, QTabWidget, QGridLayout,
                              QTextEdit, QGroupBox, QLineEdit, QGraphicsDropShadowEffect,
                              QSystemTrayIcon, QMenu, QAction, QSplashScreen)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QRect, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import (QPixmap, QImage, QPainter, QScreen, QFont, QIcon, 
                          QPalette, QColor, QLinearGradient, QBrush, QPen)
import cv2
import pyautogui
import threading
import time
import json
import psutil


class AdvancedScreenRecorder(QThread):
    update_frame = Signal(np.ndarray)
    recording_finished = Signal()
    progress_update = Signal(int)  # Recording duration in seconds
    fps_update = Signal(float)     # Current FPS
    file_size_update = Signal(int) # File size in bytes
    
    def __init__(self, output_file, screen_region=None, camera_device=0, 
                 camera_position="bottom-right", camera_size=(320, 240), 
                 fps=30, quality=85, record_audio=True, mouse_cursor=True, 
                 parent=None):
        super().__init__(parent)
        self.output_file = output_file
        self.screen_region = screen_region
        self.camera_device = camera_device
        self.camera_position = camera_position
        self.camera_size = camera_size
        self.fps = fps
        self.quality = quality
        self.record_audio = record_audio
        self.mouse_cursor = mouse_cursor
        self.is_recording = False
        self.is_paused = False
        self.frame_count = 0
        self.start_time = None
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        if screen_region:
            self.x, self.y, self.width, self.height = screen_region
        else:
            self.x, self.y = 0, 0
            self.width, self.height = self.screen_width, self.screen_height
        
        # Initialize video writer with better codec
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(output_file, self.fourcc, fps, (self.width, self.height))
        
        # Initialize camera if available
        self.camera_available = False
        if camera_device is not None:
            self.cap = cv2.VideoCapture(camera_device)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_size[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_size[1])
                self.cap.set(cv2.CAP_PROP_FPS, fps)
                self.camera_available = True
            else:
                self.cap = None
        
    def run(self):
        self.is_recording = True
        self.start_time = time.time()
        last_time = time.time()
        fps_counter = 0
        fps_timer = time.time()
        
        while self.is_recording:
            if not self.is_paused:
                current_time = time.time()
                
                # Capture screen with cursor if enabled
                if self.mouse_cursor:
                    screen_img = pyautogui.screenshot(region=(self.x, self.y, self.width, self.height))
                else:
                    # Alternative method without cursor (would need implementation)
                    screen_img = pyautogui.screenshot(region=(self.x, self.y, self.width, self.height))
                
                screen_frame = np.array(screen_img)
                screen_frame = cv2.cvtColor(screen_frame, cv2.COLOR_RGB2BGR)
                
                # Add camera overlay if available
                if self.camera_available and self.cap:
                    ret, camera_frame = self.cap.read()
                    if ret:
                        # Flip camera horizontally for mirror effect
                        camera_frame = cv2.flip(camera_frame, 1)
                        camera_frame = cv2.resize(camera_frame, self.camera_size)
                        
                        # Add rounded corners and border to camera
                        camera_frame = self.add_camera_effects(camera_frame)
                        
                        # Determine camera position
                        x_pos, y_pos = self.get_camera_position()
                        
                        # Blend camera frame with screen
                        self.blend_camera_frame(screen_frame, camera_frame, x_pos, y_pos)
                
                # Write frame to output file
                self.out.write(screen_frame)
                self.frame_count += 1
                
                # Emit frame for preview
                preview_frame = cv2.cvtColor(screen_frame, cv2.COLOR_BGR2RGB)
                self.update_frame.emit(preview_frame)
                
                # Update progress
                duration = int(current_time - self.start_time)
                self.progress_update.emit(duration)
                
                # Calculate and emit FPS
                fps_counter += 1
                if current_time - fps_timer >= 1.0:
                    actual_fps = fps_counter / (current_time - fps_timer)
                    self.fps_update.emit(actual_fps)
                    fps_counter = 0
                    fps_timer = current_time
                
                # Emit file size (approximate)
                if os.path.exists(self.output_file):
                    file_size = os.path.getsize(self.output_file)
                    self.file_size_update.emit(file_size)
            
            # Control frame rate
            elapsed = time.time() - last_time
            sleep_time = max(0, 1.0/self.fps - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()
        
        # Clean up
        if self.camera_available and self.cap:
            self.cap.release()
        self.out.release()
        self.recording_finished.emit()
    
    def add_camera_effects(self, frame):
        """Add visual effects to camera frame"""
        # Add a subtle border
        cv2.rectangle(frame, (0, 0), (frame.shape[1]-1, frame.shape[0]-1), (255, 255, 255), 2)
        return frame
    
    def get_camera_position(self):
        """Calculate camera position based on settings"""
        margin = 20
        if self.camera_position == "top-left":
            return margin, margin
        elif self.camera_position == "top-right":
            return self.width - self.camera_size[0] - margin, margin
        elif self.camera_position == "bottom-left":
            return margin, self.height - self.camera_size[1] - margin
        else:  # bottom-right
            return self.width - self.camera_size[0] - margin, self.height - self.camera_size[1] - margin
    
    def blend_camera_frame(self, screen_frame, camera_frame, x_pos, y_pos):
        """Blend camera frame with screen frame"""
        y_end = min(y_pos + self.camera_size[1], self.height)
        x_end = min(x_pos + self.camera_size[0], self.width)
        
        if y_pos >= 0 and x_pos >= 0:
            screen_frame[y_pos:y_end, x_pos:x_end] = camera_frame[:y_end-y_pos, :x_end-x_pos]
    
    def pause_recording(self):
        self.is_paused = True
    
    def resume_recording(self):
        self.is_paused = False
    
    def stop_recording(self):
        self.is_recording = False


class ModernPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 450)
        self.frame = np.zeros((450, 800, 3), dtype=np.uint8)
        self.setStyleSheet("""
            ModernPreviewWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2C3E50, stop: 1 #34495E);
                border: 2px solid #3498DB;
                border-radius: 10px;
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
    def update_frame(self, frame):
        self.frame = frame
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.frame is not None and self.frame.size > 0:
            h, w, c = self.frame.shape
            q_img = QImage(self.frame.data, w, h, w * c, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Scale pixmap to fit widget while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Center the pixmap
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Draw placeholder
            painter.fillRect(self.rect(), QColor(44, 62, 80))
            painter.setPen(QColor(255, 255, 255, 100))
            painter.setFont(QFont("Segoe UI", 24, QFont.Light))
            painter.drawText(self.rect(), Qt.AlignCenter, "EEM Studio Pro\nPreview Area")


class ModernButton(QPushButton):
    def __init__(self, text, color="#3498DB", parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setStyleSheet(f"""
            ModernButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {color}, stop: 1 {self.darken_color(color)});
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                min-width: 120px;
            }}
            ModernButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {self.lighten_color(color)}, stop: 1 {color});
            }}
            ModernButton:pressed {{
                background: {self.darken_color(color)};
            }}
            ModernButton:disabled {{
                background: #7F8C8D;
            }}
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
    
    def darken_color(self, color):
        """Darken a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, c - 30) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def lighten_color(self, color):
        """Lighten a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        lightened = tuple(min(255, c + 30) for c in rgb)
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"


class EEMStudioPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEM Studio Pro - Professional Screen Recording by Elijah Ekpen Mensah")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Initialize variables
        self.recorder = None
        self.is_recording = False
        self.is_paused = False
        self.output_file = ""
        self.selected_region = None
        self.recording_duration = 0
        
        # Load settings
        self.settings = self.load_settings()
        
        # Setup UI
        self.init_ui()
        self.setup_system_tray()
        self.apply_theme()
        
        # Setup status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(1000)  # Update every second
        
    def init_ui(self):
        # Central widget with modern styling
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2C3E50, stop: 1 #34495E);
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with branding
        self.create_header(main_layout)
        
        # Main content area with tabs
        self.create_tabs(main_layout)
        
        # Control buttons
        self.create_control_buttons(main_layout)
        
        # Status bar
        self.create_status_bar(main_layout)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def create_header(self, parent_layout):
        """Create the branded header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #E74C3C, stop: 0.5 #8E44AD, stop: 1 #3498DB);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        header_layout = QHBoxLayout()
        
        # Brand logo/title
        brand_label = QLabel("EEM Studio Pro")
        brand_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                background: transparent;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
        """)
        
        # Subtitle
        subtitle_label = QLabel("Professional Screen Recording Suite\nBy Elijah Ekpen Mensah")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 14px;
                background: transparent;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            }
        """)
        
        header_layout.addWidget(brand_label)
        header_layout.addStretch()
        header_layout.addWidget(subtitle_label)
        
        header_frame.setLayout(header_layout)
        parent_layout.addWidget(header_frame)
    
    def create_tabs(self, parent_layout):
        """Create tabbed interface"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #34495E;
                border-radius: 10px;
                background: rgba(44, 62, 80, 100);
            }
            QTabBar::tab {
                background: #34495E;
                color: white;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #3498DB;
            }
            QTabBar::tab:hover {
                background: #4A6741;
            }
        """)
        
        # Recording Tab
        recording_tab = QWidget()
        self.setup_recording_tab(recording_tab)
        self.tab_widget.addTab(recording_tab, "📹 Recording")
        
        # Settings Tab
        settings_tab = QWidget()
        self.setup_settings_tab(settings_tab)
        self.tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        # Analytics Tab
        analytics_tab = QWidget()
        self.setup_analytics_tab(analytics_tab)
        self.tab_widget.addTab(analytics_tab, "📊 Analytics")
        
        parent_layout.addWidget(self.tab_widget)
    
    def setup_recording_tab(self, tab):
        """Setup the main recording interface"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Preview area
        preview_group = QGroupBox("Live Preview")
        preview_group.setStyleSheet(self.get_group_style())
        preview_layout = QVBoxLayout()
        
        self.preview_widget = ModernPreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        preview_group.setLayout(preview_layout)
        
        layout.addWidget(preview_group, stretch=2)
        
        # Recording controls in a grid
        controls_group = QGroupBox("Recording Controls")
        controls_group.setStyleSheet(self.get_group_style())
        controls_layout = QGridLayout()
        
        # Output file selection
        output_label = QLabel("Output File:")
        output_label.setStyleSheet("font-weight: bold;")
        self.output_line = QLineEdit()
        self.output_line.setStyleSheet(self.get_input_style())
        self.output_line.setPlaceholderText("Select output file location...")
        browse_btn = ModernButton("Browse", "#E67E22")
        browse_btn.clicked.connect(self.select_output_file)
        
        controls_layout.addWidget(output_label, 0, 0)
        controls_layout.addWidget(self.output_line, 0, 1)
        controls_layout.addWidget(browse_btn, 0, 2)
        
        # Region selection
        region_label = QLabel("Capture Region:")
        region_label.setStyleSheet("font-weight: bold;")
        self.region_line = QLineEdit()
        self.region_line.setStyleSheet(self.get_input_style())
        self.region_line.setPlaceholderText("Full screen")
        self.region_line.setReadOnly(True)
        region_btn = ModernButton("Select", "#9B59B6")
        region_btn.clicked.connect(self.select_region)
        
        controls_layout.addWidget(region_label, 1, 0)
        controls_layout.addWidget(self.region_line, 1, 1)
        controls_layout.addWidget(region_btn, 1, 2)
        
        # Quick settings
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("font-weight: bold;")
        self.fps_combo = QComboBox()
        self.fps_combo.setStyleSheet(self.get_input_style())
        self.fps_combo.addItems(["24", "30", "60"])
        self.fps_combo.setCurrentText("30")
        
        quality_label = QLabel("Quality:")
        quality_label.setStyleSheet("font-weight: bold;")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(50, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setStyleSheet(self.get_slider_style())
        self.quality_value_label = QLabel("85%")
        self.quality_slider.valueChanged.connect(lambda v: self.quality_value_label.setText(f"{v}%"))
        
        controls_layout.addWidget(fps_label, 2, 0)
        controls_layout.addWidget(self.fps_combo, 2, 1)
        controls_layout.addWidget(quality_label, 3, 0)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value_label)
        controls_layout.addLayout(quality_layout, 3, 1, 1, 2)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        tab.setLayout(layout)
    
    def setup_settings_tab(self, tab):
        """Setup the settings interface"""
        layout = QVBoxLayout()
        
        # Camera Settings
        camera_group = QGroupBox("Camera Settings")
        camera_group.setStyleSheet(self.get_group_style())
        camera_layout = QGridLayout()
        
        # Camera device
        device_label = QLabel("Camera Device:")
        device_label.setStyleSheet("font-weight: bold;")
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet(self.get_input_style())
        self.detect_cameras()
        
        # Camera position
        position_label = QLabel("Camera Position:")
        position_label.setStyleSheet("font-weight: bold;")
        self.position_combo = QComboBox()
        self.position_combo.setStyleSheet(self.get_input_style())
        self.position_combo.addItems(["top-left", "top-right", "bottom-left", "bottom-right"])
        self.position_combo.setCurrentText("bottom-right")
        
        # Camera size
        size_label = QLabel("Camera Size:")
        size_label.setStyleSheet("font-weight: bold;")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(160, 640)
        self.width_spin.setValue(320)
        self.width_spin.setSuffix(" px")
        self.width_spin.setStyleSheet(self.get_input_style())
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(120, 480)
        self.height_spin.setValue(240)
        self.height_spin.setSuffix(" px")
        self.height_spin.setStyleSheet(self.get_input_style())
        
        camera_layout.addWidget(device_label, 0, 0)
        camera_layout.addWidget(self.device_combo, 0, 1)
        camera_layout.addWidget(position_label, 1, 0)
        camera_layout.addWidget(self.position_combo, 1, 1)
        camera_layout.addWidget(size_label, 2, 0)
        size_layout = QHBoxLayout()
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("×"))
        size_layout.addWidget(self.height_spin)
        camera_layout.addLayout(size_layout, 2, 1)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Advanced Settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setStyleSheet(self.get_group_style())
        advanced_layout = QVBoxLayout()
        
        self.record_audio_check = QCheckBox("Record System Audio")
        self.record_audio_check.setChecked(True)
        self.record_audio_check.setStyleSheet("font-size: 14px;")
        
        self.mouse_cursor_check = QCheckBox("Show Mouse Cursor")
        self.mouse_cursor_check.setChecked(True)
        self.mouse_cursor_check.setStyleSheet("font-size: 14px;")
        
        self.minimize_tray_check = QCheckBox("Minimize to System Tray")
        self.minimize_tray_check.setChecked(True)
        self.minimize_tray_check.setStyleSheet("font-size: 14px;")
        
        advanced_layout.addWidget(self.record_audio_check)
        advanced_layout.addWidget(self.mouse_cursor_check)
        advanced_layout.addWidget(self.minimize_tray_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        tab.setLayout(layout)
    
    def setup_analytics_tab(self, tab):
        """Setup analytics and system info"""
        layout = QVBoxLayout()
        
        # System Performance
        perf_group = QGroupBox("System Performance")
        perf_group.setStyleSheet(self.get_group_style())
        perf_layout = QGridLayout()
        
        # CPU Usage
        cpu_label = QLabel("CPU Usage:")
        cpu_label.setStyleSheet("font-weight: bold;")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setStyleSheet(self.get_progress_style())
        
        # Memory Usage
        memory_label = QLabel("Memory Usage:")
        memory_label.setStyleSheet("font-weight: bold;")
        self.memory_progress = QProgressBar()
        self.memory_progress.setStyleSheet(self.get_progress_style())
        
        # Current FPS
        fps_label = QLabel("Current FPS:")
        fps_label.setStyleSheet("font-weight: bold;")
        self.current_fps_label = QLabel("0.0")
        self.current_fps_label.setStyleSheet("font-size: 16px; color: #2ECC71;")
        
        # File Size
        filesize_label = QLabel("Recording Size:")
        filesize_label.setStyleSheet("font-weight: bold;")
        self.filesize_label = QLabel("0 MB")
        self.filesize_label.setStyleSheet("font-size: 16px; color: #3498DB;")
        
        perf_layout.addWidget(cpu_label, 0, 0)
        perf_layout.addWidget(self.cpu_progress, 0, 1)
        perf_layout.addWidget(memory_label, 1, 0)
        perf_layout.addWidget(self.memory_progress, 1, 1)
        perf_layout.addWidget(fps_label, 2, 0)
        perf_layout.addWidget(self.current_fps_label, 2, 1)
        perf_layout.addWidget(filesize_label, 3, 0)
        perf_layout.addWidget(self.filesize_label, 3, 1)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # Recording Statistics
        stats_group = QGroupBox("Recording Statistics")
        stats_group.setStyleSheet(self.get_group_style())
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background: #2C3E50;
                border: 1px solid #34495E;
                border-radius: 5px;
                color: white;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        self.stats_text.setReadOnly(True)
        self.update_stats_display()
        
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        tab.setLayout(layout)
    
    def create_control_buttons(self, parent_layout):
        """Create main control buttons"""
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Record button
        self.record_button = ModernButton("🔴 Start Recording", "#E74C3C")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setMinimumHeight(50)
        
        # Pause button
        self.pause_button = ModernButton("⏸️ Pause", "#F39C12")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)
        self.pause_button.setMinimumHeight(50)
        
        # Stop button
        self.stop_button = ModernButton("⏹️ Stop", "#95A5A6")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(50)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()
        
        buttons_frame.setLayout(buttons_layout)
        parent_layout.addWidget(buttons_frame)
    
    def create_status_bar(self, parent_layout):
        """Create status bar with recording info"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background: rgba(52, 73, 94, 150);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        status_layout = QHBoxLayout()
        
        # Recording duration
        self.duration_label = QLabel("⏱️ Duration: 00:00:00")
        self.duration_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Recording status
        self.status_label = QLabel("🔴 Ready to Record")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #E74C3C;")
        
        # Version info
        version_label = QLabel("EEM Studio Pro v2.0")
        version_label.setStyleSheet("color: rgba(255, 255, 255, 150); font-size: 12px;")
        
        status_layout.addWidget(self.duration_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(version_label)
        
        status_frame.setLayout(status_layout)
        parent_layout.addWidget(status_frame)
    
    def setup_system_tray(self):
        """Setup system tray functionality"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            # You can set a custom icon here
            self.tray_icon.setToolTip("EEM Studio Pro")
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show EEM Studio Pro", self)
            show_action.triggered.connect(self.show)
            
            record_action = QAction("Start Recording", self)
            record_action.triggered.connect(self.toggle_recording)
            
            quit_action = QAction("Exit", self)
            quit_action.triggered.connect(self.close)
            
            tray_menu.addAction(show_action)
            tray_menu.addAction(record_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # Connect double-click to show window
            self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def apply_theme(self):
        """Apply the modern dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2C3E50, stop: 1 #34495E);
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: white;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
            }
        """)
    
    def get_group_style(self):
        """Get consistent group box styling"""
        return """
            QGroupBox {
                background: rgba(44, 62, 80, 100);
                border: 2px solid #34495E;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                color: white;
                margin-top: 15px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: #3498DB;
            }
        """
    
    def get_input_style(self):
        """Get consistent input styling"""
        return """
            QComboBox, QLineEdit, QSpinBox {
                background: #34495E;
                border: 2px solid #2C3E50;
                border-radius: 6px;
                padding: 8px;
                color: white;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
                border-color: #3498DB;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
        """
    
    def get_slider_style(self):
        """Get slider styling"""
        return """
            QSlider::groove:horizontal {
                border: 1px solid #34495E;
                height: 8px;
                background: #2C3E50;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498DB;
                border: 1px solid #2980B9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3498DB, stop: 1 #2980B9);
                border-radius: 4px;
            }
        """
    
    def get_progress_style(self):
        """Get progress bar styling"""
        return """
            QProgressBar {
                border: 2px solid #34495E;
                border-radius: 8px;
                text-align: center;
                color: white;
                background: #2C3E50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2ECC71, stop: 1 #27AE60);
                border-radius: 6px;
            }
        """
    
    def detect_cameras(self):
        """Detect available cameras"""
        self.device_combo.clear()
        self.device_combo.addItem("No Camera", None)
        
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.device_combo.addItem(f"Camera {i}", i)
                cap.release()
        
        # Set default to first available camera
        if self.device_combo.count() > 1:
            self.device_combo.setCurrentIndex(1)
    
    def select_output_file(self):
        """Select output file location"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"EEM_Recording_{timestamp}.mp4"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", 
            os.path.join(os.path.expanduser("~"), "Videos", default_name),
            "Video Files (*.mp4 *.avi *.mov);;All Files (*)"
        )
        
        if file_path:
            self.output_file = file_path
            self.output_line.setText(file_path)
    
    def select_region(self):
        """Select screen region to record"""
        self.hide()
        QTimer.singleShot(500, self._capture_region)
    
    def _capture_region(self):
        """Capture screen region selection"""
        from PySide6.QtWidgets import QRubberBand
        from PySide6.QtCore import QPoint, QSize
        
        # Get primary screen
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        # Create fullscreen selection window
        self.region_window = QWidget()
        self.region_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.region_window.setGeometry(screen.geometry())
        self.region_window.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        
        # Instructions label
        instructions = QLabel("Drag to select recording area. Press ESC to cancel.", self.region_window)
        instructions.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(0, 0, 0, 150);
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        instructions.move(50, 50)
        instructions.adjustSize()
        
        # Create rubber band
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.region_window)
        self.rubber_band.setStyleSheet("QRubberBand { border: 3px solid #3498DB; background: rgba(52, 152, 219, 50); }")
        
        # Variables for selection
        self.selection_start = QPoint()
        
        # Event handlers
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.selection_start = event.pos()
                self.rubber_band.setGeometry(QRect(self.selection_start, QSize()))
                self.rubber_band.show()
        
        def mouseMoveEvent(event):
            if self.rubber_band.isVisible():
                rect = QRect(self.selection_start, event.pos()).normalized()
                self.rubber_band.setGeometry(rect)
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton and self.rubber_band.isVisible():
                self.rubber_band.hide()
                rect = self.rubber_band.geometry()
                
                if rect.width() > 10 and rect.height() > 10:
                    self.selected_region = (rect.x(), rect.y(), rect.width(), rect.height())
                    self.region_line.setText(f"{rect.width()}×{rect.height()} at ({rect.x()}, {rect.y()})")
                
                self.region_window.close()
                self.show()
        
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                self.region_window.close()
                self.show()
        
        # Install event handlers
        self.region_window.mousePressEvent = mousePressEvent
        self.region_window.mouseMoveEvent = mouseMoveEvent
        self.region_window.mouseReleaseEvent = mouseReleaseEvent
        self.region_window.keyPressEvent = keyPressEvent
        
        self.region_window.show()
        self.region_window.setFocus()
    
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording"""
        if not self.output_file:
            QMessageBox.warning(self, "No Output File", 
                              "Please select an output file location first.")
            return
        
        # Get settings
        camera_device = self.device_combo.currentData()
        camera_position = self.position_combo.currentText()
        camera_size = (self.width_spin.value(), self.height_spin.value())
        fps = int(self.fps_combo.currentText())
        quality = self.quality_slider.value()
        record_audio = self.record_audio_check.isChecked()
        mouse_cursor = self.mouse_cursor_check.isChecked()
        
        # Create recorder
        self.recorder = AdvancedScreenRecorder(
            output_file=self.output_file,
            screen_region=self.selected_region,
            camera_device=camera_device,
            camera_position=camera_position,
            camera_size=camera_size,
            fps=fps,
            quality=quality,
            record_audio=record_audio,
            mouse_cursor=mouse_cursor
        )
        
        # Connect signals
        self.recorder.update_frame.connect(self.preview_widget.update_frame)
        self.recorder.recording_finished.connect(self.on_recording_finished)
        self.recorder.progress_update.connect(self.update_duration)
        self.recorder.fps_update.connect(self.update_fps)
        self.recorder.file_size_update.connect(self.update_file_size)
        
        # Start recording
        self.recorder.start()
        self.is_recording = True
        
        # Update UI
        self.record_button.setText("🔴 Recording...")
        self.record_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_label.setText("🔴 Recording in Progress")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #E74C3C;")
        
        # Show tray notification
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage("EEM Studio Pro", "Recording started", 
                                     QSystemTrayIcon.Information, 3000)
    
    def toggle_pause(self):
        """Pause or resume recording"""
        if not self.recorder:
            return
        
        if not self.is_paused:
            self.recorder.pause_recording()
            self.is_paused = True
            self.pause_button.setText("▶️ Resume")
            self.status_label.setText("⏸️ Recording Paused")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #F39C12;")
        else:
            self.recorder.resume_recording()
            self.is_paused = False
            self.pause_button.setText("⏸️ Pause")
            self.status_label.setText("🔴 Recording in Progress")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #E74C3C;")
    
    def stop_recording(self):
        """Stop recording"""
        if self.recorder:
            self.recorder.stop_recording()
    
    def on_recording_finished(self):
        """Handle recording completion"""
        self.is_recording = False
        self.is_paused = False
        
        # Update UI
        self.record_button.setText("🔴 Start Recording")
        self.record_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("⏸️ Pause")
        self.stop_button.setEnabled(False)
        self.status_label.setText("✅ Recording Complete")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2ECC71;")
        
        # Show completion message
        reply = QMessageBox.question(
            self, "Recording Complete",
            f"Recording saved successfully!\n\n{self.output_file}\n\nWould you like to open the file location?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{self.output_file}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", self.output_file])
            else:  # Linux
                subprocess.run(["xdg-open", os.path.dirname(self.output_file)])
        
        # Show tray notification
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage("EEM Studio Pro", "Recording completed successfully!", 
                                     QSystemTrayIcon.Information, 5000)
    
    def update_duration(self, seconds):
        """Update recording duration display"""
        self.recording_duration = seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        self.duration_label.setText(f"⏱️ Duration: {hours:02d}:{minutes:02d}:{secs:02d}")
    
    def update_fps(self, fps):
        """Update current FPS display"""
        self.current_fps_label.setText(f"{fps:.1f}")
        
        # Change color based on FPS
        if fps >= 25:
            color = "#2ECC71"  # Green
        elif fps >= 15:
            color = "#F39C12"  # Orange
        else:
            color = "#E74C3C"  # Red
        
        self.current_fps_label.setStyleSheet(f"font-size: 16px; color: {color}; font-weight: bold;")
    
    def update_file_size(self, size_bytes):
        """Update file size display"""
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        
        self.filesize_label.setText(size_str)
    
    def update_system_status(self):
        """Update system performance indicators"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.cpu_progress.setValue(int(cpu_percent))
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_progress.setValue(int(memory.percent))
            
            # Update stats text if on analytics tab
            if self.tab_widget.currentIndex() == 2:  # Analytics tab
                self.update_stats_display()
                
        except Exception as e:
            pass  # Ignore errors in system monitoring
    
    def update_stats_display(self):
        """Update statistics display"""
        try:
            # System info
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats_text = f"""
╔══════════════════════════════════════╗
║           EEM STUDIO PRO             ║
║        System Information            ║
╚══════════════════════════════════════╝

🖥️  System Resources:
   CPU Cores: {cpu_count}
   Total RAM: {memory.total / (1024**3):.1f} GB
   Available RAM: {memory.available / (1024**3):.1f} GB
   Disk Space: {disk.free / (1024**3):.1f} GB free

📊 Current Session:
   Recording Duration: {self.recording_duration // 3600:02d}:{(self.recording_duration % 3600) // 60:02d}:{self.recording_duration % 60:02d}
   Output File: {os.path.basename(self.output_file) if self.output_file else 'Not set'}
   Status: {'Recording' if self.is_recording else 'Ready'}

⚙️  Current Settings:
   FPS: {self.fps_combo.currentText()}
   Quality: {self.quality_slider.value()}%
   Camera: {'Enabled' if self.device_combo.currentData() is not None else 'Disabled'}
   Region: {'Custom' if self.selected_region else 'Full Screen'}

═══════════════════════════════════════
EEM Studio Pro v2.0 - Professional Recording Suite
Developed by Elijah Ekpen Mensah
© 2024 All Rights Reserved
            """
            
            self.stats_text.setPlainText(stats_text.strip())
            
        except Exception as e:
            self.stats_text.setPlainText(f"Error loading system information: {str(e)}")
    
    def load_settings(self):
        """Load application settings"""
        settings_file = os.path.join(os.path.expanduser("~"), ".eem_studio_settings.json")
        default_settings = {
            "output_directory": os.path.join(os.path.expanduser("~"), "Videos"),
            "default_fps": 30,
            "default_quality": 85,
            "camera_position": "bottom-right",
            "camera_size": [320, 240]
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return default_settings
    
    def save_settings(self):
        """Save application settings"""
        settings = {
            "output_directory": os.path.dirname(self.output_file) if self.output_file else self.settings.get("output_directory"),
            "default_fps": int(self.fps_combo.currentText()),
            "default_quality": self.quality_slider.value(),
            "camera_position": self.position_combo.currentText(),
            "camera_size": [self.width_spin.value(), self.height_spin.value()]
        }
        
        try:
            settings_file = os.path.join(os.path.expanduser("~"), ".eem_studio_settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except:
            pass
    
    def closeEvent(self, event):
        """Handle application closing"""
        if self.is_recording:
            reply = QMessageBox.question(
                self, "Recording in Progress",
                "A recording is in progress. Do you want to stop recording and exit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.recorder:
                    self.recorder.stop_recording()
                self.save_settings()
                event.accept()
            else:
                event.ignore()
        else:
            # Check if should minimize to tray
            if self.minimize_tray_check.isChecked() and hasattr(self, 'tray_icon'):
                event.ignore()
                self.hide()
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.showMessage("EEM Studio Pro", 
                                             "Application minimized to tray", 
                                             QSystemTrayIcon.Information, 2000)
            else:
                self.save_settings()
                event.accept()


def create_splash_screen():
    """Create splash screen"""
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(QColor(44, 62, 80))
    
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw gradient background
    gradient = QLinearGradient(0, 0, 400, 300)
    gradient.setColorAt(0, QColor(231, 76, 60))
    gradient.setColorAt(0.5, QColor(142, 68, 173))
    gradient.setColorAt(1, QColor(52, 152, 219))
    painter.fillRect(0, 0, 400, 300, QBrush(gradient))
    
    # Draw text
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
    painter.drawText(20, 80, 360, 50, Qt.AlignCenter, "EEM Studio Pro")
    
    painter.setFont(QFont("Segoe UI", 12))
    painter.drawText(20, 140, 360, 30, Qt.AlignCenter, "Professional Screen Recording Suite")
    painter.drawText(20, 170, 360, 30, Qt.AlignCenter, "By Elijah Ekpen Mensah")
    
    painter.setFont(QFont("Segoe UI", 10))
    painter.drawText(20, 250, 360, 30, Qt.AlignCenter, "Loading... Please wait")
    
    painter.end()
    
    splash = QSplashScreen(splash_pix)
    splash.setMask(splash_pix.mask())
    return splash


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("EEM Studio Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Elijah Ekpen Mensah")
    
    # Show splash screen
    splash = create_splash_screen()
    splash.show()
    app.processEvents()
    
    # Simulate loading time
    import time
    time.sleep(2)
    
    # Create main window
    window = EEMStudioPro()
    window.show()
    
    # Close splash
    splash.finish(window)
    
    sys.exit(app.exec())