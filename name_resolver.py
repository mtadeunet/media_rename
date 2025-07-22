import exiftool
from datetime import datetime
import base64
import openai
import os
from config import SearchType

class NameResolver:
    def __init__(self, file_path: str, config: dict):
        self.file_path = file_path
        self.date = None
        self.name = None
        self.suggested_directory = None
        self.config = config
        self.metadata = None

    @property
    def success(self):
        return self.date is not None and self.name is not None and self.suggested_directory is not None


    def parse_date(self, date_str: str, format: str = None) -> datetime:
        if not format:
            format = "%Y:%m:%d %H:%M:%S.%f" if "." in date_str else "%Y:%m:%d %H:%M:%S"

            if "+" in date_str:
                date_str = date_str[::-1].replace(":", "", 1)[::-1]
                format = f"{format}%z"

        return datetime.strptime(date_str, format)


    def format_name(self, date: datetime):
        pattern = self.config["file_pattern"]
        if "%f" in pattern:
            offset = date.strftime("%f")[:-3]
            pattern = pattern.replace("%f", offset)

        self.name = self.date.strftime(pattern) + os.path.splitext(self.file_path)[1]
        self.suggested_directory = self.date.strftime(self.config["directory_pattern"])


    def process(self):
        if self.config["search"] == SearchType.Image:
            self.from_image()
        elif self.config["search"] == SearchType.FileSystem:
            self.from_creation_date()
        else:
            self.from_exif()

    def from_image(self) -> str:
        # Convert image to base64
        with open(self.file_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Use GPT-4 Vision Preview
        analysis = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a date extraction assistant. You are very good at analyzing images and extracting date information from them."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and extract any date information visible in the image. Return the date in the format YYYYMMDD_HHMMSS with no other text. If no date is visible, return 'No date found'."
                        },
                        {
                            "type": "image_url",
                            "image_url": { "url": f"data:image/jpeg;base64,{image_data}" }
                        }
                    ]
                }
            ]
        )
        
        date_str = analysis.choices[0].message.content.strip()
        
        if date_str == "No date found":
            raise Exception("No date found")
            
        self.date = self.parse_date(date_str, "%Y%m%d_%H%M%S")
        self.format_name(self.date)


    def from_exif(self):
        self.metadata = exiftool.ExifToolHelper().get_metadata(self.file_path)

        if len(self.metadata) > 1:
            raise ValueError(f"ERROR: Multiple metadata found for file: {self.file_path}")

        metadata = self.metadata[0]

        if metadata["File:FileType"] in ["JPEG", "JPG", "PNG"]:
            if "Composite:SubSecDateTimeOriginal" in metadata:
                self.date = self.parse_date(metadata["Composite:SubSecDateTimeOriginal"])
            elif "EXIF:DateTimeOriginal" in metadata:
                self.date = self.parse_date(metadata["EXIF:DateTimeOriginal"])
            else:
                raise Exception(f"No date found in EXIF metadata {self.file_path}")
            
        elif metadata["File:FileType"] in ["MP4", "MOV"]:
            self.date = self.parse_date(metadata["QuickTime:CreateDate"])
        else:
            raise Exception(f"Unsupported file type: {metadata['File:FileType']} {self.file_path}")
        
        self.format_name(self.date)


    def from_creation_date(self):
        self.metadata = exiftool.ExifToolHelper().get_metadata(self.file_path)

        if len(self.metadata) > 1:
            raise ValueError(f"ERROR: Multiple metadata found for file: {self.file_path}")

        metadata = self.metadata[0]

        date = metadata["File:FileModifyDate"]
        
        self.date = self.parse_date(date)
        self.format_name(self.date)
