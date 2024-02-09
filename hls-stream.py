import asyncio
import subprocess
import boto3
import os

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

REGION = "us-east-1"
SOURCE = os.environ.get('SOURCE')

LOGLEVEL = os.environ.get('LOGLEVEL')
if LOGLEVEL is None:
    LOGLEVEL = 'warning'

VERBOSE = os.environ.get('VERBOSE')
if VERBOSE is None:
    VERBOSE = 'error'

CHUNK_DURATION_MS = 100  # Set between 50 and 200ms for real-time applications
SAMPLE_RATE = 16000
CHANNEL_NUMS = 1
BITS_PER_SAMPLE = 16


def chunk_size(chunk_duration_ms):
    bytes_per_sample = BITS_PER_SAMPLE // 8
    return int(chunk_duration_ms / 1000 * SAMPLE_RATE * bytes_per_sample)


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)


async def basic_transcribe():
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

    if (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) is not None:
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
        enable_partial_results_stabilization=True,
    )

    async def write_chunks():
        command = [
            'ffmpeg',
            '-i', SOURCE,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', str(SAMPLE_RATE),
            '-ac', str(CHANNEL_NUMS),
            '-loglevel', str(LOGLEVEL),  # debug, info, warning (default param), fatal
            '-v', str(VERBOSE),  # quiet, error, panic
            '-hide_banner',
            # '-stats',
            '-f', 'wav',
            '-'
        ]
        ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE)

        try:
            loop = asyncio.get_running_loop()
            while True:
                chunk = await loop.run_in_executor(
                    None,
                    ffmpeg_process.stdout.read,
                    chunk_size(CHUNK_DURATION_MS)
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
