import exiftool
from datetime import datetime, timedelta
import base64
import openai
import os
from config import SearchType
from pdf2image import convert_from_path
from io import BytesIO
from zoneinfo import ZoneInfo

class NameResolver:
    def __init__(self, file_path: str, config: dict, timezone: str = 'UTC', apply_dst: bool = True):
        self.file_path = file_path
        self.date = None
        self.name = None
        self.suggested_directory = None
        self.config = config
        self.metadata = None
        self.apply_dst = apply_dst

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
        """Extract dates from images or PDFs using GPT-4 Vision"""
        try:
            if self.file_path.lower().endswith(".pdf"):
                # Convert PDF to images
                images = convert_from_path(self.file_path)

                buffered = BytesIO()
                images[0].save(buffered, format="JPEG")
                image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            else:
                # For non-PDF files, process as image
                with open(self.file_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')

            analysis = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """
You are a date extraction assistant. 
You are very good at analyzing images and extracting date information from them. 

IMPORTANT: Focus on the current year 2025. Be extra careful to distinguish between 2023 and 2025 and be very careful distinguishing 7 and 1.

Instructions:
1. First analyze the image orientation. The image might be rotated or upside down.
2. Automatically rotate the image to the correct orientation before analyzing.
3. Dates are usually on top of the image, before any description or details.
4. Look for dates near fields labeled 'Data', 'Data e Hora', or 'Date'.
5. The dates are usually in one of these formats: YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY.
6. Time is usually in the format HH:MM or HH:MM:SS.
7. Always double check the dates to make sure they are correct. This needs to be very precise.
8. If you can't find a date in the first orientation, try rotating the image 90 degrees and look again.
9. If no date is visible after trying all orientations, return 'No date found'.
10. The date can never be bigger than the date when the image was made (in the exif metadata).
11. If no time is found, assume 00:00:00.

Return the date in the format YYYYMMDD_HHMMSS with no other text."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """
Analyze this image and extract any date information visible in the image. If the image is rotated, rotate it to the correct orientation first. 

IMPORTANT: Pay extra attention to distinguish between 2023 and 2025. If you see a date that looks like 2023, double check if it might actually be 2025.

Return the date in the format YYYYMMDD_HHMMSS with no other text. If no date is visible, return 'No date found'."""
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
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None


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
            if "QuickTime:CreationDate" in metadata:                
                # This already contemplates daylight savings...if exists
                self.date: datetime = self.parse_date(metadata["QuickTime:CreationDate"])
            else:
                self.date: datetime = self.parse_date(metadata["QuickTime:CreateDate"])
                if self.apply_dst:
                    self.date = self.date + timedelta(hours=1)
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
