from config import SearchType
from name_resolver import NameResolver
import os


default_directory_config = { "search": SearchType.Exif, "directory_pattern": "%Y/%Y-%m-%d", "file_pattern": "%Y%m%d_%H%M%S_%f" }

class MediaRenamer:
    def __init__(self, simulate: bool = True, rename_only: bool = False, special_directories: dict = {}, log_callback: callable = print):
        self.simulate = simulate
        self.rename_only = rename_only
        self.special_directories = special_directories
        self.log = log_callback



    def rename_file(self, file_path: str):
        try:
            if not os.path.exists(file_path):
                self.log("ERROR: The file does not exist: " + file_path)
                return
            
            directory_config = default_directory_config

            for item, value in self.special_directories.items():
                if file_path.startswith(item):
                    directory_config = value
                    break

            resolver = NameResolver(file_path, directory_config)

            if self.rename_only:
                self.log(f"{file_path} -> {resolver.name}")
            else:
                self.log(f"{file_path} -> {resolver.name} ({resolver.suggested_directory})")

            if self.simulate:
                return

            if not resolver.success:
                raise Exception("The date search was not successful for file: " + file_path)

            # if not self.rename_only:

            # if not self.rename_only:
                # os.rename(file_path, resolver.get_renamed_path())

        except Exception as e:
            self.log(f"ERROR: {e}")
            return

    
    def rename_file_in_directory(self, directory: str, recursive: bool = False):
        for file_path in os.listdir(directory):
            full_path = os.path.join(directory, file_path)

            if os.path.isfile(full_path):
                self.rename_file(full_path)
            elif recursive and file_path not in ["invalid", "duplicates"]:
                self.rename_file_in_directory(full_path)
