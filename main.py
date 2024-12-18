import os
import json
import logging
import argparse
from datetime import datetime
import googleapiclient.discovery
import googleapiclient.errors
from youtube_transcript_api import YouTubeTranscriptApi
from youtubeai import YoutubeChannelLm

class SubtitleExtractor:
    def __init__(self, channel_id, api_key):
        self.channel_id = channel_id

        # API keys
        self.api_key = api_key
        
        self.videos = []
        self.loading = False

        # Defines
        self.srt = None
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename=os.path.join('data', "info-{}-{}.log".format(datetime.now().date().strftime("%Y-%m-%d"), datetime.now().time().strftime("%H-%M-%S"))), level=logging.INFO)
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=self.api_key)

        # Executions
        self.create_dirs([
            ["data"],
            ["data", channel_id],
            ["data", channel_id, "subtitles"],
            ["data", channel_id, "videos"],
            ['data', channel_id, 'vectorstore']
        ])

        # logging
        self.logger.info("Initialized")

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
                self.logger.info(f"Created directory: {dir_path}")
            else:
                self.logger.info(f"Directory already exists: {dir_path}")

    def get_videos_list(self):
        next_page_token = None

        # checks
        if not self.youtube: return

        self.loading = True
        request = self.youtube.channels().list(
            part='contentDetails',
            id=self.channel_id
        )

        response = request.execute()

        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        while True:
            request = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )

            response = request.execute()

            for item in response['items']:
                video_data = {
                    'id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'publishedAt': item['snippet']['publishedAt']
                }
                self.videos.append(video_data)
            
            next_page_token = response.get('nextPageToken')

            if not next_page_token:
                break

        self.loading = False


    def dump_video_data(self, filename='videos.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.videos, f, ensure_ascii=False, indent=4)
        
        self.logger.info('JSON data dumped success.')


    def get_video_subtitle(self, video_id):
        self.loading = True
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            language_code = None
            for transcript in transcript_list:
                language_code = transcript.language_code
                break
            if not language_code: raise Exception("language code not found")
            transcript = transcript_list.find_transcript([language_code])
            translated_transcript = transcript.translate('en')
            self.srt = translated_transcript.fetch()
                
        except Exception as e:
            self.logger.error("Error during get subtitle for video {}".format(video_id))
            self.logger.error(f"Error: {e}")

        if not self.srt: return
        file_path = os.path.join('data', self.channel_id, "subtitles", f"{video_id}.subtitles.txt")
        
        for line in self.srt:
            with open(file_path, 'a', encoding="utf-8") as f:
                f.write(f"{line['text']}\n")
        self.loading = False

    
    def execute(self):
        self.get_videos_list()
        self.dump_video_data(os.path.join("data", f"{self.channel_id}.videos.json"))
        for video in self.videos:
            self.logger.debug("Subtitle for video id: {}".format(video['id']))
            self.get_video_subtitle(video['id'])
        self.logger.info("Execution completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Ai chatbot for your own youtube channel.")

    parser.add_argument("-e", "--extract-data", action="store_true", help="Extract youtube subtitles data and store them.")
    parser.add_argument('-r', '--run-model', action="store_true", help="Run your ai model after extracting data.")

    parser.add_argument('--channel-id', type=str, help='Provide your channel id, ex:- UCwpr_shE_KEjoOVFqbwGYQ', required=True)
    parser.add_argument('--api-key', type=str, help='youtube api key to extract the list of channel video. (Any public api will be valid not the channel specific one.)', required=True)

    args = parser.parse_args()

    if args.extract_data:
        print(f"Extracting data for channel {args.channel_id} ...")
        subtitle_extractor = SubtitleExtractor(args.channel_id, args.api_key)
        subtitle_extractor.execute()
    elif args.run_model:
        print(f"Training and running your ai bot.")
        youtube_channelml = YoutubeChannelLm(args.channel_id, args.api_key)
        youtube_channelml.run()
    else:
        parser.print_help()
