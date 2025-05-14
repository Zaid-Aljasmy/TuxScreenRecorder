# 🎥 TuxScreenRecorder

**TuxScreenRecorder** is a lightweight Python GUI application for recording your screen on Linux using `ffmpeg`.  
It provides a simple and user-friendly interface built with `PyQt6`.

---

##  Screenshots

### Logo App
![Logo](logo.jpg)

### Recorder Tab
![Recorder Tab](TSRRecorderTab.png)

### Informations Tab
![Informations Tab](/TSR-InfoTab.png)

### Appimage
![Appiamge soon!](appiamge.png)
---

##  Features

- Easy-to-use interface with PyQt6  
- Supports recording full screen or custom areas (soon!)
- Save recordings as `.mp4` using `ffmpeg`  
- Simple and clean tabbed layout

---

##  Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Zaid-Aljasmy/TuxScreenRecorder.git
cd TuxScreenRecorder
```

### 2. Create and Activate a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate the environment
# For Linux/macOS:
source venv/bin/activate
# For Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶ Running the App

```bash
python main.py
```

Make sure `ffmpeg` is installed and available in your system's PATH.

To install ffmpeg on Debian/Ubuntu-based systems:

```bash
sudo apt install ffmpeg
```

---

##  License

This project is licensed under the [MIT License](LICENSE).

---

##  Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

##  Author

Developed by [Zaid Aljasmy](https://github.com/Zaid-Aljasmy)
