from config import SearchType
from name_resolver import NameResolver
import os
import filecmp


default_directory_config = { "search": SearchType.Exif, "directory_pattern": "%Y/%Y-%m-%d", "file_pattern": "%Y%m%d_%H%M%S_%f" }

class MediaRenamer:
    def __init__(self, simulate: bool = True, create_sub_directories: bool = False, special_directories: dict = {}, log_callback: callable = print, delete_empty_directories: bool = False, invalid_as_file_date: bool = False):
        self.simulate = simulate
        self.create_sub_directories = create_sub_directories
        self.special_directories = special_directories
        self.log = log_callback
        self.delete_empty_directories = delete_empty_directories
        self.invalid_as_file_date = invalid_as_file_date

        self.renamed_files = []
        self.deleted_files = []
        self.invalid_files = []
        self.duplicate_files = []
        self.skipped_files = []
        self.delete_directories = []


    def process_file(self, entry: os.PathLike[str], working_directory: os.PathLike[str]):
        try:
            if not entry.is_file():
                self.log(f"ERROR: Not a file: {entry}")
                return
            if not os.path.exists(entry):
                self.log("ERROR: The file does not exist: " + entry)
                return
            
            directory_config = default_directory_config

            for item, value in self.special_directories.items():
                if entry.path.startswith(item):
                    directory_config = value
                    break

            resolver = NameResolver(entry.path, directory_config)

            try:
                resolver.process()
            except Exception as e:
                self.log(f"ERROR: {e}")

            target = None

            if not resolver.success:
                if self.invalid_as_file_date:
                    resolver.from_creation_date()
                else:
                    self.log(f"INVALID: {entry.path} -> {target}")
                    self.invalid_files.append(entry.path)
                    target = os.path.join(working_directory, "invalid", os.path.basename(entry.path))

            if resolver.success:
                if self.create_sub_directories:
                    target = os.path.join(working_directory, resolver.suggested_directory, resolver.name)
                else:
                    target = os.path.join(working_directory, resolver.name)

            # if the source and target are the same, skip...we're fine
            if entry.path == target:
                self.log("SKIP: " + entry.path)
                self.skipped_files.append(entry.path)
                return

            # from here, the source and the target are in different locations
            
            if os.path.exists(target):
                # deal with duplicate file
                if filecmp.cmp(entry.path, target):
                    # it's exactly the same file...delete the source
                    self.log(f"DELETE: {entry.path}")
                    self.deleted_files.append(entry.path)

                    not self.simulate and os.remove(entry.path)
                    return
                else:
                    # it's a duplicate filename but the file contents are different...move to "duplicates" dir
                    target = os.path.join(working_directory, "duplicates", os.path.basename(target))
                    self.log(f"DUPLICATE: {entry.path} = {target}")
                    self.duplicate_files.append(target)

            not self.simulate and os.makedirs(os.path.dirname(target), exist_ok=True)
            self.log(f"RENAME: {os.path.relpath(entry.path, working_directory)} -> {os.path.relpath(target, working_directory)}")
            not self.simulate and os.rename(entry.path, target)
            self.renamed_files.append(entry.path)

        except Exception as e:
            self.log(f"ERROR: {e}")
            return

    
    def process_directory(self, current_directory: os.PathLike[str], working_directory: os.PathLike[str], recursive: bool = False):
        with os.scandir(current_directory) as entries:
            for entry in entries:
                if entry.is_file():
                    self.process_file(entry, working_directory)
                elif recursive and entry.name not in ["invalid", "duplicates"]:
                    self.process_directory(entry, working_directory, recursive)
                    
                    if self.delete_empty_directories and not any(os.scandir(entry)):
                        self.delete_directories.append(entry)
                        os.rmdir(entry)
        

        self.log("Renamed files: " + str(len(self.renamed_files)))
        self.log("Deleted files: " + str(len(self.deleted_files)))
        self.log("Invalid files: " + str(len(self.invalid_files)))
        self.log("Duplicate files: " + str(len(self.duplicate_files)))
        self.log("Skipped files: " + str(len(self.skipped_files)))
        self.log("Deleted directories: " + str(len(self.delete_directories)))
        self.log("Total files: " + str(len(self.renamed_files) + len(self.deleted_files) + len(self.invalid_files) + len(self.duplicate_files) + len(self.skipped_files)))
