@echo off
echo ============================================
echo  Face Attendance System - Dependency Setup
echo ============================================
echo.
echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing cmake...
pip install cmake

echo.
echo Step 3: Installing dlib (may take a few minutes)...
pip install dlib

echo.
echo Step 4: Installing face-recognition...
pip install face-recognition

echo.
echo Step 5: Installing remaining packages...
pip install opencv-python customtkinter Pillow openpyxl matplotlib

echo.
echo ============================================
echo  Setup Complete!
echo  Run the app with:  python app.py
echo ============================================
pause
