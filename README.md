# 🖐️ Hand Gesture Mouse Controller

A real-time hand gesture recognition system that lets you **control your mouse cursor using hand gestures** detected via your webcam. This project uses **MediaPipe**, **OpenCV**, and **PyAutoGUI** to interpret hand movements and gestures and convert them into mouse actions — like moving, clicking, and dragging — in a hands-free, intuitive way.

---

## 🧠 How It Works

The application uses:

- 🎥 **OpenCV** to capture real-time video from your webcam.
- ✋ **MediaPipe Hands** to detect and track hand landmarks.
- 🖱️ **PyAutoGUI** to control the mouse cursor and simulate clicks.

By recognizing the positions of your fingertips and gestures (like pinching), the system maps your **index finger** to move the cursor and interprets **finger distances** as click or drag gestures.

---

## 🚀 Features

- ✅ Real-time hand detection using webcam
- ✅ Cursor control using index finger
- ✅ Click events via finger pinching gesture
- ✅ Multi-finger gesture detection possible for future expansion
- ✅ Lightweight and runs on CPU

---

## 🛠️ Tech Stack

| Component       | Library Used     |
|----------------|------------------|
| Video Capture   | OpenCV           |
| Hand Detection  | MediaPipe        |
| Mouse Control   | PyAutoGUI        |
| GUI Automation  | pyperclip, PyRect, etc. |

---

## 📦 Requirements

You must have Python 3.7–3.10 installed.
If tkinter is not found on your system:
  Windows: reinstall Python with "tcl/tk and IDLE" enabled.
  Linux: sudo apt install python3-tk
  macOS: Use Python from python.org


## Project structure :
gesture_mapper.py - Core gesture mapping functionality
gesture_gui.py - Professional GUI interface
app_with_gui.py - Main application with GUI integration
Updated controller.py - Enhanced with custom gesture detection
Updated app.py - Command-line interface for gesture mapping
requirements.txt - Dependencies list


## 🚀 How to Use

After installing dependencies :
pip install -r requirements.txt

## Option 1: GUI Interface :
in terminal:

python app_with_gui.py


## 🔒 Limitations:
This is a first-phase prototype, and while it demonstrates core functionality, several limitations currently impact the user experience:

  ⚠️ Laggy Mouse Control: The cursor movement can feel laggy or unresponsive, especially on systems with lower processing power. Optimization of tracking frequency and system-level integration is pending.

  🐢 Limited Speed & Precision: Fine control of cursor speed is not yet implemented. Fast hand movements may be misinterpreted, and small motions can feel jittery.

  🚫 No Gesture Shortcut Manager: There's no separate window or interface for managing or customizing gesture-to-shortcut mappings. Users can't yet define their own gestures for system-level actions (like volume control, minimize, etc.).

  🪲 Occasional Buggy Behavior: Due to limitations in gesture accuracy and lack of filtering, false detections or unintended mouse actions can occur — particularly during fast hand motions or idle gestures near the camera.

  🧠 Hardcoded Gestures: All gestures and their mapped actions are hardcoded in the script. There is currently no gesture training or personalization capability.

  🔁 Limited Gesture Feedback: The system doesn't show real-time gesture feedback or on-screen overlays, which can make it hard for users to know if a gesture was correctly detected.



## 🪪 License

Licensed under the Apache License 2.0.
See the LICENSE file for full license text.
