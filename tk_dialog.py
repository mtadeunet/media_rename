from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading
from media_renamer import MediaRenamer
from config import config


class PathPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Path Picker with Logging")
        self.root.geometry("600x400")
        self.root.option_add("*Font", ("Noto Sans", 10))

        self.create_widgets()

    def create_widgets(self):
        # Top frame
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="x", expand=False)

        # Path entry and browse
        self.path_entry = ttk.Entry(frame, width=50)
        self.path_entry.grid(row=0, column=0, padx=(0, 5), pady=(0, 10), sticky="ew")

        browse_button = ttk.Button(frame, text="Browse", command=self.browse_path)
        browse_button.grid(row=0, column=1, pady=(0, 10))

        # Checkboxes
        self.create_subdirs_var = tk.BooleanVar(value=False)
        self.simulate_var = tk.BooleanVar(value=False)
        self.recursive_var = tk.BooleanVar(value=False)
        self.remove_empty_dirs_var = tk.BooleanVar(value=False)
        self.invalid_as_file_date_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            frame,
            text="Create sub-directories",
            variable=self.create_subdirs_var
        ).grid(row=1, column=0, columnspan=2, sticky="w")

        ttk.Checkbutton(
            frame,
            text="Simulate",
            variable=self.simulate_var
        ).grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Checkbutton(
            frame,
            text="Recursive",
            variable=self.recursive_var
        ).grid(row=3, column=0, columnspan=2, sticky="w")

        ttk.Checkbutton(
            frame,
            text="Remove empty directories",
            variable=self.remove_empty_dirs_var
        ).grid(row=4, column=0, columnspan=2, sticky="w")

        ttk.Checkbutton(
            frame,
            text="Use file creation date for invalid files",
            variable=self.invalid_as_file_date_var
        ).grid(row=5, column=0, columnspan=2, sticky="w")

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        ttk.Button(button_frame, text="Print State", command=self.print_state).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Process", command=self.process).pack(side="left")

        frame.columnconfigure(0, weight=1)

        # Log output
        log_frame = ttk.LabelFrame(self.root, text="Log Output", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.log_box = tk.Text(log_frame, wrap="word", height=8, state="disabled")
        self.log_box.pack(fill="both", expand=True)

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.log(f"Path selected: {path}")

    def print_state(self):
        self.log("-----")
        self.log(f"Selected Path: {self.path_entry.get()}")
        self.log(f"Create sub-directories: {self.create_subdirs_var.get()}")
        self.log(f"Simulate: {self.simulate_var.get()}")
        self.log(f"Recursive: {self.recursive_var.get()}")
        self.log(f"Remove empty directories: {self.remove_empty_dirs_var.get()}")
        self.log(f"Use file creation date for invalid files: {self.invalid_as_file_date_var.get()}")

    def process(self):
        # Run the real work in a background thread
        threading.Thread(target=self.run_process).start()

    def run_process(self):
        self.log("Processing started...")
        try:
            renamer = MediaRenamer(
                simulate=self.simulate_var.get(), 
                create_sub_directories=self.create_subdirs_var.get(), 
                special_directories=config["special_directories"], 
                log_callback=self.log,
                delete_empty_directories=self.remove_empty_dirs_var.get(),
                invalid_as_file_date=self.invalid_as_file_date_var.get()
            )
            
            # Process the directory
            renamer.process_directory(
                Path(self.path_entry.get()), 
                Path(self.path_entry.get()), 
                recursive=self.recursive_var.get()
            )
        except Exception as e:
            self.log(f"ERROR: {e}")
        self.log("Processing finished.")

    def log(self, message):
        print(message)
        self.log_box.configure(state='normal')
        self.log_box.insert(tk.END, message + '\n')
        self.log_box.see(tk.END)
        self.log_box.configure(state='disabled')
        self.root.update_idletasks()

