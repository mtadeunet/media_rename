from dotenv import load_dotenv
from config import config
from tk_dialog import PathPickerApp
import tkinter as tk

# Load environment variables
load_dotenv()

# renamer = MediaRenamer(simulate=False, rename_only=True, special_directories=config["special_directories"])

# for file_path in config["file_paths"]:
#     renamer.rename_file(file_path)



# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = PathPickerApp(root)
    root.mainloop()
