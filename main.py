from genericpath import exists
from posixpath import split
import queue
import threading
import cv2
import subprocess as sp
import time
from numpy.core.fromnumeric import size
from numpy.lib import add_docstring
import pyaudio
import wave
from tqdm import tqdm
from PIL import Image, ImageDraw
import numpy as np
import os
import ffmpeg


class Live(object):
    def __init__(self, inputUrl="", rtmpUrl=""):
        self.frame_queue = queue.Queue()
        self.video_queue = queue.Queue() # 待播放的视频列表
        self.playing_video = None # 正在播放的视频
        self.playing_image = None # 显示的图片
        self.playing_text = None # 显示文字
        self.command = ""
        # 自行设置
        self.rtmpUrl = rtmpUrl
        self.camera_path = inputUrl
        self.width = None
        self.hight = None

        #音频
        self.audio = Audio("test.wav")
        self.audio.add_radio("test1.wav")
        self.connect()

    def connect(self):
        print("开启推流")
        if self.camera_path:
            self.cap = cv2.VideoCapture(self.camera_path)
        else:
            self.cap = cv2.VideoCapture(0)   

        # Get video information
        self.rtmp_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.rtmp_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.rtmp_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.hight = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.run_mmpeg()

    def run_mmpeg(self):
        # ffmpeg command
        self.command = ['ffmpeg',
                '-y',
                '-f', 'rawvideo',
                '-vcodec','rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', "{}x{}".format(self.rtmp_width, self.rtmp_height),
                '-r', str(self.rtmp_fps),
                '-i', '-',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-ar', '44100',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-f', 'flv', 
                # '-listen', '1',
                self.rtmpUrl
                # "cc.mp4"
                # "rtmp://127.0.0.1:3000/live/cc"
                ]

        # 防止多线程时 command 未被设置
        while True:
            if len(self.command) > 0:
                # 管道配置
                self.p = sp.Popen(self.command, stdin=sp.PIPE)
                break

    def read_frame(self):
        # read webcamera
        while(self.cap.isOpened()):
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("Opening camera is failed")
                    break

                # put frame into queue
                self.frame_queue.put(frame)
            except Exception as e:
                print("error, will retry : ", str(e))
                time.sleep(1)
                self.connect()

            # 显示图片
            # cv2.imshow('capture', frame)

    def push_frame(self):
        while True:
            if self.frame_queue.empty() != True:
                frame = self.frame_queue.get()
                # print("XXXXXXXXXX: ", frame.shape)
                # cv2.imshow('capture', frame)

                # 添加图片
                frame = self.merge_image(frame, scale_rate=0.3, position=[100,100])
                frame = self.merge_text(frame, position=[10, 200])

                # # 合并视频贞
                add_frame = self.get_video_frame()
                # # print(type(add_frame))
                if type(add_frame) == np.ndarray:
                    # cv2.imshow('capture', add_frame)
                    frame = self.merge_frame(frame, add_frame)

                # radio = self.audio.get_add_frame(self.audio.CHUNK)
                # if radio:
                #     p.stdin.write(radio)
                try:
                    self.p.stdin.write(frame.tostring())
                except Exception as e:
                    print("write rtmp faile, retry %s", str(e))
                    time.sleep(1)
                    self.run_mmpeg()

    def merge_frame(self, frame, addFrame, scale_rate=0.3, position=[0, 0]):
        img1 = Image.fromarray(frame)
        img2 = Image.fromarray(addFrame)
        img2 = img2.resize((int(self.width * scale_rate), int(self.hight * scale_rate)))
        img1.paste(img2, position)
        return np.asarray(img1)

    def merge_image(self, frame, scale_rate=0.3, position=None):
        if not self.playing_image:
            return frame
        o = Image.open(self.playing_image)
        o = o.resize((int(self.width * scale_rate), int(self.hight * scale_rate)))
        img1 = Image.fromarray(frame)
        # r,g,b = img1.split()
        # img1 = Image.merge("RGB", (r, g, b))
        if isinstance(position, list) and len(position) == 2:
            img1.paste(o, position)

        out = np.asarray( img1)
        return out

    def merge_text(self, frame, position=None):
        if not self.playing_text:
            return frame
        img1 = Image.fromarray(frame)
        image_editable = ImageDraw.Draw(img1)
        if not isinstance(position, list) or len(position) == 2:
            position = [10, 200]
        image_editable.text(position, self.playing_text, (237, 230, 211), align='center', size=100)
        out = np.asarray( img1)
        return out

    def add_text(self, text):
        self.playing_text = text
    
    def remove_text(self):
        self.playing_text = None

    def add_image(self, name):
        self.playing_image = name

    def remove_image(self):
        self.playing_image = None

    def remove_video(self):
        self.playing_video = None
        
    def add_video(self, video_path=None):
        # 打开视频，并存入播放视频的队列中
        if video_path and os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            self.video_queue.put(cap)
    def get_video_frame(self):
        if self.playing_video and self.playing_video.isOpened():
            ret, frame = self.playing_video.read()
            if ret == True:
                return frame
        # 视频已经播放完了，则释放资源，并将正播放视频值为空
        if self.playing_video:
            self.playing_video.release()
            self.playing_video = None
        # 检查待播放列表是否为空，如果不为空，则添加到正播放中
        if not self.video_queue.empty():
            self.playing_video = self.video_queue.get()
            return self.get_video_frame()
        return None

    def exec(self):
        while True:
            i = input("请输入指令：add|del jpg|video|text value\n ")
            cs = i.split()
            if len(cs) != 3:
                print("错误的输入！")
                continue
            if cs[0] == "add":
                if cs[1] == "jpg":
                    self.add_image(cs[2])
                    continue
                elif cs[1] == "video":
                    self.add_video(cs[2])
                    continue
                elif cs[2] == "text":
                    self.add_text(cs[2])
                    continue
                else:
                    print("错误的输入！")
                    continue
            elif cs[0] == "del":
                if cs[1] == "jpg":
                    self.remove_image(cs[2])
                    continue
                elif cs[1] == "video":
                    self.remove_video(cs[2])
                    continue
                elif cs[2] == "text":
                    self.remove_text(cs[2])
                    continue
            print("错误的输入！")
            continue


    def run(self):
        threads = [
            threading.Thread(target=Live.read_frame, args=(self,)),
            threading.Thread(target=Live.push_frame, args=(self,))
        ]
        [thread.setDaemon(True) for thread in threads]
        [thread.start() for thread in threads]

        # self.push_frame()

        #  添加视频
        # self.add_video("test.mp4")
        # self.add_image("test.jpg")
        # self.add_text("Hello Man!")
        self.exec()
        for i in threads:
            i.join()

class Audio(object):
    def __init__(self,wave_out_path):
        self.waiting_play_queue = queue.Queue() #待播放音频列表
        self.playing = None # 正播放的音频

        self.p = pyaudio.PyAudio()

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1 # 麦克风的channel
        self.RATE = 44100

        self.wf = wave.open(wave_out_path, 'wb')
        self.wf.setnchannels(self.CHANNELS) # 1 单声道, 2 立体声
        self.wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        self.wf.setframerate(self.RATE)

    def __del__(self):
        self.wf.close()

    def add_radio(self, radio_path):
        #  添加音频源
        if radio_path and os.path.exists(radio_path):
            wf = wave.open(radio_path, 'rb')
            self.waiting_play_queue.put(wf)

    def get_add_frame(self, frame_count):
        if self.playing:
            data2 = self.playing.readframes(frame_count)
            # 如果当前的播放结束，则情况播放列表
            if not data2:
                self.playing = None
            else:
                return data2
        # 检查是否有待播放的队列
        if not self.waiting_play_queue.empty():
            self.playing = self.waiting_play_queue.get()
            return self.get_add_frame(frame_count)

    def record_audio(self,record_second):
        stream = None
        def callback(in_data, frame_count, time_info, status):
            # 获取额外播放音频信息
            add_frame = self.get_add_frame(frame_count)
            if add_frame:
                decoded_add = np.frombuffer(add_frame, np.int16)
                decoded_in = np.frombuffer(in_data, np.int16)
                newdata = (decoded_in * 0.7 + decoded_add* 0.3).astype(np.int16)
                self.wf.writeframes(newdata)
                return (newdata.tostring(), status)
            else:
                self.wf.writeframes(in_data)
                return (in_data, status)

        stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK,
                        stream_callback=callback)

        # out_stream = p.open(format=FORMAT,   # 播放扬声器
        #                 channels=CHANNELS,
        #                 rate=RATE,
        #                 output=True,
        #                 frames_per_buffer=CHUNK)
        print("* recording")
        stream.start_stream()
        print("* done recording")
        while stream.is_active():
            time.sleep(0.1)
        stream.stop_stream()
        stream.close()
        self.p.terminate()
        self.wf.close()

    def mac(self):
        print(pyaudio.PaMacCoreStreamInfo().get_channel_map())

    def get_audio_devices_info(self):
        # 获取到扬声器的channel
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            print((i,dev['name'],dev['maxInputChannels']))

class ReadRTMP(object):
    def ReadFromRTMP(self):
        self.source = ffmpeg.input("rtmp://127.0.0.1:3000/live/cc")
        audio = self.source.audio.filter("aecho", 0.8, 0.9, 1000, 0.3)
        video = self.source.video.hflip()
        out = ffmpeg.output(audio, video, "xx.mp4")
        ffmpeg.run(out)
    def get_viedo_width_height(self,path):
        cap = cv2.VideoCapture(path)

        # Get video information
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height
    def split_av(self):
        width, height = self.get_viedo_width_height("test.mp4")
        process1 = (
            ffmpeg
            .input("test.mp4")
            .output('pipe:', format='rawvideo')
            .run_async(pipe_stdout=True)
        )
        process2 = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(width, height))
            .output("zz.mp4", pix_fmt='yuv420p')
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

        while True:
            in_bytes = process1.stdout.read(width * height * 3)
            if not in_bytes:
                break
            in_frame = (
                np
                .frombuffer(in_bytes, np.uint8)
                .reshape([height, width, 3])
            )
            out_frame = in_frame * 0.3
            # process2.stdin.write(
            #     out_frame
            #     .astype(np.uint8)
            #     .tobytes()
            # )
            process2.stdin.write(in_bytes)
        process2.stdin.close()
        process1.wait()
        process2.wait()


if __name__ == "__main__":
    url = "rtmp://139.155.2.91/live/s"
    live = Live(inputUrl=url, rtmpUrl="rtmp://139.155.2.91/live/L17LTlsVqMNTZyLKMIFSD2x28MlgPJ0SDZVHnHJPxMKi0tWx")
    live.run()
    # live.read_frame()
    # audio = Audio("test.wav")
    # audio.add_radio("test1.wav")
    # audio.get_audio_devices_info()
    # audio.record_audio(record_second=4)
    # audio.mac()
    # a = ReadRTMP()
    # a.split_av()