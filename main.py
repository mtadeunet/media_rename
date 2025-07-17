from dotenv import load_dotenv
from media_renamer import MediaRenamer
from config import config

# Load environment variables
load_dotenv()

renamer = MediaRenamer(simulate=False, rename_only=True, special_directories=config["special_directories"])

for file_path in config["file_paths"]:
    renamer.rename_file(file_path)


