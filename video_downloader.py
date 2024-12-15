import os
import json
import logging
from datetime import datetime
from yt_dlp import YoutubeDL

class VideoDownloader:
    def __init__(self, channel_id):
        # Constants
        self.channel_id = channel_id
        self.videos = None

        self.create_dirs([["data"]])

        if not os.path.exists(os.path.join("data", self.channel_id)):
            raise FileNotFoundError("Data directory not found.")
        
        self.create_dirs([["data", self.channel_id, "logs"]])

        # Initializations
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename=os.path.join(
            'data',
            self.channel_id,
            'logs',
            "downloader-{}-{}.log".format(
                datetime.now().date().strftime("%Y-%m-%d"),
                datetime.now().time().strftime("%H-%M-%S")
            )
        ), level=logging.INFO)


    def create_dirs(self, dirs_structure):
        """
        Create directories based on the nested list structure.
        
        Args:
            dirs_structure (list): List of directory paths represented as nested lists.
        """
        for path_parts in dirs_structure:
            # Construct the full path
            dir_path = os.path.join(*path_parts)
            # Check if the directory exists, if not, create it
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logging.debug(f"Created directory: {dir_path}")
            else:
                logging.debug(f"Directory already exists: {dir_path}")


    def load_videos_from_file(self):
        try:
            filepath = os.path.join("data", f"{self.channel_id}.videos.json")
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.videos = data
        except Exception as e:
            self.logger.error("Error during loading videos:")
            self.logger.error(e)
    
    def download_video(self, video_id):
        try:
            self.logger.info(f"Downloading video {video_id} ...")
            url = f"https://youtube.com/?v={video_id}"

            ydl_options =  {
                'format': 'bestvideo[height=480]',  # Specify 480p
                'outtmpl': 'data/%(channel_id)s/videos/%(id)s.%(ext)s',  # Output file name
            }
            with YoutubeDL(ydl_options) as  ydl:
                ydl.download([url])
            # (os.path.join("data", self.channel_id, "videos"), filename_prefix=self.video_id)
            self.logger.info(f"Video downloaded {video_id} ...")

        except Exception as e:
            self.logger.error("Error during downloading video:")
            self.logger.error(e)

    def execute(self):
        self.load_videos_from_file()
        for video in self.videos:
            self.download_video(video['id'])
            break

video_downloader = VideoDownloader("UCwpr_shE_KEjoOVFqbwaGYQ")
video_downloader.execute()