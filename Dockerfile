FROM python:3

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app/data"]

EXPOSE 7860

RUN python main.py -e --channel-id UCf9T51_FmMlfhiGpoes0yFA --api-key AIzaSyADIgPArEEIgcvfpEBz4GkgxG6xLSz5YO4

CMD ["python", "app.py"]