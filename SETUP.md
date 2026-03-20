# 🛠️ Setup Guide — Python Face Attendance App

## Windows Setup (Step by Step)

### 1. Install Python 3.10+
- Download: https://python.org/downloads
- During install: ✅ CHECK "Add Python to PATH"
- Verify: `python --version`

### 2. Install CMake (needed for dlib/face-recognition)
- Download: https://cmake.org/download/
- Choose "Windows x64 Installer"
- During install: ✅ SELECT "Add CMake to the system PATH"
- Verify: `cmake --version`

### 3. Install Visual Studio Build Tools (Windows only)
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- In the installer, select: "Desktop development with C++"
- This is required to compile dlib

### 4. Install Python packages
Open PowerShell in the project folder and run:
```bash
pip install cmake
pip install dlib
pip install face-recognition
pip install opencv-python
pip install customtkinter
pip install Pillow
pip install openpyxl
pip install matplotlib
```

Or all at once:
```bash
pip install -r requirements.txt
```

### 5. Run the app
```bash
python app.py
```

---

## Troubleshooting

### `dlib` install fails
Run these in order:
```bash
pip install cmake
pip install dlib --no-cache-dir
```
If still failing, install Visual Studio Build Tools (Step 3).

### `pip` not recognized
```bash
python -m pip install -r requirements.txt
```

### Camera not opening
- Make sure no other app (Zoom, Teams) is using the camera
- Try changing camera index in `face_engine.py` line: `cv2.VideoCapture(0)` → try `1` or `2`

### App opens but no window appears
- Run from PowerShell (not double-click)
- Check for error messages in terminal

---

## Quick Install Script (Windows)
Save as `install.bat` and double-click:
```bat
@echo off
echo Installing Face Attendance System dependencies...
pip install cmake
pip install dlib
pip install face-recognition
pip install opencv-python
pip install customtkinter
pip install Pillow
pip install openpyxl
pip install matplotlib
echo.
echo Done! Run: python app.py
pause
```
