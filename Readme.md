# Youtube AI
RUN /app/main.py
```shell
docker build -t python-youtube-ai .
docker run -it -v youtube_ai_data:/app/data -e YOUTUBE_API_KEY=api-key python-youtube-ai
```