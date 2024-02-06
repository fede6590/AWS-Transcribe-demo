import asyncio
import subprocess
import boto3
import os

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent


SAMPLE_RATE = 16000
CHANNEL_NUMS = 1
CHUNK_SIZE = 4096
REGION = "us-east-1"


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)


async def basic_transcribe():
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )
    _ = session.client('transcribe')  # Test for IAM role availability
    client = TranscribeStreamingClient(region=REGION)

    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=SAMPLE_RATE,
        media_encoding="pcm",
    )

    async def write_chunks():
        # mediapackage_url = "https://8572e342e3eeb5c4.mediapackage.us-east-1.amazonaws.com/out/v1/09a97e8e9e044b6d9c27307e2b5a1383/index.mpd"
        # mediapackage_url = 'https://8572e342e3eeb5c4.mediapackage.us-east-1.amazonaws.com/out/v1/8291e48e06064437b36057201626431d/index.m3u8'
        mediapackage_url = 'stream/video.m3u8'

        command = [
            'ffmpeg',
            '-i', mediapackage_url,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', str(SAMPLE_RATE),
            '-ac', str(CHANNEL_NUMS),
            '-f', 'wav',
            '-'
        ]
        ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE)

        try:
            loop = asyncio.get_running_loop()
            while True:
                chunk = await loop.run_in_executor(None,
                                                   ffmpeg_process.stdout.read,
                                                   CHUNK_SIZE
                                                   )
                if not chunk:
                    break
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
        finally:
            ffmpeg_process.stdout.close()
            ffmpeg_process.terminate()
            await ffmpeg_process.wait()

        await stream.input_stream.end_stream()

    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(), handler.handle_events())


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(basic_transcribe())
    except Exception as e:
        print(f"An error occurred: {e}")
