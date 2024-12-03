import tkinter as tk
from tkinter import ttk
import random
import time
from threading import Thread
import json
import os
import platform
from pathlib import Path
import ctypes

# Handle blur text in window.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Function to load JSON data
def load_json(file_name):
    # Get the directory where the script is located
    base_dir = Path(__file__).resolve().parent
    # Construct the full path to the JSON file
    full_path = base_dir / file_name
    
    if full_path.exists():
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"JSON file not found: {full_path}")

# Method to play a beep sound
def play_beep():
    if platform.system() == "Windows":
        # Windows beep sound
        import winsound
        winsound.Beep(1000, 200)  # Frequency=1000Hz, Duration=200ms
    elif platform.system() == "Darwin":
        # macOS beep sound
        os.system("say ready")  # Uses built-in `say` command to produce a sound
    else:
        # Linux beep sound
        os.system("echo -e '\a'")  # ASCII bell character

# Main GUI application
class DictationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nihongo Kana Dictation")
        
        self.characters_to_display = []
        self.kana_pool = {}

        # Load kana dictionaries
        self.kana_files = {
            "Seion": "seion.json",
            "Dakuon": "dakuon.json",
            "Handakuon": "handakuon.json",
            "Yoon": "yoon.json"
        }
        
        # Checkboxes for kana selection
        self.checkbox_vars = {}
        for name in self.kana_files.keys():
            self.checkbox_vars[name] = tk.IntVar()

        # Left side of the GUI
        left_frame = tk.Frame(root)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        # Instruction 1: Select character type
        self.label_instruction_1 = tk.Label(left_frame, text="Select Character Type:")
        self.label_instruction_1.pack(pady=5)
        
        # Buttons for Hiragana or Katakana
        self.character_type = 0  # Default to Hiragana
        self.button_hiragana = tk.Button(left_frame, text="Hiragana", command=self.select_hiragana)
        self.button_hiragana.pack(pady=5)
        
        self.button_katakana = tk.Button(left_frame, text="Katakana", command=self.select_katakana)
        self.button_katakana.pack(pady=5)

        # Instruction 2: Select character sets
        self.label_instruction_2 = tk.Label(left_frame, text="Select Character Sets:")
        self.label_instruction_2.pack(pady=5)

        # Checkbox options with maximum characters display
        self.max_count_labels = {}  # To store labels for max counts
        for name, var in self.checkbox_vars.items():
            frame = tk.Frame(left_frame)
            frame.pack(anchor="w")  # Ensure alignment

            # Create checkbox
            cb = tk.Checkbutton(frame, text=name, variable=var)
            cb.pack(side="left")

            # Load the character set and calculate its length
            kana_data = load_json(self.kana_files[name])
            max_chars = len(kana_data)

            # Create a label to show the count
            label = tk.Label(frame, text=f"({max_chars} chars)", font=("Arial", 10), fg="gray")
            label.pack(side="left", padx=5)
            self.max_count_labels[name] = label  # Store the label for future updates

        # Number of characters entry
        self.label_number = tk.Label(left_frame, text="Enter number of characters:")
        self.label_number.pack(pady=5)
        
        self.entry_number = tk.Entry(left_frame)
        self.entry_number.insert(0, "15")  # Default to 15 characters
        self.entry_number.pack(pady=5)
        
        # Wait time entry
        self.label_time = tk.Label(left_frame, text="Enter wait time (seconds):")
        self.label_time.pack(pady=5)
        
        self.entry_time = tk.Entry(left_frame)
        self.entry_time.insert(0, "10")  # Default to 10 seconds
        self.entry_time.pack(pady=5)
        
        # Start button
        self.button_start = tk.Button(left_frame, text="Start", command=self.start_dictation)
        self.button_start.pack(pady=5)
        
        # Character display
        self.label_display = tk.Label(left_frame, text="", font=("Arial", 42))
        self.label_display.pack(pady=20)
        
        # Show answer button
        self.button_show_answer = tk.Button(left_frame, text="Show Answer", command=self.show_answer)
        self.button_show_answer.pack(pady=5)
        self.button_show_answer.pack_forget()

        # Error message display
        self.label_error = tk.Label(left_frame, text="", fg="red")
        self.label_error.pack(pady=5)

        # Right side scrollable frame for answers
        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.right_frame)
        self.scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def select_hiragana(self):
        self.character_type = 0  # Index for Hiragana
        self.label_error.config(text="Selected: Hiragana")
    
    def select_katakana(self):
        self.character_type = 1  # Index for Katakana
        self.label_error.config(text="Selected: Katakana")

    def start_dictation(self):
        # Clear previous answers
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Validate input
        num_characters = self.entry_number.get()
        if not num_characters.isdigit():
            self.label_error.config(text="Please enter a valid number of characters.")
            return
        
        num_characters = int(num_characters)
        if num_characters <= 0:
            self.label_error.config(text="Number of characters must be positive.")
            return
        
        # Validate wait time
        wait_time = self.entry_time.get()
        if not wait_time.isdigit():
            self.label_error.config(text="Invalid wait time. Defaulting to 15 seconds.")
            wait_time = 15
        else:
            wait_time = int(wait_time)
        
        # Load selected kana sets
        self.kana_pool = {}
        for name, var in self.checkbox_vars.items():
            if var.get() == 1:  # Checkbox selected
                kana_data = load_json(self.kana_files[name])
                for romanji, kana in kana_data.items():
                    self.kana_pool[romanji] = kana[self.character_type]  # Choose Hiragana or Katakana
        
        if not self.kana_pool:
            self.label_error.config(text="Please select at least one character set.")
            return

        # Randomly select unique characters
        kana_items = list(self.kana_pool.items())
        if len(kana_items) < num_characters:
            self.label_error.config(text="Not enough unique characters in the selected set.")
            return

        self.characters_to_display = random.sample(kana_items, k=num_characters)
        
        self.label_error.config(text="Starting dictation...")
        self.entry_number.delete(0, tk.END)
        
        # Start dictation in a separate thread
        Thread(target=self.dictation_loop, args=(wait_time,)).start()
    
    def dictation_loop(self, wait_time):
        self.button_show_answer.pack_forget()  # Hide the answer button initially
        
        for romanji, char in self.characters_to_display:
            play_beep()
            self.label_display.config(text=romanji)  # Show only Romanji
            self.start_countdown(wait_time)  # Start the countdown timer
            time.sleep(wait_time)  # Wait dynamically set time

        # Show the "Show Answer" button at the end
        self.label_display.config(text="Time's up!")
        self.button_show_answer.pack()

    def start_countdown(self, wait_time):
        def update_countdown(seconds_left):
            if seconds_left > 0:
                self.label_timer.config(text=f"Time left: {seconds_left} seconds")
                self.root.after(1000, update_countdown, seconds_left - 1)
            else:
                self.label_timer.config(text="Time's up!")

        # Add or update a timer label
        if not hasattr(self, 'label_timer'):
            self.label_timer = tk.Label(self.root, text="", font=("Arial", 12), fg="blue")
            self.label_timer.pack(pady=5, after=self.label_error)  # Place below the error/status label
        
        update_countdown(wait_time)
    
    def show_answer(self):
        # Clear previous answers
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Define the font for larger text
        answer_font = ("Arial", 16, "bold")  # Adjust size and style as needed

        # Display answers in columns of 10 items each
        col = 0
        row = 0
        for idx, (romanji, char) in enumerate(self.characters_to_display, start=1):
            tk.Label(
                self.scrollable_frame,
                text=f"{romanji}: {char}",
                font=answer_font,  # Apply the larger font here
                anchor="w"
            ).grid(row=row, column=col, sticky="w", padx=5, pady=2)  # Add padding for spacing
            if idx % 20 == 0:  # Move to the next column after 10 items
                col += 1
                row = 0
            else:
                row += 1

# Run the GUI application
if __name__ == "__main__":
    root = tk.Tk()
    app = DictationApp(root)
    root.mainloop()