FROM python:3.11-slim-bookworm

# RUN useradd -m dev

WORKDIR /app

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# USER dev

COPY split-file.py .
COPY video.mp4 .

RUN mkdir stream
RUN chmod 777 stream

CMD ["python", "split-file.py"]