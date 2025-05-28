import cv2
import mediapipe as mp
from controller import Controller # Assuming controller.py is in the same directory or Python path
import threading
import tkinter as tk
from gesture_gui import GestureMapperGUI # Assuming gesture_gui.py is in the same directory
import pyautogui

# Initialize camera and MediaPipe
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

mpHands = mp.solutions.hands
# Initialize Hands with max_num_hands=2 for two-hand detection
hands = mpHands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils

# GUI variables
gui_running = False
gui_thread = None # Thread for the GUI

def run_gui():
    """Run the GUI in a separate thread."""
    global gui_running
    gui_running = True
    
    root = tk.Tk()
    app = GestureMapperGUI(root) # Controller.get_gesture_mapper() is accessed statically by GUI
    
    def on_closing():
        global gui_running
        gui_running = False
        print("GUI window closed by user.")
        try:
            root.destroy()
        except tk.TclError:
            pass # Ignore if already destroyed
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Periodic update for GUI displays (e.g., list of gestures, actions)
    def periodic_gui_update():
        global gui_running
        if gui_running and app: # Check if app object exists
            try:
                if root.winfo_exists(): # Check if root window still exists
                    app.update_displays()
                    root.after(2000, periodic_gui_update) # Update every 2 seconds
                else:
                    gui_running = False # Stop if window is gone
            except Exception as e:
                print(f"Error during GUI periodic update: {e}")
                # gui_running = False # Optionally stop on error
    
    # Start the first periodic update if GUI is running
    if gui_running:
        root.after(100, periodic_gui_update) # Initial short delay

    try:
        root.mainloop()
    except Exception as e:
        print(f"Exception in GUI mainloop: {e}")
    finally:
        gui_running = False # Ensure flag is set if mainloop exits unexpectedly
        print("GUI mainloop finished.")


def start_gui():
    """Start the GUI thread if not already running."""
    global gui_thread, gui_running
    if not gui_running:
        gui_running = True # Set flag before starting thread
        gui_thread = threading.Thread(target=run_gui, daemon=True)
        gui_thread.start()
        print("GUI started - check the GUI window for gesture mapping options.")
    else:
        print("GUI is already running or attempting to start.")


def main():
    global gui_running
    print("Hand Gesture Control with Custom Mapping (Two-Hand Capable)")
    print("==========================================================")
    print("Controls (in video window):")
    print("  G - Open GUI for gesture mapping")
    print("  H - Show help in console")
    print("  ESC - Exit application")
    print()
    
    try:
        while True:
            success, img = cap.read()
            if not success:
                print("Failed to grab frame from webcam. Exiting.")
                break # Exit if no frame
                
            img = cv2.flip(img, 1) # Flip horizontally for intuitive movement
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)

            primary_hand_lms = None # Landmarks of the designated primary hand

            if results.multi_hand_landmarks:
                # Determine primary hand (e.g., first detected, or prefer 'Right' hand if available)
                primary_hand_idx = 0 # Default to first hand
                if results.multi_handedness:
                    for i, handedness_info in enumerate(results.multi_handedness):
                        if handedness_info.classification[0].label == 'Right':
                            primary_hand_idx = i
                            break # Found 'Right' hand, use it as primary
                
                if primary_hand_idx < len(results.multi_hand_landmarks):
                     primary_hand_lms = results.multi_hand_landmarks[primary_hand_idx]

                if primary_hand_lms:
                    Controller.hand_Landmarks = primary_hand_lms # Set for built-in functions
                    Controller.update_fingers_status() # Based on Controller.hand_Landmarks (primary)
                    
                    # These built-in actions will use the primary hand's landmarks
                    Controller.cursor_moving()
                    Controller.detect_scrolling()
                    Controller.detect_zoomming() # Renamed from zoomming
                    Controller.detect_clicking()
                    Controller.detect_dragging()
                
                # Process ALL detected hands for custom gestures and drawing
                for i, hand_lms_data in enumerate(results.multi_hand_landmarks):
                    # If recording, only use the primary hand for collecting gesture data
                    if Controller.get_gesture_mapper().recording_mode:
                        if hand_lms_data == primary_hand_lms: # Compare actual landmark objects
                            Controller.detect_custom_gestures(hand_lms_data)
                    else:
                        # If not recording, detect custom gestures on any hand
                        Controller.detect_custom_gestures(hand_lms_data)
                    
                    # Draw landmarks for the current hand
                    mpDraw.draw_landmarks(img, hand_lms_data, mpHands.HAND_CONNECTIONS)
            else:
                # No hands detected, clear primary hand landmarks for Controller
                Controller.hand_Landmarks = None 
                # Optionally reset states like dragging if no hands are present for a while
                if Controller.dragging:
                    pyautogui.mouseUp(button="left")
                    Controller.dragging = False
                    print("Dragging STOPPED (no hands detected)")


            # --- Add status information to the image ---
            cv2.putText(img, "Hand Gesture Control", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if Controller.get_gesture_mapper().recording_mode:
                rec_gesture_name = Controller.get_gesture_mapper().current_gesture_name
                cv2.putText(img, f"RECORDING: {rec_gesture_name}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            mapping_count = len(Controller.get_mapped_gestures())
            cv2.putText(img, f"Custom Gestures Mapped: {mapping_count}", (10, img.shape[0] - 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.putText(img, "G: GUI | H: Help | ESC: Exit", 
                       (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

            cv2.imshow('Hand Tracker', img)
            
            key = cv2.waitKey(5) & 0xFF # Use 0xFF mask
            if key == 27:  # ESC key
                print("ESC pressed, exiting...")
                break
            elif key == ord('g') or key == ord('G'):
                start_gui()
            elif key == ord('h') or key == ord('H'):
                show_help()

    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
    finally:
        # Cleanup
        if gui_running: # Try to close GUI nicely if it's still marked as running
            gui_running = False # Signal GUI thread to stop periodic updates
            # Note: GUI thread itself might take a moment to close if stuck in mainloop.
            # Consider root.quit() or root.destroy() if accessible and thread-safe.

        print("Releasing camera and destroying OpenCV windows...")
        cap.release()
        cv2.destroyAllWindows()
        print("Application main loop finished.")


def show_help():
    """Display help information in the console."""
    help_text = """
    Hand Gesture Control Help
    ========================
    
    Built-in Gestures (Primary Hand - usually Right, or first detected):
    - Cursor Control: Move hand (index finger tip).
    - Freeze Cursor: All fingers up + Thumb down (original logic).
    - Left Click: Index finger + thumb touch.
    - Right Click: Middle finger + thumb touch.
    - Double Click: Ring finger + thumb touch (example, can be reconfigured).
    - Drag: All fingers down (fist-like).
    - Scroll Up: Little finger up + others (Index, Middle, Ring) down.
    - Scroll Down: Index finger up + others (Middle, Ring, Little) down.
    - Zoom: Index + middle up, others down; spread/pinch to zoom in/out.
    
    Custom Gestures (Either Hand):
    - Record and map via the GUI (Press 'G').
    - Ensure gesture templates are recorded for all mapped actions.
      Your 'gesture_config.json' might be missing templates for some mappings.
    - Example default mappings (if config is new/empty, requires recording):
      'thumbs_up': 'volume_up', 'thumbs_down': 'volume_down', 'peace_sign': 'screenshot'

    Keyboard Controls (Video Window Active):
    - G: Open GUI for gesture mapping
    - H: Show this help message in the console
    - ESC: Exit application
    
    Tips for Recording Gestures:
    - Use the GUI's 'Record Gestures' tab.
    - Ensure good, consistent lighting.
    - Keep your hand clearly visible within the camera frame.
    - Hold the gesture steady for 2-3 seconds while recording.
    - Make gestures distinct from each other and from built-in gestures.
    - After recording, map it to an action in the 'Map Gestures' tab.
    """
    print(help_text)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
    finally:
        # Ensure cleanup, though main() already has its own.
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Application closed.")