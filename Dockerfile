FROM python:3

WORKDIR /app

COPY requirements.txt ./
COPY main.py ./
COPY video_downloader.py ./

RUN mkdir -p /app/data

RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app/data"]

CMD ["python", "video_downloader.py"]