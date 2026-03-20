# 🎯 Face Detection Attendance System — Python

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> AI-powered real-time face recognition attendance system built with Python, Flask, face_recognition & SQLite.

---

## ✨ Features

- 🤖 **Real-time Face Detection** via webcam using `face_recognition` (dlib)
- 👤 **Student Enrollment** — capture 5 face samples for high accuracy
- ✅ **One-click Attendance** — auto-mark when face is detected
- 📊 **Dashboard** — weekly charts (bar, line, pie)
- 📁 **CSV Export** — download attendance for any date
- 🔒 **Session-based Login** — secure admin panel
- 🗄️ **SQLite Database** — zero setup, just a file

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| Face AI | face_recognition (dlib), OpenCV |
| Database | SQLite via Flask-SQLAlchemy |
| Frontend | HTML5, CSS3, Vanilla JS, Chart.js |
| Export | pandas, openpyxl, CSV |

---

## 📁 Project Structure

```
face-attendance-python/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── data/
│   └── attendance.db       # SQLite database (auto-created)
├── known_faces/            # Optional: store face photos
└── templates/
    ├── login.html          # Login page
    └── index.html          # Main app UI
```

---

## 🚀 Setup & Run

### Step 1 — Install Python 3.10+
Download from: https://python.org (check "Add to PATH" during install)

```bash
python --version   # Should show 3.10+
```

### Step 2 — Install dependencies

```bash
cd face-attendance-python
pip install -r requirements.txt
```

> ⚠️ `face_recognition` needs `cmake` and Visual Studio Build Tools on Windows.
> See **Windows Installation** section below.

### Step 3 — Run the app

```bash
python app.py
```

Open browser: **http://localhost:5000**

### Step 4 — Login

```
Username: admin
Password: admin123
```

---

## 🪟 Windows Installation (face_recognition)

`face_recognition` uses dlib which needs C++ build tools. Follow these steps:

### Option A — Pre-built wheels (Easiest)

```bash
pip install cmake
pip install dlib
pip install face_recognition
```

If dlib fails, download pre-built wheel from:
https://github.com/z-mahmud22/Dlib_Windows_Python3.x

```bash
pip install dlib-19.24.2-cp310-cp310-win_amd64.whl
pip install face_recognition
```

### Option B — Install Visual Studio Build Tools

1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Then run: `pip install face_recognition`

### Install remaining packages

```bash
pip install flask flask-cors flask-sqlalchemy opencv-python numpy Pillow pandas openpyxl
```

---

## 🎮 How to Use

1. **Login** with admin / admin123
2. **Start Camera** — click the button, allow browser permission
3. **Add a student** — type name + roll no → click "+ Add & Enroll"
4. **Enroll face** — system captures 5 samples automatically
5. **Mark attendance** — when face is detected, click "✓ Mark Attend"
6. **View roster** — click Roster tab, select date
7. **Export CSV** — click "⬇ Export CSV" button

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Login |
| GET | `/api/students` | List all students |
| POST | `/api/students` | Add student |
| DELETE | `/api/students/<id>` | Delete student |
| POST | `/api/students/<id>/enroll` | Enroll face (base64 image) |
| POST | `/api/recognize` | Recognize face in image |
| POST | `/api/attendance/mark` | Mark attendance |
| GET | `/api/attendance/today` | Today's records |
| GET | `/api/attendance/report?date=` | Report by date |
| GET | `/api/attendance/stats` | Dashboard stats |
| GET | `/api/attendance/export?date=` | Download CSV |

---

## 👨‍💻 Author

**Sonu** — MCA Student, Ram Lal Anand College, University of Delhi

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/YOUR_PROFILE)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/YOUR_USERNAME)

---

<div align="center">⭐ Star this repo if it helped you!</div>
