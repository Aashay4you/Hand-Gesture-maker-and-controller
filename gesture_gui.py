import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from controller import Controller

class GestureMapperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Mapper")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        style.configure('TButton', padding=10)
        style.configure('TFrame', background='#2b2b2b')
        
        self.recording = False
        self.recording_gesture_name = ""
        self.recording_start_time = 0
        
        self.create_widgets()
        self.update_displays()
    
    def create_widgets(self):
        # Main title
        title_label = tk.Label(self.root, text="Hand Gesture Mapper", 
                              font=('Arial', 20, 'bold'), 
                              bg='#2b2b2b', fg='white')
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Recording Tab
        self.create_recording_tab(notebook)
        
        # Mapping Tab
        self.create_mapping_tab(notebook)
        
        # Actions Tab
        self.create_actions_tab(notebook)
        
        # Status Tab
        self.create_status_tab(notebook)
    
    def create_recording_tab(self, notebook):
        recording_frame = ttk.Frame(notebook, style='TFrame')
        notebook.add(recording_frame, text="Record Gestures")
        
        # Recording section
        record_label = tk.Label(recording_frame, text="Record New Gesture", 
                               font=('Arial', 14, 'bold'), 
                               bg='#2b2b2b', fg='white')
        record_label.pack(pady=10)
        
        # Gesture name input
        name_frame = tk.Frame(recording_frame, bg='#2b2b2b')
        name_frame.pack(pady=5)
        
        tk.Label(name_frame, text="Gesture Name:", 
                bg='#2b2b2b', fg='white').pack(side=tk.LEFT)
        
        self.gesture_name_entry = tk.Entry(name_frame, width=20, font=('Arial', 12))
        self.gesture_name_entry.pack(side=tk.LEFT, padx=5)
        
        # Recording buttons
        button_frame = tk.Frame(recording_frame, bg='#2b2b2b')
        button_frame.pack(pady=10)
        
        self.record_button = tk.Button(button_frame, text="Start Recording", 
                                      command=self.start_recording,
                                      bg='#4CAF50', fg='white', 
                                      font=('Arial', 12, 'bold'),
                                      padx=20, pady=5)
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop Recording", 
                                    command=self.stop_recording,
                                    bg='#f44336', fg='white', 
                                    font=('Arial', 12, 'bold'),
                                    padx=20, pady=5, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Recording status
        self.recording_status = tk.Label(recording_frame, text="Ready to record", 
                                        font=('Arial', 12), 
                                        bg='#2b2b2b', fg='yellow')
        self.recording_status.pack(pady=10)
        
        # Instructions
        instructions = """
Recording Instructions:
1. Enter a name for your gesture
2. Click 'Start Recording'
3. Hold your hand in the desired gesture position
4. Keep the gesture steady for 2-3 seconds
5. Click 'Stop Recording' when done

Tips:
- Make sure your hand is clearly visible
- Keep the gesture consistent
- Avoid complex or rapid movements
- Record in good lighting conditions
        """
        
        instruction_text = scrolledtext.ScrolledText(recording_frame, 
                                                   height=10, width=60,
                                                   font=('Arial', 10),
                                                   bg='#3b3b3b', fg='white')
        instruction_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        instruction_text.insert(tk.END, instructions)
        instruction_text.config(state=tk.DISABLED)
    
    def create_mapping_tab(self, notebook):
        mapping_frame = ttk.Frame(notebook, style='TFrame')
        notebook.add(mapping_frame, text="Map Gestures")
        
        # Mapping section
        map_label = tk.Label(mapping_frame, text="Map Gestures to Actions", 
                            font=('Arial', 14, 'bold'), 
                            bg='#2b2b2b', fg='white')
        map_label.pack(pady=10)
        
        # Gesture selection
        gesture_frame = tk.Frame(mapping_frame, bg='#2b2b2b')
        gesture_frame.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(gesture_frame, text="Select Gesture:", 
                bg='#2b2b2b', fg='white').pack(side=tk.LEFT)
        
        self.gesture_var = tk.StringVar()
        self.gesture_combo = ttk.Combobox(gesture_frame, textvariable=self.gesture_var,
                                         width=20, state="readonly")
        self.gesture_combo.pack(side=tk.LEFT, padx=5)
        
        # Action selection
        action_frame = tk.Frame(mapping_frame, bg='#2b2b2b')
        action_frame.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(action_frame, text="Select Action:", 
                bg='#2b2b2b', fg='white').pack(side=tk.LEFT)
        
        self.action_var = tk.StringVar()
        self.action_combo = ttk.Combobox(action_frame, textvariable=self.action_var,
                                        width=20, state="readonly")
        self.action_combo.pack(side=tk.LEFT, padx=5)
        
        # Map button
        map_button = tk.Button(mapping_frame, text="Create Mapping", 
                              command=self.create_mapping,
                              bg='#2196F3', fg='white', 
                              font=('Arial', 12, 'bold'),
                              padx=20, pady=5)
        map_button.pack(pady=10)
        
        # Current mappings display
        mappings_label = tk.Label(mapping_frame, text="Current Mappings", 
                                 font=('Arial', 12, 'bold'), 
                                 bg='#2b2b2b', fg='white')
        mappings_label.pack(pady=(20, 5))
        
        # Mappings listbox with scrollbar
        listbox_frame = tk.Frame(mapping_frame, bg='#2b2b2b')
        listbox_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.mappings_listbox = tk.Listbox(listbox_frame, 
                                          yscrollcommand=scrollbar.set,
                                          bg='#3b3b3b', fg='white',
                                          font=('Arial', 10))
        self.mappings_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.mappings_listbox.yview)
        
        # Remove mapping button
        remove_button = tk.Button(mapping_frame, text="Remove Selected Mapping", 
                                 command=self.remove_mapping,
                                 bg='#FF9800', fg='white', 
                                 font=('Arial', 10),
                                 padx=15, pady=3)
        remove_button.pack(pady=5)
    
    def create_actions_tab(self, notebook):
        actions_frame = ttk.Frame(notebook, style='TFrame')
        notebook.add(actions_frame, text="Available Actions")
        
        actions_label = tk.Label(actions_frame, text="Available Actions", 
                                font=('Arial', 14, 'bold'), 
                                bg='#2b2b2b', fg='white')
        actions_label.pack(pady=10)
        
        # Actions list
        self.actions_text = scrolledtext.ScrolledText(actions_frame, 
                                                     height=20, width=70,
                                                     font=('Arial', 10),
                                                     bg='#3b3b3b', fg='white')
        self.actions_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    def create_status_tab(self, notebook):
        status_frame = ttk.Frame(notebook, style='TFrame')
        notebook.add(status_frame, text="Status & Log")
        
        status_label = tk.Label(status_frame, text="System Status", 
                               font=('Arial', 14, 'bold'), 
                               bg='#2b2b2b', fg='white')
        status_label.pack(pady=10)
        
        # Status log
        self.status_text = scrolledtext.ScrolledText(status_frame, 
                                                    height=25, width=80,
                                                    font=('Arial', 9),
                                                    bg='#1e1e1e', fg='#00ff00')
        self.status_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Clear log button
        clear_button = tk.Button(status_frame, text="Clear Log", 
                                command=self.clear_log,
                                bg='#607D8B', fg='white', 
                                font=('Arial', 10))
        clear_button.pack(pady=5)
        
        self.log_message("Gesture Mapper GUI initialized")
    
    def start_recording(self):
        gesture_name = self.gesture_name_entry.get().strip()
        if not gesture_name:
            messagebox.showwarning("Warning", "Please enter a gesture name!")
            return
        
        self.recording = True
        self.recording_gesture_name = gesture_name
        self.recording_start_time = time.time()
        
        Controller.start_gesture_recording(gesture_name)
        
        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.recording_status.config(text=f"Recording '{gesture_name}'...", fg='red')
        
        self.log_message(f"Started recording gesture: {gesture_name}")
        
        # Start recording timer
        self.update_recording_timer()
    
    def stop_recording(self):
        if self.recording:
            success = Controller.stop_gesture_recording()
            
            self.recording = False
            self.record_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            if success:
                self.recording_status.config(text=f"Successfully recorded '{self.recording_gesture_name}'", fg='green')
                self.log_message(f"Successfully recorded gesture: {self.recording_gesture_name}")
                messagebox.showinfo("Success", f"Gesture '{self.recording_gesture_name}' recorded successfully!")
            else:
                self.recording_status.config(text="Recording failed - try again", fg='red')
                self.log_message(f"Failed to record gesture: {self.recording_gesture_name}")
                messagebox.showerror("Error", "Recording failed. Please try again.")
            
            self.gesture_name_entry.delete(0, tk.END)
            self.update_displays()
    
    def update_recording_timer(self):
        if self.recording:
            elapsed = time.time() - self.recording_start_time
            self.recording_status.config(text=f"Recording '{self.recording_gesture_name}' ({elapsed:.1f}s)")
            self.root.after(100, self.update_recording_timer)
    
    def create_mapping(self):
        gesture = self.gesture_var.get()
        action = self.action_var.get()
        
        if not gesture or not action:
            messagebox.showwarning("Warning", "Please select both gesture and action!")
            return
        
        if Controller.map_gesture_to_action(gesture, action):
            self.log_message(f"Mapped gesture '{gesture}' to action '{action}'")
            messagebox.showinfo("Success", f"Mapped '{gesture}' to '{action}'")
            self.update_displays()
        else:
            self.log_message(f"Failed to map gesture '{gesture}' to action '{action}'")
            messagebox.showerror("Error", "Failed to create mapping!")
    
    def remove_mapping(self):
        selection = self.mappings_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mapping to remove!")
            return
        
        mapping_text = self.mappings_listbox.get(selection[0])
        gesture_name = mapping_text.split(" -> ")[0]
        
        if Controller.remove_gesture_mapping(gesture_name):
            self.log_message(f"Removed mapping for gesture '{gesture_name}'")
            messagebox.showinfo("Success", f"Removed mapping for '{gesture_name}'")
            self.update_displays()
        else:
            messagebox.showerror("Error", "Failed to remove mapping!")
    
    def update_displays(self):
        # Update gesture combo
        gestures = list(Controller.get_gesture_mapper().gesture_templates.keys())
        self.gesture_combo['values'] = gestures
        
        # Update action combo
        actions = Controller.get_available_actions()
        self.action_combo['values'] = actions
        
        # Update mappings listbox
        self.mappings_listbox.delete(0, tk.END)
        mappings = Controller.get_mapped_gestures()
        for gesture, action in mappings.items():
            self.mappings_listbox.insert(tk.END, f"{gesture} -> {action}")
        
        # Update actions text
        self.actions_text.delete(1.0, tk.END)
        self.actions_text.insert(tk.END, "Available Actions:\n\n")
        for i, action in enumerate(actions, 1):
            description = self.get_action_description(action)
            self.actions_text.insert(tk.END, f"{i:2d}. {action}\n    {description}\n\n")
    
    def get_action_description(self, action):
        descriptions = {
            "left_click": "Perform a left mouse click",
            "right_click": "Perform a right mouse click",
            "double_click": "Perform a double click",
            "scroll_up": "Scroll up",
            "scroll_down": "Scroll down",
            "zoom_in": "Zoom in (Ctrl + scroll up)",
            "zoom_out": "Zoom out (Ctrl + scroll down)",
            "copy": "Copy selected text (Ctrl+C)",
            "paste": "Paste from clipboard (Ctrl+V)",
            "undo": "Undo last action (Ctrl+Z)",
            "redo": "Redo last action (Ctrl+Y)",
            "select_all": "Select all (Ctrl+A)",
            "new_tab": "Open new tab (Ctrl+T)",
            "close_tab": "Close current tab (Ctrl+W)",
            "refresh": "Refresh page (F5)",
            "alt_tab": "Switch between applications (Alt+Tab)",
            "minimize": "Minimize window",
            "maximize": "Maximize window",
            "screenshot": "Take a screenshot",
            "volume_up": "Increase system volume",
            "volume_down": "Decrease system volume",
            "play_pause": "Play/pause media",
            "next_track": "Next track (Ctrl+Right)",
            "prev_track": "Previous track (Ctrl+Left)",
        }
        return descriptions.get(action, "Custom action")
    
    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
    
    def clear_log(self):
        self.status_text.delete(1.0, tk.END)
        self.log_message("Log cleared")

def run_gui():
    root = tk.Tk()
    app = GestureMapperGUI(root)
    
    # Update displays every 2 seconds
    def periodic_update():
        app.update_displays()
        root.after(2000, periodic_update)
    
    periodic_update()
    root.mainloop()

if __name__ == "__main__":
    run_gui()
