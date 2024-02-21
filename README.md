# AWS Transcribe streaming client for HLS/DASH

Simply run:
```
./run.sh
```
and follow the instructions.

You'll be asked to pass your AWS credentials and the URL (or local path) to the HLS/DASH manifest.

You can find some free HLS & DASH manifest example test URLs here: \
https://ottverse.com/free-mpeg-dash-mpd-manifest-example-test-urls/ \
https://ottverse.com/free-hls-m3u8-test-urls/ \

You can edit the environment variables in 'run.sh' bash script to change the value of *ffmpeg* flags *LOGLEVEL* and *VERBOSE*. Also, you can unmute the *-stats* flag (just one Python code line) in the 'transcribe.py' script to get *ffmpeg* statistical information.

Press 'Ctrl+X' to KeyboardInterrupt.
