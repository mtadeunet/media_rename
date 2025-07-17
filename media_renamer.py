from config import SearchType
from name_resolver import NameResolver
import os
import filecmp


default_directory_config = { "search": SearchType.Exif, "directory_pattern": "%Y/%Y-%m-%d", "file_pattern": "%Y%m%d_%H%M%S_%f" }

class MediaRenamer:
    def __init__(self, simulate: bool = True, create_sub_directories: bool = False, special_directories: dict = {}, log_callback: callable = print):
        self.simulate = simulate
        self.create_sub_directories = create_sub_directories
        self.special_directories = special_directories
        self.log = log_callback


    def process_file(self, file_path: str, working_directory: str):
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

            try:
                resolver.process()
            except Exception as e:
                self.log(f"ERROR: {e}")

            target = None

            if resolver.success:
                if self.create_sub_directories:
                    target = os.path.join(working_directory, resolver.suggested_directory, resolver.name)
                else:
                    target = os.path.join(working_directory, resolver.name)
            else:
                self.log("INVALID: " + file_path)
                target = os.path.join(working_directory, "invalid", os.path.basename(file_path))

            # if the source and target are the same, skip...we're fine
            if file_path == target:
                self.log("SKIP: " + target)
                return

            # from here, the source and the target are in different locations
            
            if os.path.exists(target):
                # deal with duplicate file
                if filecmp.cmp(file_path, target):
                    # it's exactly the same file...delete the source
                    self.log(f"DELETE: {file_path}")

                    not self.simulate and os.remove(file_path)
                    return
                else:
                    # it's a duplicate filename but the file contents are different...move to "duplicates" dir
                    target = os.path.join(working_directory, "duplicates", os.path.basename(target))
                    self.log("DUPLICATE: " + target)

            not self.simulate and os.makedirs(os.path.dirname(target), exist_ok=True)
            self.log(f"RENAME: {file_path} -> {target}")
            not self.simulate and os.rename(file_path, target)

        except Exception as e:
            self.log(f"ERROR: {e}")
            return

    
    def process_directory(self, current_directory: str, working_directory: str, recursive: bool = False):
        for file_path in os.listdir(current_directory):
            full_path = os.path.join(current_directory, file_path)

            if os.path.isfile(full_path):
                self.process_file(full_path, working_directory)
            elif recursive and file_path not in ["invalid", "duplicates"]:
                self.process_directory(full_path, working_directory, recursive)
