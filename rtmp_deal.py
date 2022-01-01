import ffmpeg
import numpy as np
from PIL import Image

# https://github.com/kkroening/ffmpeg-python/issues/252
# https://github.com/fluent-ffmpeg/node-fluent-ffmpeg/issues/807

INPUT = "test.mp4"
OUTPUT = "out.mp4"


def get_width_height(INPUT):
    # Probe the input video.
    probe = ffmpeg.probe(INPUT)
    info = next(s for s in probe["streams"] if s["codec_type"] == "video")
    width = info["width"]
    height = info["height"]
    avg_frame_rate = info["avg_frame_rate"]
    return width, height, avg_frame_rate

width, height, avg_frame_rate = get_width_height(INPUT)
print(width, height, avg_frame_rate)


# Define the input and output processes.
# The output process is a video and audio stream concatenated together.
input_process = (
    ffmpeg.input(INPUT)
    .output("pipe:", format="rawvideo", pix_fmt="rgb24")
    .run_async(pipe_stdout=True)
)

input_audio_process = (
    ffmpeg.input(INPUT)
    .output("pipe:", format="aac", ac=2, ar=44100)
    .run_async(pipe_stdout=True)
)

video_output = ffmpeg.input(
    "pipe:",
    format="rawvideo",
    pix_fmt="rgb24",
    s="{}x{}".format(width, height),
    r=avg_frame_rate,
)
# video_output = ffmpeg.input(INPUT).video

audio_output = ffmpeg.input(INPUT).audio
# audio_output = ffmpeg.input(
#     "pipe:",
#     format="aac",
#     ac=2,
#     ar=44100
# )

output_process = (
    ffmpeg.concat(video_output, audio_output, v=1, a=1)
    .output(OUTPUT, pix_fmt="yuv420p")
    .overwrite_output()
    .run_async(pipe_stdin=True)
)

# Added video information
add_path = INPUT
a_width, a_height, a_avg_frame_rate = get_width_height(add_path)
add_input = (
    ffmpeg.input(add_path)
    .output("pipe:", format="rawvideo", pix_fmt="rgb24")
    .run_async(pipe_stdout=True)
)

def get_add_frame(input, width, height):
    in_bytes = input.stdout.read(width * height * 3)
    if not in_bytes:
        return None
    frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
    frame = frame.copy()
    frame[:, :, 0] = 0
    return frame

def merge_frame(frame, addFrame, o_width, o_height, scale_rate=0.3, position=[0, 0]):
    img1 = Image.fromarray(frame)
    img2 = Image.fromarray(addFrame)
    img2 = img2.resize((int(o_width * scale_rate), int(o_height * scale_rate)))
    img1.paste(img2, position)
    return np.asarray(img1)

# # Video processing.
while True:
    in_bytes = input_process.stdout.read(width * height * 3)
    if not in_bytes:
         break
    frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])

    frame = frame.copy()
    frame[:, :, 0] = 0

    # Merge video
    add_frame = get_add_frame(add_input, a_width, a_height)
    result_frame = merge_frame(frame, add_frame, width, height)

    # output_process.stdin.write(frame.astype(np.uint8).tobytes())
    output_process.stdin.write(result_frame.astype(np.uint8).tobytes())

# # Audio processing
# while True:
#     chunk = 1024
#     in_bytes = input_audio_process.stdout.read(chunk)
#     if not in_bytes:
#         break
#     print("xxxxxxxxxxxxxxx", in_bytes)
#     output_process.stdin.write(in_bytes)



output_process.stdin.close()
input_process.wait()
output_process.wait()