FROM python:3.11-slim-bookworm

RUN useradd -m dev

WORKDIR /app

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    # libjack-jackd2-dev \
    # portaudio19-dev \
    # python3-dev \
    # build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /app/temp && chown dev:dev /app/temp

USER dev

COPY requirements.txt .
COPY ts_transcribe.py .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "ts_transcribe.py"]
