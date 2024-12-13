import os
import json
import googleapiclient.discovery
import googleapiclient.errors
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

class YoutubeAi:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.languages = ['hi', 'en']

        # API keys
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.videos = []
        self.loading = False

        # Defines
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=self.api_key)
        self.srt = None

        # Executions
        os.mkdir(os.path.join('data', self.channel_id))

    def get_videos_list(self):
        next_page_token = None

        # checks
        if not self.youtube: return

        self.loading = True
        while True:
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                maxResults=100,  # Maximum results per page
                pageToken=next_page_token
            )

            response = request.execute()

            for item in response['items']:
                video_id = item['id'].get('videoId')
                if video_id:
                    video_title = item['snippet']['title']
                    video_publish_time = item['snippet']['publishedAt']
                    self.videos.append({
                        'id': video_id,
                        'title': video_title,
                        'publishedAt': video_publish_time
                    })
            
            next_page_token = response.get('nextPageToken')

            if not next_page_token:
                break

        self.loading = False


    def dump_video_data(self, filename='videos.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.videos, f, ensure_ascii=False, indent=4)
        print('JSON data dumped success.')


    def get_video_subtitle(self, video_id):
        self.loading = True
        try:
            self.srt = YouTubeTranscriptApi.get_transcript(video_id, languages=self.languages)
        except NoTranscriptFound:
            pass

        if not self.srt: return
        
        for line in self.srt:
            "/data/channel_id/video_id.subtitle.txt"
            with open(os.path.join('data', self.channel_id, f"{video_id}.subtitle.txt"), 'a') as f:
                f.write(f"{line['text']}\n")
        self.loading = False

    
    def execute(self):
        self.get_videos_list()
        self.dump_video_data(os.path.join("data", f"{self.channel_id}.videos.json"))
        for video in self.videos:
            self.get_video_subtitle(video.id)
        print("Execution completed.")

youtubeai = YoutubeAi('UCwpr_shE_KEjoOVFqbwaGYQ')
