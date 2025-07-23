from config import SearchType
from name_resolver import NameResolver
import os
import filecmp
from pathlib import Path


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


    def process_file(self, entry: Path, working_directory: Path):
        try:
            if not entry.is_file():
                self.log(f"ERROR: Not a file: {entry}")
                return
            if not os.path.exists(entry):
                self.log("ERROR: The file does not exist: " + entry)
                return
            
            directory_config = default_directory_config

            for item, value in self.special_directories.items():
                if entry.is_relative_to(Path(item)):
                    directory_config = value
                    break

            resolver = NameResolver(entry.as_posix(), directory_config)

            try:
                resolver.process()
            except Exception as e:
                self.log(f"ERROR: {e}")

            target = None

            if not resolver.success:
                if self.invalid_as_file_date:
                    resolver.from_creation_date()
                else:
                    self.log(f"INVALID: {entry.as_posix()} -> {target}")
                    self.invalid_files.append(entry.as_posix())
                    target = os.path.join(working_directory, "invalid", os.path.basename(entry.as_posix()))

            if resolver.success:
                if self.create_sub_directories:
                    target = os.path.join(working_directory, resolver.suggested_directory, resolver.name)
                else:
                    target = os.path.join(working_directory, resolver.name)

            # if the source and target are the same, skip...we're fine
            if entry.as_posix() == target:
                self.log("SKIP: " + entry.as_posix())
                self.skipped_files.append(entry.as_posix())
                return

            # from here, the source and the target are in different locations
            
            if os.path.exists(target):
                # deal with duplicate file
                if filecmp.cmp(entry.as_posix(), target):
                    # it's exactly the same file...delete the source
                    self.log(f"DELETE: {entry.as_posix()}")
                    self.deleted_files.append(entry.as_posix())

                    not self.simulate and os.remove(entry.as_posix())
                    return
                else:
                    # it's a duplicate filename but the file contents are different...move to "duplicates" dir
                    # calculate hash of file
                    hash = hashlib.md5(open(entry.as_posix(), "rb").read()).hexdigest()
                    target_filename, target_extension = os.path.splitext(os.path.basename(target))
                    target = os.path.join(working_directory, "duplicates", f"{target_filename}_{hash}.{target_extension}")
                    self.log(f"DUPLICATE: {entry.as_posix()} = {target}")
                    self.duplicate_files.append(target)

            not self.simulate and os.makedirs(os.path.dirname(target), exist_ok=True)
            self.log(f"RENAME: {os.path.relpath(entry.as_posix(), working_directory)} -> {os.path.relpath(target, working_directory)}")
            not self.simulate and os.rename(entry.as_posix(), target)
            self.renamed_files.append(entry.as_posix())

        except Exception as e:
            self.log(f"ERROR: {e}")
            return

    
    def process_directory(self, current_directory: os.PathLike[str], working_directory: os.PathLike[str], recursive: bool = False):
        # Collect all files and directories first
        all_files = []
        all_directories = []

        # Walk through the directory tree
        for root, dirs, files in os.walk(current_directory):
            # Skip invalid and duplicates directories
            if "invalid" in root or "duplicates" in root:
                continue
                
            # Collect files
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
                
            # Collect directories
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                all_directories.append(dir_path)

        # Process files one by one
        for file_path in all_files:
            try:
                entry = Path(file_path)
                self.process_file(entry, working_directory)
            except Exception as e:
                self.log(f"ERROR processing file {file_path}: {e}")

        # Process directories for deletion if requested
        if self.delete_empty_directories:
            for dir_path in reversed(all_directories):  # Process in reverse order
                try:
                    if not os.listdir(dir_path):
                        self.delete_directories.append(dir_path)
                        if not self.simulate:
                            os.rmdir(dir_path)
                except Exception as e:
                    self.log(f"ERROR deleting empty directory {dir_path}: {e}")

        # Log statistics
        self.log("Renamed files: " + str(len(self.renamed_files)))
        self.log("Deleted files: " + str(len(self.deleted_files)))
        self.log("Invalid files: " + str(len(self.invalid_files)))
        self.log("Duplicate files: " + str(len(self.duplicate_files)))
        self.log("Skipped files: " + str(len(self.skipped_files)))
        self.log("Deleted directories: " + str(len(self.delete_directories)))
        self.log("Total files: " + str(len(self.renamed_files) + len(self.deleted_files) + len(self.invalid_files) + len(self.duplicate_files) + len(self.skipped_files)))
