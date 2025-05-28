import json
import os
import sys # Added for sys.platform
from typing import Dict, List, Callable, Any
import pyautogui
import subprocess
import time

# Attempt to import pycaw for Windows volume control
try:
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
    can_control_volume_pycaw = True
except ImportError:
    can_control_volume_pycaw = False

class GestureMapper:
    def __init__(self, config_file="gesture_config.json"):
        self.config_file = config_file
        self.gesture_mapping = {}
        self.custom_actions = {}
        self.recording_mode = False
        self.recorded_gesture = [] # Stores signatures of the gesture being recorded
        self.current_gesture_name = "" # Name of the gesture being recorded
        self.gesture_templates = {}
        self.load_config()
        self.setup_default_actions()

    def setup_default_actions(self):
        """Setup default available actions that can be mapped to gestures"""
        self.custom_actions = {
            "left_click": lambda: pyautogui.click(),
            "right_click": lambda: pyautogui.rightClick(),
            "double_click": lambda: pyautogui.doubleClick(),
            "scroll_up": lambda: pyautogui.scroll(120),
            "scroll_down": lambda: pyautogui.scroll(-120),
            "zoom_in": lambda: self.zoom_action(True),
            "zoom_out": lambda: self.zoom_action(False),
            "drag_start": lambda: pyautogui.mouseDown(button="left"), # Note: drag is usually continuous
            "drag_end": lambda: pyautogui.mouseUp(button="left"),   # So might be better handled by built-in drag
            "copy": lambda: pyautogui.hotkey('ctrl', 'c'),
            "paste": lambda: pyautogui.hotkey('ctrl', 'v'),
            "undo": lambda: pyautogui.hotkey('ctrl', 'z'),
            "redo": lambda: pyautogui.hotkey('ctrl', 'y'),
            "select_all": lambda: pyautogui.hotkey('ctrl', 'a'),
            "new_tab": lambda: pyautogui.hotkey('ctrl', 't'),
            "close_tab": lambda: pyautogui.hotkey('ctrl', 'w'),
            "refresh": lambda: pyautogui.hotkey('f5'),
            "alt_tab": lambda: pyautogui.hotkey('alt', 'tab'),
            "minimize": lambda: pyautogui.hotkey('win', 'down'), # pyautogui.hotkey('win', 'm') also works
            "maximize": lambda: pyautogui.hotkey('win', 'up'),
            "screenshot": lambda: pyautogui.screenshot(f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"), # Saves with timestamp
            "volume_up": lambda: self.volume_control(True),
            "volume_down": lambda: self.volume_control(False),
            "play_pause": lambda: pyautogui.hotkey('space'), # General media key
            "next_track": lambda: pyautogui.hotkey('nexttrack'),
            "prev_track": lambda: pyautogui.hotkey('prevtrack'),
            # You can add more pyautogui.press('...') or pyautogui.hotkey('...') commands
        }

    def zoom_action(self, zoom_in: bool):
        """Helper method for zoom actions"""
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(200 if zoom_in else -200) # Increased scroll amount for noticeable zoom
        pyautogui.keyUp('ctrl')
        print(f"Zoom {'In' if zoom_in else 'Out'} executed")

    def volume_control(self, increase: bool):
        """Helper method for cross-platform volume control."""
        try:
            if sys.platform == "win32":  # Windows
                if can_control_volume_pycaw:
                    sessions = AudioUtilities.GetAllSessions()
                    if not sessions:
                        print("No audio sessions found to control volume.")
                        pyautogui.press('volumeup' if increase else 'volumedown') # Fallback
                        return
                    for session in sessions:
                        if session.Process: # Check if session is valid
                            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                            current_volume = volume.GetMasterVolume()
                            # Increase/decrease by 0.02 (2% of total volume range 0.0 to 1.0)
                            new_volume = current_volume + (0.02 if increase else -0.02)
                            new_volume = max(0.0, min(1.0, new_volume)) # Clamp
                            volume.SetMasterVolume(new_volume, None)
                    print(f"Volume {'increased' if increase else 'decreased'} by 2% using pycaw.")
                else:
                    print("pycaw not found. Attempting pyautogui key press for volume.")
                    pyautogui.press('volumeup' if increase else 'volumedown')

            elif sys.platform == "darwin":  # macOS
                increment = 5 if increase else -5
                subprocess.run(['osascript', '-e', f'set volume output volume (output volume of (get volume settings) + {increment})'])
                print(f"Volume {'increased' if increase else 'decreased'} using osascript.")
            else:  # Linux (assuming ALSA or PulseAudio common setups)
                subprocess.run(['amixer', '-q', '-D', 'pulse', 'sset', 'Master', '2%+' if increase else '2%-'])
                # Fallback or alternative for systems without 'pulse' as default for amixer:
                # subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{"+" if increase else "-"}2%'])
                print(f"Volume {'increased' if increase else 'decreased'} by 2% using amixer/pactl.")
        except Exception as e:
            print(f"Error controlling volume: {e}. Falling back to key presses.")
            try:
                pyautogui.press('volumeup' if increase else 'volumedown')
            except Exception as e2:
                print(f"Fallback volume key press also failed: {e2}")

    def load_config(self):
        """Load gesture configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.gesture_mapping = data.get('gesture_mapping', {})
                    self.gesture_templates = data.get('gesture_templates', {})
                print(f"Loaded {len(self.gesture_mapping)} custom gesture mappings and {len(self.gesture_templates)} templates.")
            except Exception as e:
                print(f"Error loading config '{self.config_file}': {e}. Using defaults.")
                self.gesture_mapping = {}
                self.gesture_templates = {}
                self.create_default_config_if_empty() # Ensure some defaults if load fails
        else:
            print(f"Config file '{self.config_file}' not found. Creating default configuration.")
            self.create_default_config_if_empty()

    def save_config(self):
        """Save current gesture configuration to file"""
        try:
            data = {
                'gesture_mapping': self.gesture_mapping,
                'gesture_templates': self.gesture_templates
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Gesture configuration saved to '{self.config_file}'")
        except Exception as e:
            print(f"Error saving config: {e}")

    def create_default_config_if_empty(self):
        """Create default gesture mappings if current config is empty or file not found."""
        if not self.gesture_mapping and not self.gesture_templates: # Only if both are empty
            self.gesture_mapping = {
                "peace_sign": "screenshot",
                "thumbs_up": "volume_up",
                "thumbs_down": "volume_down",
                "ok_sign": "play_pause",
                "pointing_up": "scroll_up", # This is a custom gesture, built-in scroll is different
                "pointing_down": "scroll_down", # This is a custom gesture
                "fist": "minimize",
                # "open_palm": "maximize" # Example, record this gesture first
            }
            # Note: Default templates are not added here. User MUST record them.
            print("Initialized with some default gesture mappings. Please record templates for them.")
        self.save_config()

    def get_gesture_signature(self, hand_landmarks):
        """Generate a signature for the current hand gesture based on landmark data."""
        if not hand_landmarks:
            return None

        landmarks = hand_landmarks.landmark
        signature = {'fingers_up': [False] * 5, 'finger_distances': []}

        # Finger tip indices and their corresponding PIP (Proximal Interphalangeal) joint indices
        # For thumb, use TIP and IP (Interphalangeal)
        tip_indices = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Little
        pip_indices = [3, 6, 10, 14, 18]  # Thumb IP, Index PIP, Middle PIP, Ring PIP, Little PIP
        mcp_indices = [2, 5, 9, 13, 17]  # MCP joints (base of fingers)

        # Determine which fingers are "up"
        # Thumb: Compare Y-coordinate of tip to IP and MCP
        if landmarks[tip_indices[0]].y < landmarks[pip_indices[0]].y and \
           landmarks[tip_indices[0]].y < landmarks[mcp_indices[0]].y:
            signature['fingers_up'][0] = True # Thumb up

        # Other fingers: Compare Y-coordinate of tip to PIP
        for i in range(1, 5):
            if landmarks[tip_indices[i]].y < landmarks[pip_indices[i]].y and \
               landmarks[tip_indices[i]].y < landmarks[mcp_indices[i]].y:
                signature['fingers_up'][i] = True

        # Calculate normalized distances between key points (e.g., finger tips)
        # Example: Distance between thumb tip and index finger tip
        dist_thumb_index = ((landmarks[4].x - landmarks[8].x)**2 +
                            (landmarks[4].y - landmarks[8].y)**2 +
                            (landmarks[4].z - landmarks[8].z)**2)**0.5
        signature['finger_distances'].append(dist_thumb_index)

        # Example: Distance between index finger tip and middle finger tip
        dist_index_middle = ((landmarks[8].x - landmarks[12].x)**2 +
                             (landmarks[8].y - landmarks[12].y)**2 +
                             (landmarks[8].z - landmarks[12].z)**2)**0.5
        signature['finger_distances'].append(dist_index_middle)
        
        # Add more features as needed for robust gesture differentiation.
        # e.g., distances to palm center, angles between fingers.

        return signature

    def start_recording_gesture(self, gesture_name: str):
        """Start recording a new gesture"""
        self.recording_mode = True
        self.recorded_gesture = [] # Clear previous recording data
        self.current_gesture_name = gesture_name
        print(f"Recording gesture: '{gesture_name}'. Hold gesture steady.")

    def record_gesture_frame(self, hand_landmarks):
        """Record a frame (signature) of the gesture being recorded"""
        if self.recording_mode and hand_landmarks:
            signature = self.get_gesture_signature(hand_landmarks)
            if signature:
                self.recorded_gesture.append(signature)

    def stop_recording_gesture(self):
        """Stop recording and save the gesture template if enough data is collected."""
        self.recording_mode = False
        if not self.current_gesture_name:
            print("Recording stopped. No gesture name was set.")
            return False

        if len(self.recorded_gesture) > 10:  # Need at least ~10 frames for a decent average
            template = self.create_gesture_template(self.recorded_gesture)
            self.gesture_templates[self.current_gesture_name] = template
            self.save_config()
            print(f"Gesture '{self.current_gesture_name}' recorded successfully with {len(self.recorded_gesture)} frames.")
            self.recorded_gesture = []
            self.current_gesture_name = ""
            return True
        else:
            print(f"Recording failed for '{self.current_gesture_name}'. Not enough data captured ({len(self.recorded_gesture)} frames). Try holding longer.")
            self.recorded_gesture = []
            self.current_gesture_name = ""
            return False

    def create_gesture_template(self, recorded_frames: List[Dict]) -> Dict:
        """Create an average gesture template from multiple recorded frames."""
        if not recorded_frames:
            return {}

        num_frames = len(recorded_frames)
        # Assuming all signatures have the same structure (e.g., 5 fingers, 2 distances)
        num_fingers = len(recorded_frames[0]['fingers_up'])
        num_distances = len(recorded_frames[0]['finger_distances'])

        avg_fingers_up_counts = [0] * num_fingers
        avg_distances = [0.0] * num_distances

        for frame_signature in recorded_frames:
            # Count how many times each finger is up
            for i, is_up in enumerate(frame_signature['fingers_up']):
                if is_up:
                    avg_fingers_up_counts[i] += 1
            
            # Sum distances for averaging
            for i, dist in enumerate(frame_signature['finger_distances']):
                avg_distances[i] += dist

        # Create template by averaging
        template = {
            'fingers_up': [count > num_frames/2 for count in avg_fingers_up_counts], # Majority vote
            'finger_distances': [dist/num_frames for dist in avg_distances] # Mean distances
        }

        return template

    def match_gesture(self, hand_landmarks, tolerance=0.25): # Adjusted tolerance
        """Match current hand pose against recorded gesture templates."""
        if not hand_landmarks or not self.gesture_templates:
            return None

        current_signature = self.get_gesture_signature(hand_landmarks)
        if not current_signature:
            return None

        best_match = None
        best_similarity = -1.0

        for gesture_name, template in self.gesture_templates.items():
            similarity = self.calculate_gesture_similarity(current_signature, template)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = gesture_name

        # Only return a match if similarity exceeds threshold
        return best_match if best_similarity > (1.0 - tolerance) else None

    def calculate_gesture_similarity(self, signature1: Dict, signature2: Dict) -> float:
        """Calculate similarity between two gesture signatures."""
        if not signature1 or not signature2:
            return 0.0

        # Compare finger states (up/down)
        finger_match_score = sum(1 for a, b in zip(signature1['fingers_up'], signature2['fingers_up']) if a == b)
        finger_score = finger_match_score / len(signature1['fingers_up'])

        # Compare finger distances
        distance_diffs = []
        for d1, d2 in zip(signature1['finger_distances'], signature2['finger_distances']):
            # Normalize difference relative to the distances
            avg_dist = (d1 + d2) / 2
            if avg_dist > 0:
                diff = abs(d1 - d2) / avg_dist
                distance_diffs.append(max(0, 1 - diff))
            else:
                distance_diffs.append(1.0 if d1 == d2 else 0.0)

        distance_score = sum(distance_diffs) / len(distance_diffs) if distance_diffs else 1.0

        # Weighted combination (can adjust weights based on importance)
        finger_weight = 0.7  # Finger state is more important
        distance_weight = 0.3 # Distances help differentiate similar poses
        
        return (finger_score * finger_weight) + (distance_score * distance_weight)

    def map_gesture_to_action(self, gesture_name: str, action_name: str):
        """Map a gesture to an action."""
        if gesture_name not in self.gesture_templates:
            print(f"Error: Gesture '{gesture_name}' not found in templates. Record it first.")
            return False
        
        if action_name not in self.custom_actions:
            print(f"Error: Action '{action_name}' not found in available actions.")
            return False
        
        self.gesture_mapping[gesture_name] = action_name
        self.save_config()
        print(f"Mapped gesture '{gesture_name}' to action '{action_name}'")
        return True

    def execute_gesture_action(self, gesture_name: str) -> bool:
        """Execute the action mapped to a gesture."""
        if gesture_name not in self.gesture_mapping:
            # print(f"No action mapped to gesture: {gesture_name}")
            return False
        
        action_name = self.gesture_mapping[gesture_name]
        if action_name not in self.custom_actions:
            print(f"Error: Mapped action '{action_name}' not found!")
            return False
        
        try:
            self.custom_actions[action_name]()
            print(f"Executed action '{action_name}' for gesture '{gesture_name}'")
            return True
        except Exception as e:
            print(f"Error executing action '{action_name}': {e}")
            return False

    def get_available_actions(self) -> List[str]:
        """Get list of available actions that can be mapped to gestures."""
        return list(self.custom_actions.keys())

    def get_mapped_gestures(self) -> Dict[str, str]:
        """Get current gesture-to-action mappings."""
        return self.gesture_mapping.copy()

    def remove_gesture_mapping(self, gesture_name: str) -> bool:
        """Remove a gesture-to-action mapping."""
        if gesture_name in self.gesture_mapping:
            del self.gesture_mapping[gesture_name]
            self.save_config()
            print(f"Removed mapping for gesture: {gesture_name}")
            return True
        return False

    def add_custom_action(self, action_name: str, action_function: Callable[[], Any]):
        """Add a new custom action that can be mapped to gestures."""
        if action_name in self.custom_actions:
            print(f"Warning: Overwriting existing action '{action_name}'")
        self.custom_actions[action_name] = action_function
        print(f"Added custom action: {action_name}")