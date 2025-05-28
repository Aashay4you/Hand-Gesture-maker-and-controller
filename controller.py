import pyautogui
from gesture_mapper import GestureMapper
import time

class Controller:
    prev_hand = None
    right_clicked = False
    left_clicked = False
    double_clicked = False
    dragging = False
    hand_Landmarks = None  # This will be set to the PRIMARY hand's landmarks by the app
    
    # Finger status attributes (will be updated based on PRIMARY hand_Landmarks)
    little_finger_down = None
    little_finger_up = None
    index_finger_down = None
    index_finger_up = None
    middle_finger_down = None
    middle_finger_up = None
    ring_finger_down = None
    ring_finger_up = None
    Thump_finger_down = None # Thumb misspelled
    Thump_finger_up = None   # Thumb misspelled
    all_fingers_down = None
    all_fingers_up = None
    index_finger_within_Thumb_finger = None
    middle_finger_within_Thumb_finger = None
    little_finger_within_Thumb_finger = None
    ring_finger_within_Thumb_finger = None
    
    screen_width, screen_height = pyautogui.size()
    
    _gesture_mapper = None  # Private class variable for lazy initialization
    
    @classmethod
    def get_gesture_mapper(cls):
        if cls._gesture_mapper is None:
            cls._gesture_mapper = GestureMapper()
        return cls._gesture_mapper
    
    # --- Custom Gesture Detection State ---
    last_gesture_time = 0           # Timestamp of the last executed custom gesture (for cooldown)
    gesture_cooldown = 1.0          # Cooldown in seconds between distinct custom gesture executions
    
    # Variables for gesture hold detection
    last_detected_gesture_name = None # Name of the gesture currently being detected/held
    gesture_hold_start_time = 0     # Timestamp when the current gesture started being detected
    gesture_hold_threshold = 0.5    # Seconds to hold a gesture before executing its action

    @staticmethod
    def update_fingers_status():
        """Updates finger statuses based on Controller.hand_Landmarks (PRIMARY hand)."""
        if Controller.hand_Landmarks is None:
            # print("No primary hand landmarks to update finger status.")
            return

        landmarks = Controller.hand_Landmarks.landmark # shortcut
        
        # Using PIP (Proximal Interphalangeal) vs MCP (Metacarpophalangeal) for up/down
        # For Thumb (landmark 4,3,2), Y might not be best. Comparing X to wrist or other fingers can be better.
        # Simplified: Thumb tip Y vs Thumb IP Y
        Controller.Thump_finger_up = landmarks[4].y < landmarks[3].y
        Controller.Thump_finger_down = not Controller.Thump_finger_up
        
        # Index: Tip (8) vs PIP (6)
        Controller.index_finger_up = landmarks[8].y < landmarks[6].y
        Controller.index_finger_down = not Controller.index_finger_up
        
        # Middle: Tip (12) vs PIP (10)
        Controller.middle_finger_up = landmarks[12].y < landmarks[10].y
        Controller.middle_finger_down = not Controller.middle_finger_up
        
        # Ring: Tip (16) vs PIP (14)
        Controller.ring_finger_up = landmarks[16].y < landmarks[14].y
        Controller.ring_finger_down = not Controller.ring_finger_up
        
        # Little: Tip (20) vs PIP (18)
        Controller.little_finger_up = landmarks[20].y < landmarks[18].y
        Controller.little_finger_down = not Controller.little_finger_up

        Controller.all_fingers_down = (Controller.index_finger_down and
                                       Controller.middle_finger_down and
                                       Controller.ring_finger_down and
                                       Controller.little_finger_down)
        Controller.all_fingers_up = (Controller.index_finger_up and
                                     Controller.middle_finger_up and
                                     Controller.ring_finger_up and
                                     Controller.little_finger_up)

        # Proximity checks for thumb + finger (for clicking)
        # These are approximate, might need tuning based on hand size and camera angle
        threshold_touch = 0.05 # Normalized distance threshold for touch
        
        # Index finger tip (8) to Thumb tip (4)
        dist_idx_thumb = ((landmarks[8].x - landmarks[4].x)**2 + (landmarks[8].y - landmarks[4].y)**2)**0.5
        Controller.index_finger_within_Thumb_finger = dist_idx_thumb < threshold_touch

        # Middle finger tip (12) to Thumb tip (4)
        dist_mid_thumb = ((landmarks[12].x - landmarks[4].x)**2 + (landmarks[12].y - landmarks[4].y)**2)**0.5
        Controller.middle_finger_within_Thumb_finger = dist_mid_thumb < threshold_touch
        
        # Ring finger tip (16) to Thumb tip (4)
        dist_ring_thumb = ((landmarks[16].x - landmarks[4].x)**2 + (landmarks[16].y - landmarks[4].y)**2)**0.5
        Controller.ring_finger_within_Thumb_finger = dist_ring_thumb < threshold_touch

        # Little finger (20) to Thumb tip (4) - less common for clicks, but for completeness
        dist_lit_thumb = ((landmarks[20].x - landmarks[4].x)**2 + (landmarks[20].y - landmarks[4].y)**2)**0.5
        Controller.little_finger_within_Thumb_finger = dist_lit_thumb < threshold_touch

    @staticmethod
    def get_position(hand_x_position, hand_y_position):
        # This smoothing logic can be complex. A simple direct mapping or light smoothing.
        # pyautogui.moveTo clamps to screen edges automatically.
        
        # Raw mapping:
        # current_x = int(hand_x_position * Controller.screen_width)
        # current_y = int(hand_y_position * Controller.screen_height)

        # Smoothed movement (exponential moving average or simple interpolation)
        # For simplicity, using a sensitivity factor for now.
        sensitivity = 1.5 # Adjust this for faster/slower cursor
        
        old_x, old_y = pyautogui.position()
        
        # Map normalized hand position (0-1) to screen coordinates
        # Invert X if camera is mirrored and flip is applied (img = cv2.flip(img, 1))
        # If not flipped, hand_x_position directly maps. Assuming flip is done.
        target_x = int((1.0 - hand_x_position) * Controller.screen_width)
        target_y = int(hand_y_position * Controller.screen_height)

        # Interpolate for smoother movement
        move_x = old_x + (target_x - old_x) * 0.3 # Adjust 0.3 for smoothness
        move_y = old_y + (target_y - old_y) * 0.3

        # Apply sensitivity by amplifying the delta from current position to target
        # This might make it jumpy if not careful. The interpolation above is usually better.
        # Let's stick to interpolated move_x, move_y for now.

        # pyautogui.moveTo already handles clamping to screen edges.
        return (int(move_x), int(move_y))

    @staticmethod
    def cursor_moving():
        if Controller.hand_Landmarks is None: return
        
        # Use index finger tip (landmark 8) for cursor control
        # Using MCP (landmark 0) or a point between fingers can also be stable.
        point_idx = 8 
        current_x_norm = Controller.hand_Landmarks.landmark[point_idx].x
        current_y_norm = Controller.hand_Landmarks.landmark[point_idx].y
        
        x, y = Controller.get_position(current_x_norm, current_y_norm)
        
        # Cursor freeze condition: e.g., fist (all fingers down) or specific gesture
        # Original: all_fingers_up and Thump_finger_down
        # Let's use: if all fingers are down (fist-like) or a specific 'freeze' custom gesture
        cursor_freezed = Controller.all_fingers_up and Controller.Thump_finger_down # Original logic

        if not cursor_freezed:
            pyautogui.moveTo(x, y, duration=0) # duration=0 for fastest response

    @staticmethod
    def detect_scrolling():
        if Controller.hand_Landmarks is None: return

        # Scroll Up: Little finger up, others down (Index, Middle, Ring)
        scrolling_up = (Controller.little_finger_up and
                        Controller.index_finger_down and
                        Controller.middle_finger_down and
                        Controller.ring_finger_down)
        if scrolling_up:
            pyautogui.scroll(120) # Scroll amount
            print("Scrolling UP (built-in)")
            time.sleep(0.2) # Small delay to prevent rapid scrolling

        # Scroll Down: Index finger up, others down (Middle, Ring, Little)
        scrolling_down = (Controller.index_finger_up and
                          Controller.middle_finger_down and
                          Controller.ring_finger_down and
                          Controller.little_finger_down)
        if scrolling_down:
            pyautogui.scroll(-120) # Scroll amount
            print("Scrolling DOWN (built-in)")
            time.sleep(0.2) # Small delay

    @staticmethod
    def detect_zoomming(): # Renamed from zoomming
        if Controller.hand_Landmarks is None: return

        # Zoom: Index and Middle up, Ring and Little down
        zoom_base_gesture = (Controller.index_finger_up and
                             Controller.middle_finger_up and
                             Controller.ring_finger_down and
                             Controller.little_finger_down)
        
        if zoom_base_gesture:
            # Distance between index tip (8) and middle tip (12)
            landmarks = Controller.hand_Landmarks.landmark
            dist_index_middle = ((landmarks[8].x - landmarks[12].x)**2 + 
                                 (landmarks[8].y - landmarks[12].y)**2)**0.5
            
            # Define thresholds for pinch/spread
            pinch_threshold = 0.07  # Fingers close
            spread_threshold = 0.12 # Fingers further apart
                                    # These thresholds are relative to normalized coordinates
                                    # and may need calibration.

            # Store previous distance to detect change
            if not hasattr(Controller, 'prev_zoom_dist'):
                Controller.prev_zoom_dist = dist_index_middle

            current_dist = dist_index_middle
            
            # Zoom In: Fingers spreading apart
            if current_dist > Controller.prev_zoom_dist and current_dist > spread_threshold * 0.8: # check if spreading and somewhat spread
                pyautogui.keyDown('ctrl')
                pyautogui.scroll(100) # positive for zoom in
                pyautogui.keyUp('ctrl')
                print("Zooming In (built-in)")
                time.sleep(0.1) # debounce
            
            # Zoom Out: Fingers pinching together
            elif current_dist < Controller.prev_zoom_dist and current_dist < pinch_threshold * 1.2: # check if pinching and somewhat pinched
                pyautogui.keyDown('ctrl')
                pyautogui.scroll(-100) # negative for zoom out
                pyautogui.keyUp('ctrl')
                print("Zooming Out (built-in)")
                time.sleep(0.1) # debounce
            
            Controller.prev_zoom_dist = current_dist


    @staticmethod
    def detect_clicking():
        if Controller.hand_Landmarks is None: return

        # Left Click: Index finger touches thumb, other main fingers (Middle, Ring, Little) are up.
        left_click_condition = (Controller.index_finger_within_Thumb_finger and
                                Controller.middle_finger_up and
                                Controller.ring_finger_up and
                                Controller.little_finger_up and
                                not Controller.middle_finger_within_Thumb_finger and # Ensure other fingers aren't also touching
                                not Controller.ring_finger_within_Thumb_finger)

        if not Controller.left_clicked and left_click_condition:
            pyautogui.click()
            Controller.left_clicked = True
            print("Left Clicking (built-in)")
            # time.sleep(0.2) # Debounce if needed
        elif not Controller.index_finger_within_Thumb_finger: # Reset when finger moves away
            Controller.left_clicked = False

        # Right Click: Middle finger touches thumb, other main fingers (Index, Ring, Little) are up.
        right_click_condition = (Controller.middle_finger_within_Thumb_finger and
                                 Controller.index_finger_up and
                                 Controller.ring_finger_up and
                                 Controller.little_finger_up and
                                 not Controller.index_finger_within_Thumb_finger and
                                 not Controller.ring_finger_within_Thumb_finger)
        if not Controller.right_clicked and right_click_condition:
            pyautogui.rightClick()
            Controller.right_clicked = True
            print("Right Clicking (built-in)")
            # time.sleep(0.2)
        elif not Controller.middle_finger_within_Thumb_finger:
            Controller.right_clicked = False

        # Double Click: Ring finger touches thumb (example, can be changed)
        double_click_condition = (Controller.ring_finger_within_Thumb_finger and
                                  Controller.index_finger_up and
                                  Controller.middle_finger_up and
                                  Controller.little_finger_up and
                                  not Controller.index_finger_within_Thumb_finger and
                                  not Controller.middle_finger_within_Thumb_finger)
        if not Controller.double_clicked and double_click_condition:
            pyautogui.doubleClick()
            Controller.double_clicked = True
            print("Double Clicking (built-in)")
            # time.sleep(0.2)
        elif not Controller.ring_finger_within_Thumb_finger:
            Controller.double_clicked = False

    @staticmethod
    def detect_dragging():
        if Controller.hand_Landmarks is None: return
        
        # Drag: All fingers (Index, Middle, Ring, Little) are down (fist-like)
        # Assumes thumb state doesn't matter for this simple drag.
        drag_condition = Controller.all_fingers_down 

        if not Controller.dragging and drag_condition:
            pyautogui.mouseDown(button="left")
            Controller.dragging = True
            print("Dragging STARTED (built-in)")
        elif Controller.dragging and not drag_condition: # If dragging and condition is no longer met
            pyautogui.mouseUp(button="left")
            Controller.dragging = False
            print("Dragging STOPPED (built-in)")
            
    @staticmethod
    def detect_custom_gestures(current_hand_landmarks):
        """Detect and execute custom gestures for the given hand landmarks."""
        current_time = time.time()

        # Handle recording mode:
        if Controller.get_gesture_mapper().recording_mode:
            # The app_with_gui.py ensures this is called only for the primary hand during recording.
            Controller.get_gesture_mapper().record_gesture_frame(current_hand_landmarks)
            # print(f"Recording frame for {Controller.gesture_mapper.current_gesture_name}...") # Debug
            return # Don't try to match/execute while recording

        # Cooldown check: only allow new gesture execution after cooldown period
        if current_time - Controller.last_gesture_time < Controller.gesture_cooldown:
            return

        detected_gesture_name = Controller.get_gesture_mapper().match_gesture(current_hand_landmarks)

        if detected_gesture_name:
            if detected_gesture_name == Controller.last_detected_gesture_name:
                # Gesture is being held, check if hold time exceeds threshold
                if (current_time - Controller.gesture_hold_start_time) >= Controller.gesture_hold_threshold:
                    if Controller.get_gesture_mapper().execute_gesture_action(detected_gesture_name):
                        Controller.last_gesture_time = current_time  # Reset cooldown timer
                        # Reset hold state as action is executed
                        Controller.last_detected_gesture_name = None 
                        Controller.gesture_hold_start_time = 0
            else:
                # New gesture detected, start tracking its hold time
                Controller.last_detected_gesture_name = detected_gesture_name
                Controller.gesture_hold_start_time = current_time
        else:
            # No gesture (or no match), reset hold state
            Controller.last_detected_gesture_name = None
            Controller.gesture_hold_start_time = 0
            
    # --- Methods to interact with GestureMapper (called from GUI or main app) ---
    @staticmethod
    def start_gesture_recording(gesture_name: str):
        Controller.get_gesture_mapper().start_recording_gesture(gesture_name)

    @staticmethod
    def stop_gesture_recording() -> bool:
        return Controller.get_gesture_mapper().stop_recording_gesture()

    @staticmethod
    def map_gesture_to_action(gesture_name: str, action_name: str) -> bool:
        return Controller.get_gesture_mapper().map_gesture_to_action(gesture_name, action_name)

    @staticmethod
    def get_available_actions() -> list:
        return Controller.get_gesture_mapper().get_available_actions()

    @staticmethod
    def get_mapped_gestures() -> dict:
        return Controller.get_gesture_mapper().get_mapped_gestures()

    @staticmethod
    def remove_gesture_mapping(gesture_name: str) -> bool:
        return Controller.get_gesture_mapper().remove_gesture_mapping(gesture_name)