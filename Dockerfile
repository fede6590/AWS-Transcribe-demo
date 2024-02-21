FROM python:3.11-slim-bookworm

RUN useradd -m dev

WORKDIR /app

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER dev

COPY requirements.txt .
COPY transcribe.py .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "transcribe.py"]
