FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
COPY main.py ./

RUN mkdir -p /app/data

RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app/data"]

CMD ["python", "main.py"]