# 🎬 EEM Studio Pro

**Professional Screen Recording Suite**

*Developed by Elijah Ekpen Mensah*

---

## 📖 Overview

**EEM Studio Pro** is a powerful, professional-grade screen recording application built with modern UI design and advanced features. This comprehensive recording suite combines high-quality screen capture with camera overlay capabilities, real-time performance monitoring, and an intuitive user interface.

### ✨ Key Highlights
- 🎯 **Professional Branding** - Fully branded with EEM Studio Pro identity
- 🖥️ **High-Quality Recording** - Multiple resolution and FPS options
- 📹 **Camera Integration** - Seamless webcam overlay with positioning controls
- 📊 **Real-Time Analytics** - System performance monitoring and recording statistics
- 🎨 **Modern UI** - Dark theme with gradient backgrounds and professional styling
- ⚙️ **Advanced Settings** - Comprehensive configuration options
- 🔔 **System Tray Support** - Background operation with tray notifications

---

## 🚀 Features

### 🎥 Recording Capabilities
- **Screen Recording** with customizable regions
- **Camera Overlay** with adjustable positioning (top-left, top-right, bottom-left, bottom-right)
- **Multiple FPS Options** (24, 30, 60 fps)
- **Quality Control** with adjustable compression (50-100%)
- **Pause/Resume** functionality during recording
- **Mouse Cursor** capture toggle
- **Audio Recording** support (system audio)

### 🖼️ Visual Interface
- **Live Preview** with professional styling
- **Tabbed Interface** (Recording, Settings, Analytics)
- **Modern Dark Theme** with gradient backgrounds
- **Branded Splash Screen** on startup
- **Custom Styled Controls** with hover effects and shadows
- **Real-Time Status Updates** with color-coded indicators

### 📈 Analytics & Monitoring
- **Real-Time System Monitoring** (CPU and Memory usage)
- **Recording Statistics** (duration, file size, FPS)
- **Performance Metrics** display
- **System Information** panel
- **Session Analytics** with detailed reporting

### ⚙️ Advanced Settings
- **Camera Device Selection** with auto-detection
- **Camera Size Configuration** (160x120 to 640x480)
- **Region Selection** with visual feedback
- **Output Format Options** (MP4, AVI, MOV)
- **Settings Persistence** - remembers your preferences
- **System Tray Integration** with minimize-to-tray option

---

## 📋 System Requirements

### Minimum Requirements
- **Operating System:** Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **RAM:** 4 GB (8 GB recommended for 1080p recording)
- **CPU:** Intel i3 or AMD equivalent (i5+ recommended for 60fps recording)
- **Storage:** 1 GB available space (plus space for recordings)
- **Camera:** Optional - USB webcam or built-in camera

### Recommended Specifications
- **RAM:** 8 GB or more
- **CPU:** Intel i5/AMD Ryzen 5 or better
- **GPU:** Dedicated graphics card for better performance
- **Storage:** SSD with 10+ GB free space
- **Network:** Internet connection for updates

---

## 🔧 Installation

### Prerequisites
Ensure you have Python 3.8 or higher installed on your system.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Required Packages
```bash
pip install PySide6 opencv-python pyautogui numpy psutil
```

### Step 3: Run the Application
```bash
python eem_studio_pro.py
```

### Requirements.txt
```text
PySide6>=6.5.0
opencv-python>=4.8.0
pyautogui>=0.9.54
numpy>=1.24.0
psutil>=5.9.0
```

---

## 🎮 Usage Guide

### Getting Started

1. **Launch Application**
   - Run the Python script or executable
   - Wait for the splash screen to load
   - The main interface will appear with three tabs

2. **Basic Recording**
   - Go to the **Recording** tab
   - Click **Browse** to select output file location
   - Configure quality and FPS settings
   - Click **🔴 Start Recording**
   - Click **⏹️ Stop** when finished

### 📹 Recording Tab

#### Output Settings
- **Output File:** Choose where to save your recording
- **Capture Region:** Select full screen or custom region
- **FPS:** Choose between 24, 30, or 60 frames per second
- **Quality:** Adjust compression quality (50-100%)

#### Recording Controls
- **🔴 Start Recording:** Begin screen capture
- **⏸️ Pause:** Temporarily pause recording
- **▶️ Resume:** Continue paused recording
- **⏹️ Stop:** End recording and save file

### ⚙️ Settings Tab

#### Camera Configuration
- **Camera Device:** Select from detected cameras or disable
- **Camera Position:** Choose overlay position on screen
- **Camera Size:** Adjust webcam window dimensions

#### Advanced Options
- **Record System Audio:** Include system sounds
- **Show Mouse Cursor:** Display cursor in recording
- **Minimize to System Tray:** Hide to tray during recording

### 📊 Analytics Tab

#### System Performance
- **CPU Usage:** Real-time processor utilization
- **Memory Usage:** RAM consumption monitoring
- **Current FPS:** Live frame rate display
- **Recording Size:** File size tracker

#### Session Statistics
- Detailed system information
- Recording session data
- Performance metrics
- Application version and credits

### 🎯 Region Selection

1. Click **Select** button next to "Capture Region"
2. Application will minimize temporarily
3. Drag to select desired screen area
4. Release mouse to confirm selection
5. Press **ESC** to cancel selection

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Start/Stop Recording |
| `P` | Pause/Resume Recording |
| `Esc` | Cancel Region Selection |
| `Ctrl+Q` | Quit Application |
| `F11` | Toggle Fullscreen Preview |

---

## 🔧 Configuration

### Settings File Location
Settings are automatically saved to:
- **Windows:** `%USERPROFILE%\.eem_studio_settings.json`
- **macOS/Linux:** `~/.eem_studio_settings.json`

### Default Settings
```json
{
  "output_directory": "~/Videos",
  "default_fps": 30,
  "default_quality": 85,
  "camera_position": "bottom-right",
  "camera_size": [320, 240]
}
```

---

## 🎨 Customization

### Color Themes
The application uses a professional dark theme with the following color palette:
- **Primary:** #3498DB (Blue)
- **Secondary:** #E74C3C (Red)
- **Success:** #2ECC71 (Green)
- **Warning:** #F39C12 (Orange)
- **Background:** #2C3E50 to #34495E (Dark Blue Gradient)

### UI Modifications
To customize the interface, modify the stylesheet methods in the `EEMStudioPro` class:
- `get_group_style()` - Group box styling
- `get_input_style()` - Input field styling
- `get_slider_style()` - Slider styling
- `apply_theme()` - Overall theme application

---

## 🚨 Troubleshooting

### Common Issues

#### Camera Not Detected
- Ensure camera is not being used by another application
- Try different USB ports for external cameras
- Restart the application
- Check camera permissions in system settings

#### Recording Quality Issues
- Reduce FPS for better quality on slower systems
- Increase quality slider value
- Close unnecessary applications during recording
- Ensure sufficient storage space

#### Performance Problems
- Monitor CPU/Memory usage in Analytics tab
- Lower recording resolution
- Reduce FPS to 24 for slower systems
- Close background applications

#### Audio Not Recording
- Enable "Record System Audio" in Settings
- Check system audio permissions
- Ensure audio devices are properly configured
- Try restarting the application

### Error Messages

| Error | Solution |
|-------|----------|
| "No Output File" | Select a save location before recording |
| "Camera Unavailable" | Check camera connections and permissions |
| "Insufficient Storage" | Free up disk space in output directory |
| "Recording Failed" | Restart application and try again |

---

## 🔒 Privacy & Security

### Data Collection
EEM Studio Pro does **NOT** collect or transmit any personal data. All recordings and settings remain on your local system.

### File Security
- Recordings are saved locally to your chosen directory
- No cloud upload or external transmission
- Settings file contains only application preferences
- No network connectivity required for operation

### Permissions Required
- **Camera Access:** For webcam overlay (optional)
- **Screen Recording:** For screen capture functionality
- **File System:** For saving recordings and settings
- **System Information:** For performance monitoring

---

## 🤝 Contributing

We welcome contributions to EEM Studio Pro! Here's how you can help:

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies
4. Make your changes
5. Test thoroughly
6. Submit a pull request

### Bug Reports
When reporting bugs, please include:
- Operating system and version
- Python version
- Complete error message
- Steps to reproduce the issue
- System specifications

### Feature Requests
For new features, please provide:
- Detailed description of the feature
- Use case scenarios
- Expected behavior
- Implementation suggestions (if any)

---

## 📄 License

**EEM Studio Pro** is developed by **Elijah Ekpen Mensah**.

### Terms of Use
- ✅ Personal use permitted
- ✅ Educational use permitted
- ✅ Modification for personal use permitted
- ❌ Commercial redistribution prohibited without permission
- ❌ Removal of branding/credits prohibited

For commercial licensing inquiries, please contact the developer.

---

## 📞 Support & Contact

### Getting Help
- **Documentation:** Refer to this README
- **Issues:** Check the troubleshooting section
- **Updates:** Keep the application updated for best performance

### Contact Information
- **Developer:** Elijah Ekpen Mensah
- **Project:** EEM Studio Pro
- **Version:** 2.0
- **Release Date:** 2024

### Social Media & Updates
Stay connected for updates and announcements:
- Follow development progress
- Get notified of new features
- Access community support

---

## 🎉 Acknowledgments

### Technologies Used
- **PySide6** - Modern Qt-based GUI framework
- **OpenCV** - Computer vision and video processing
- **PyAutoGUI** - Screen capture functionality
- **NumPy** - Numerical computing for image processing
- **psutil** - System and process monitoring

### Special Thanks
- Qt Project for the excellent PySide6 framework
- OpenCV community for robust video processing tools
- Python community for extensive library ecosystem
- Beta testers and early adopters for valuable feedback

---

## 🔄 Version History

### Version 2.0 (Current)
- ✨ Complete UI redesign with modern dark theme
- 🎥 Enhanced recording capabilities with pause/resume
- 📊 Real-time analytics and system monitoring
- 📹 Improved camera integration with effects
- ⚙️ Advanced settings panel with persistence
- 🔔 System tray integration
- 🎨 Professional branding and splash screen

### Version 1.0 (Legacy)
- Basic screen recording functionality
- Simple camera overlay
- Basic UI with minimal styling
- Essential recording controls

---

## 🚀 Future Roadmap

### Planned Features
- **Multi-monitor support** with monitor selection
- **Audio waveform visualization** in real-time
- **Annotation tools** for drawing on screen during recording
- **Hotkey customization** for all functions
- **Export presets** for different platforms (YouTube, Vimeo, etc.)
- **Built-in video editor** with basic editing tools
- **Cloud storage integration** for automatic backup
- **Streaming capabilities** to popular platforms

### Technical Improvements
- **Hardware acceleration** for better performance
- **GPU encoding** support for faster processing
- **Optimized memory usage** for longer recordings
- **Enhanced error handling** and recovery
- **Automated testing** suite for stability
- **Cross-platform packaging** for easy installation

---

**Thank you for using EEM Studio Pro!** 🎬

*Professional Screen Recording Made Simple*

**Developed with ❤️ by Elijah Ekpen Mensah**