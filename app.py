import cv2
import mediapipe as mp
from controller import Controller
import threading
import time

cap = cv2.VideoCapture(0)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

# GUI state for gesture recording
recording_gesture = False
recording_gesture_name = ""
recording_start_time = 0

def handle_keyboard_input():
    """Handle keyboard commands for gesture recording and mapping"""
    global recording_gesture, recording_gesture_name, recording_start_time
    
    while True:
        try:
            command = input().strip().lower()
            
            if command.startswith('record '):
                # Start recording a new gesture
                gesture_name = command[7:]  # Remove 'record ' prefix
                if gesture_name:
                    recording_gesture_name = gesture_name
                    recording_gesture = True
                    recording_start_time = time.time()
                    Controller.start_gesture_recording(gesture_name)
                    print(f"Recording gesture '{gesture_name}' - hold the gesture steady...")
                else:
                    print("Please provide a gesture name: record <gesture_name>")
            
            elif command == 'stop':
                # Stop recording
                if recording_gesture:
                    if Controller.stop_gesture_recording():
                        print(f"Successfully recorded gesture '{recording_gesture_name}'")
                    else:
                        print("Failed to record gesture - try again")
                    recording_gesture = False
                    recording_gesture_name = ""
                else:
                    print("No recording in progress")
            
            elif command.startswith('map '):
                # Map gesture to action
                parts = command[4:].split(' to ')
                if len(parts) == 2:
                    gesture_name, action_name = parts
                    if Controller.map_gesture_to_action(gesture_name.strip(), action_name.strip()):
                        print(f"Mapped '{gesture_name}' to '{action_name}'")
                    else:
                        print("Mapping failed - check gesture and action names")
                else:
                    print("Usage: map <gesture_name> to <action_name>")
            
            elif command == 'actions':
                # List available actions
                actions = Controller.get_available_actions()
                print("Available actions:")
                for action in actions:
                    print(f"  - {action}")
            
            elif command == 'gestures':
                # List mapped gestures
                gestures = Controller.get_mapped_gestures()
                if gestures:
                    print("Mapped gestures:")
                    for gesture, action in gestures.items():
                        print(f"  - {gesture} -> {action}")
                else:
                    print("No gestures mapped yet")
            
            elif command.startswith('remove '):
                # Remove gesture mapping
                gesture_name = command[7:]
                if Controller.remove_gesture_mapping(gesture_name):
                    print(f"Removed mapping for '{gesture_name}'")
                else:
                    print(f"No mapping found for '{gesture_name}'")
            
            elif command == 'help':
                # Show help
                print("\nAvailable commands:")
                print("  record <name>     - Start recording a new gesture")
                print("  stop              - Stop recording current gesture")
                print("  map <gesture> to <action> - Map gesture to action")
                print("  actions           - List available actions")
                print("  gestures          - List mapped gestures")
                print("  remove <gesture>  - Remove gesture mapping")
                print("  help              - Show this help")
                print("  quit              - Exit the application")
            
            elif command == 'quit':
                break
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

# Start keyboard input thread
keyboard_thread = threading.Thread(target=handle_keyboard_input, daemon=True)
keyboard_thread.start()

print("Hand Gesture Control with Custom Mapping")
print("========================================")
print("Type 'help' for available commands")
print("Press ESC in the video window to exit")
print()

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        Controller.hand_Landmarks = results.multi_hand_landmarks[0]
        mpDraw.draw_landmarks(img, Controller.hand_Landmarks, mpHands.HAND_CONNECTIONS)
        
        Controller.update_fingers_status()
        Controller.cursor_moving()
        Controller.detect_scrolling()
        Controller.detect_zoomming()
        Controller.detect_clicking()
        Controller.detect_dragging()
        
        # Detect custom gestures
        Controller.detect_custom_gestures()
    
    # Add recording indicator to the image
    if recording_gesture:
        elapsed_time = time.time() - recording_start_time
        cv2.putText(img, f"Recording: {recording_gesture_name} ({elapsed_time:.1f}s)", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(img, "Hold gesture steady - type 'stop' when done", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # Add instruction text
    cv2.putText(img, "Type 'help' in terminal for commands", 
               (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow('Hand Tracker', img)
    if cv2.waitKey(5) & 0xff == 27:
        break

cap.release()
cv2.destroyAllWindows()

# Original gesture functions (comments from original code):
# DragDrop
# rightclick
# leftclick
# doubleclick
# scroll up
# scroll down
# Zoom in 
# Zoom out
# Some of these might have been changed during the testing phase.