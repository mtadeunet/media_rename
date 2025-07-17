from enum import Enum

SearchType = Enum("SearchType", "Exif Image FileSystem")

config = {
    "special_directories": {
    "/media/miguel/Nextcloud/live/Projects/Funny Planet/Facturas/": { "search": SearchType.Image, "directory_pattern": "%Y-%m-%d", "file_pattern": "%Y%m%d_%H%M%S_%f" },
    "/media/miguel/Nextcloud/live/InstantUpload/Facturas/": { "search": SearchType.Image, "directory_pattern": "%Y-%m-%d", "file_pattern": "%Y%m%d_%H%M%S_%f" },
    "/media/miguel/Nextcloud/live/InstantUpload/Tumblr/": { "search": SearchType.FileSystem, "directory_pattern": "", "file_pattern": "%Y%m%d_%H%M%S" }
    },
    "file_paths": [
        "/media/miguel/Nextcloud/live/InstantUpload/Camera/IMG20250618165911.jpg", # android jpeg
        "/media/miguel/Nextcloud/live/InstantUpload/Euphoria/2025-07-01/20250701_180122000.mp4", # android mp4
        "/media/miguel/Nextcloud/live/Collection/Euphoria/2023/2023-05-01 - Praia/20230501_125123_054.jpg", # iphone jpeg
        "/media/miguel/Nextcloud/live/Collection/Euphoria/2022/2022-06-04 - Passeio na Adiça/20220604_152419.mov", # iphone mov
        "/media/miguel/Nextcloud/live/Collection/Euphoria/2022/2022-09 - Férias/2022-09-21/20220921_230546.mp4", # dji mp4
        "/media/miguel/Nextcloud/live/InstantUpload/Tumblr/2025-06-02/Tumblr_l_876371776198045.jpg", # tumblr jpeg
        "/media/miguel/Nextcloud/live/InstantUpload/Euphoria/2025-07-16 14.20.48/IMG-20250714-WA0003.jpg", # whatsapp jpeg
        "/media/miguel/Nextcloud/live/Collection/Euphoria/2014/2014-06-23 - Telemóvel/1062375_10204198971952532_1167579156_n.jpg", # old jpeg 1
        "/media/miguel/Nextcloud/live/Collection/Euphoria/2014/2014-06-23 - Telemóvel/10603069_10204518720906056_699270818_n.jpg", # old jpeg 2
        "/media/miguel/Nextcloud/live/Projects/Funny Planet/Facturas/2025/01/20250103_113019.jpg" # factura 1
    ]
}