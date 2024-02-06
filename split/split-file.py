import subprocess
import os


def split_video(input_file, segment_duration):
    base, _ = os.path.splitext(input_file)
    output_manifest = f"{base}.m3u8"

    command = f"ffmpeg -i {input_file} -c:v libx264 -c:a aac -f hls -hls_time {segment_duration} -hls_list_size 0 -hls_segment_filename stream/%03d.ts {os.path.join('stream', output_manifest)}"

    try:
        subprocess.run(command, shell=True, check=True)
        print("Segmentation successful!")
    except subprocess.CalledProcessError as error:
        print("Error during segmentation:", error)


input_file = "video.mp4"
segment_duration = 2

split_video(input_file, segment_duration)
