from enum import Enum

SearchType = Enum("SearchType", "Exif Image FileSystem")

config = {
    "special_directories": {
        "/some/path": { "search": SearchType.Image, "directory_pattern": "%Y-%Y-%m-%d", "file_pattern": "%Y%m%d_%H%M%S_%f" },
    },
}