import tkinter as tk
from PIL import Image, ImageTk
import time
from util import *
import threading
import socket
import base64
from scipy.fftpack import fft, ifft
from collections import defaultdict
from tkinter import PhotoImage
from multiprocessing import Process
import asyncio
import json


class APP:
    def __init__(self):
        self.Stop = False
        self.video_active = False
        self.text = None
        self.imgs = {}
        self.window = tk.Tk()
        self.window.title("Video Conference")
        self.window.geometry("1500x1000")
        self.frame = tk.Frame(self.window)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.left_frame = tk.Frame(
            self.frame, bg="gray"
        )  # 设置背景颜色为灰色，模拟空白区域
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.pack_propagate(False)  # 防止frame根据内容自适应大小
        self.left_frame.config(width=800, height=1500)  # 固定大小

        self.canvas = tk.Canvas(self.left_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(
            self.left_frame, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.scrollbar.set)
        self.label_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.label_frame, anchor="nw")

        self.right_frame = tk.Frame(self.frame)
        self.right_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        self.entry_label = tk.Label(self.right_frame, text="输入文本:")
        self.entry_label.pack(pady=5)
        self.entry_box = tk.Entry(self.right_frame)
        self.entry_box.pack(padx=5, pady=5)

        # 用于显示输入文本的Text控件
        self.scrollbar = tk.Scrollbar(self.right_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget = tk.Text(
            self.right_frame,
            height=15,
            width=50,
            state=tk.DISABLED,
            yscrollcommand=self.scrollbar.set,
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.scrollbar.config(command=self.text_widget.yview)

        self.video_icon = PhotoImage(file="icons/video.png")
        self.video_button = tk.Button(
            self.frame,
            text="Toggle Video",
            image=self.video_icon,
            compound="left",  # 图标在文字的左边
            command=self.toggle_videoTransmission,
            height=10,  # 设置按钮高度
            width=10,  # 设置按钮宽度
            bg="#007BFF",  # 设置按钮背景色
            fg="white",  # 设置字体颜色
            relief="raised",  # 按钮边框样式
        )
        self.video_button.grid(row=4, column=0, padx=2, pady=10, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.entry_box.bind(
            "<Return>", lambda event: self.on_enter_pressed(self.entry_box)
        )
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.labels = {}

    def toggle_videoTransmission(self):
        self.video_active = not self.video_active

    def on_enter_pressed(self, entry_box):
        entered_text = entry_box.get()
        self.text = entered_text
        entry_box.delete(0, tk.END)

    def close_window(self):
        self.Stop = True
        for thread in threading.enumerate():
            if thread != threading.main_thread():
                thread.join()
        if self.window:
            self.window.quit()
            self.window.destroy()
            self.window = None

    def add_message(self, chat_box, message):
        chat_box.config(state=tk.NORMAL)  # 使聊天框可编辑
        chat_box.insert(tk.END, message + "\n")  # 在聊天框中插入消息
        chat_box.yview(tk.END)  # 滚动到最后一行
        chat_box.config(state=tk.DISABLED)  # 禁用编辑

    async def video_send(self, id, ip, port):
        reader, writer = await asyncio.open_connection(ip, port)

        cap = cv2.VideoCapture(0)
        while True:
            if self.Stop:
                print("send stop!")
                message = {"type": "quit", "client_id": id}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                # data = await reader.read(100)
                print(f"send quit message: {message} to client {id}")
                break
            if not self.video_active:
                compressed_image_base64 = black_image
            else:
                camera_image = capture_camera(cap)
                camera_image = camera_image.resize((200, 150), Image.LANCZOS)
                compressed_image = compress_image(camera_image)
                compressed_image_base64 = base64.b64encode(compressed_image).decode(
                    "utf-8"
                )
            message = {
                "client_id": id,
                "type": "video",
                "data": compressed_image_base64,
            }
            writer.write(json.dumps(message).encode())
            await writer.drain()
            if not self.video_active:
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.025)

    async def display(self, id, ip, port, chat_box):
        reader, writer = await asyncio.open_connection(ip, port)
        message = {"client_id": id, "type": "receive"}
        writer.write(json.dumps(message).encode())
        await writer.drain()
        while True:
            if self.Stop:
                break
            data = await reader.read(50000)  # exit的时候会卡在这里
            # print(f"data is {data}")
            objects = parse_multiple_json_objects(data)
            # print(f'receive message {message["type"]} len = {len(objects)}')
            for message in objects:
                if message["type"] == "quit":
                    quit_client_id = message["client_id"]
                    if quit_client_id == id:
                        self.Stop = True
                        break
                    print(f"first imgs length is {len(self.imgs)}")
                    print(f"first quit_client_id is {quit_client_id}")
                    if quit_client_id in self.imgs.keys():
                        self.labels[quit_client_id].destroy()
                        del self.labels[quit_client_id]
                        del self.imgs[quit_client_id]
                    print(f"then imgs length is {len(self.imgs)}")
                    print(f"then quit_client_id is {quit_client_id}")
                    break
            for message in objects:
                if message["type"] == "video":
                    image = message["data"]
                    viedo_id = message["client_id"]
                    self.imgs[viedo_id] = image
                elif message["type"] == "text":
                    text = message["data"]
                    cid = message["client_id"]
                    print(f"we start comparing cid is {cid} and id is {id}")
                    if cid == id:
                        text = "Me: " + text
                    else:
                        text = cid + ": " + text
                    self.add_message(chat_box, text)
            await asyncio.sleep(0.01)
        print("display STOP !!")

    def update_video(self):
        cnt = 0
        # print(f"imgs length in update_video is {len(self.imgs)}")
        # print(f"Labels length in update_video is {len(self.labels)}")
        if self.Stop:
            self.close_window()
            return 
        for id, image in self.imgs.copy().items():
            tk_image = ImageTk.PhotoImage(decompress_image(image))
            if id not in self.labels.keys():
                self.labels[id] = tk.Label(
                    self.left_frame, relief="solid", image=tk_image
                )
                # self.labels[id].grid(row=0, column=cnt, padx=10, pady=10)
                # cnt += 1
            label = self.labels.get(id)
            label.grid(row=0, column=cnt, padx=10, pady=10)
            cnt += 1
            label.config(image=tk_image)
            label.image = tk_image
        self.window.after(10, self.update_video)

    def start_async_task_video(self, id, ip, port):
        loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
        asyncio.set_event_loop(loop)  # 设置事件循环
        try:
            loop.run_until_complete(self.video_send(id, ip, port))
        except Exception as e:
            print(f"Conn close in video task: {e}")
        finally:
            loop.close()

    def start_async_task_display(self, id, ip, port, chat_box):
        loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
        asyncio.set_event_loop(loop)  # 设置事件循环
        try:
            loop.run_until_complete(self.display(id, ip, port, chat_box))
        except Exception as e:
            print(f"Conn close in display task: {e}")
        finally:
            loop.close()

    async def text_send(self, id, ip, port):
        reader, writer = await asyncio.open_connection(ip, port)
        while True:
            if self.Stop:
                message = {"type": "quit", "client_id": id}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                break
            if self.text:
                message = {"client_id": id, "type": "text", "data": self.text}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print(f"text 发送成功!: {message}")
                self.text = None
            await asyncio.sleep(1)

    def start_async_task_text(self, id, ip, port):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.text_send(id, ip, port))
        except Exception as e:
            print(f"Conn close in text task: {e}")
        finally:
            loop.close()

    def start(self, id, ip, port):
        send_video_thread = threading.Thread(
            target=self.start_async_task_video, args=(id, ip, port)
        )
        send_video_thread.start()
        send_text_thread = threading.Thread(
            target=self.start_async_task_text, args=(id, ip, port)
        )
        send_text_thread.start()

        display_thread = threading.Thread(
            target=self.start_async_task_display, args=(id, ip, port, self.text_widget)
        )
        display_thread.start()
        self.update_video()
        self.window.mainloop()


# def toggle_audioTransmission():
#     global audio_active
#     if not audio_active:
#         audio_active = True
#     else:
#         audio_active = False


# def toggle_videoTransmission():
#     global video_active
#     if not video_active:
#         video_active = True
#     else:
#         video_active = False
# def on_enter_pressed(entry_box):
#     global text
#     entered_text = entry_box.get()
#     text = entered_text
#     entry_box.delete(0, tk.END)

# def add_message(chat_box, message):
#     chat_box.config(state=tk.NORMAL)  # 使聊天框可编辑
#     chat_box.insert(tk.END, message + "\n")  # 在聊天框中插入消息
#     chat_box.yview(tk.END)  # 滚动到最后一行
#     chat_box.config(state=tk.DISABLED)  # 禁用编辑

# async def audio_send_receive(id, ip, port):
#     reader, writer = await asyncio.open_connection(ip, port)
#     await asyncio.sleep(0.3)
#     labels = {}
#     global cnt

#     # 发送包含 id 的消息
#     message = {"client_id": id, "type": "audio"}
#     writer.write(json.dumps(message).encode())
#     await writer.drain()  # 确保消息已发送

#     print(f"send our id for audio : {message}")

#     async def capture_audios():
#         stream = pyaudio.PyAudio().open(
#             format=FORMAT,
#             channels=CHANNELS,
#             rate=RATE,
#             input=True,
#             frames_per_buffer=CHUNK,
#         )

#         # 捕获音频数据

#         while True:
#             if not audio_active:
#                 await asyncio.sleep(0.001)
#                 continue
#             cap_audio = stream.read(CHUNK)

#             cap_audio_base64 = base64.b64encode(cap_audio).decode("utf-8")

#             message = {"audio": f"{cap_audio_base64}"}

#             writer.write(json.dumps(message).encode())
#             await writer.drain()

#             # 控制视频发送的频率
#             await asyncio.sleep(0.001)

#     async def display_audio():
#         global cnt
#         audio = pyaudio.PyAudio()
#         stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
#         try:
#             while True:
#                 if not audio_active:
#                     await asyncio.sleep(0.001)
#                     continue
#                 data = await reader.read(10300)
#                 if not data:
#                     print("Server no data.")
#                     continue
#                 stream.write(data)
#         except ConnectionAbortedError as e:
#             print(f"Connection aborted: {e}")

#     # 创建并发任务
#     send_task = asyncio.create_task(capture_audios())
#     receive_task = asyncio.create_task(display_audio())

#     try:
#         await asyncio.gather(send_task, receive_task)
#     except asyncio.CancelledError:
#         print("Tasks were cancelled.")
#     finally:
#         writer.close()
#         await writer.wait_closed()


# async def text_send(id, ip, port, chat_box):
#     reader, writer = await asyncio.open_connection(ip, port)
#     message = {"client_id": id, "type": "text"}
#     writer.write(json.dumps(message).encode())
#     await writer.drain()
#     print(f"send our id for text: {message}")
#     global text
#     while True:
#         await asyncio.sleep(0.1)
#         if Stop:
#             message = {"type": "quit", "client_id":id}
#             writer.write(json.dumps(message).encode())
#             await writer.drain()
#             break
#         if text:
#             message = {
#                 "client_id": id,
#                 "type": "video",
#                 "data": text
#             }
#             writer.write(json.dumps(message).encode())
#             await writer.drain()
#             print(f"text 发送成功!: {message}")
#             text = None
# def start_async_task_text(id, ip, port):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(text_send(id, ip, port))
#     except Exception as e:
#         print(f"Conn close in video task: {e}")
#     finally:
#         loop.close()

# def start_async_task_video(id, ip, port):
#     loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
#     asyncio.set_event_loop(loop)  # 设置事件循环
#     try:
#         loop.run_until_complete(video_send(id, ip, port))
#     except Exception as e:
#         print(f"Conn close in video task: {e}")
#     finally:
#         loop.close()
# def start_async_task_display(id, ip, port, chat_box):
#     loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
#     asyncio.set_event_loop(loop)  # 设置事件循环
#     try:
#         loop.run_until_complete(display(id, ip, port, chat_box))
#     except Exception as e:
#         print(f"Conn close in display task: {e}")
#     finally:
#         loop.close()
# def start_async_task_audio(id, ip, port):
#     loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
#     asyncio.set_event_loop(loop)  # 设置事件循环
#     try:
#         loop.run_until_complete(audio_send_receive(id, ip, port))
#     except Exception as e:
#         print(f"Conn close in video task: {e}")
#     finally:
#         loop.close()


# def start_ui(id, ip, port):
#     global window, Stop, audio_active, video_active
#     Stop = False
#     audio_active = True
#     video_active = True
#     # 初始化 pygame 的音频模块（确保只初始化一次）
#     # pygame.mixer.init()
#     # 创建主窗口
#     global text
#     text = None
#     window = tk.Tk()
#     window.title("Video Conference")
#     window.geometry("1500x1000")  # 设置窗口大小
#     # 创建主界面框架，使用grid布局
#     frame = tk.Frame(window)
#     frame.pack(expand=True, fill=tk.BOTH)
#     global left_frame
#     # 左侧：用于显示摄像头图像的占位符（空白块）
#     left_frame = tk.Frame(frame, bg="gray")  # 设置背景颜色为灰色，模拟空白区域
#     left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
#     left_frame.pack_propagate(False)  # 防止frame根据内容自适应大小
#     left_frame.config(width=800, height=1500)  # 固定大小

#     global convas, label_frame
#     # 创建一个 Canvas 用于滚动
#     canvas = tk.Canvas(left_frame)
#     canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
#     # 添加垂直滚动条
#     scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
#     scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
#     canvas.config(yscrollcommand=scrollbar.set)
#     # 创建一个 Frame 来放置所有的 Label，实际的 Label 会放在这个 Frame 中
#     label_frame = tk.Frame(canvas)
#     canvas.create_window((0, 0), window=label_frame, anchor="nw")

#     # label = tk.Label(left_frame)
#     # label.pack(expand=True, fill=tk.BOTH)
#     # # TODO: 应该是要创造一个新的label,然后按照一定的排列方式呈现
#     # labels[cnt] = label

#     # 右侧：输入文本区域
#     right_frame = tk.Frame(frame)
#     right_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
#     entry_label = tk.Label(right_frame, text="输入文本:")
#     entry_label.pack(pady=5)
#     entry_box = tk.Entry(right_frame)
#     entry_box.pack(padx=5, pady=5)

#     # 用于显示输入文本的Text控件
#     scrollbar = tk.Scrollbar(right_frame)
#     scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
#     text_widget = tk.Text(
#         right_frame,
#         height=15,
#         width=50,
#         state=tk.DISABLED,
#         yscrollcommand=scrollbar.set,
#     )
#     text_widget.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
#     scrollbar.config(command=text_widget.yview)

#     # global send_video
#     # send_video = Process(target=start_async_task_video, args=(id, ip, port))
#     # send_video.start()

#     # sendtext_thread = threading.Thread(
#     #     target=start_async_task_text, args=(id, ip, port, text_widget)
#     # )
#     # sendtext_thread.start()
#     send_video_thread = threading.Thread(
#         target=start_async_task_video, args=(id, ip, port)
#     )
#     send_video_thread.start()
#     display_thread = threading.Thread(
#         target=start_async_task_display,args=(id, ip, port, text_widget)
#     )
#     display_thread.start()
#     # send_audio_thread = threading.Thread(
#     #     target=start_async_task_audio, args=(id, ip, port)
#     # )
#     # send_audio_thread.start()

#     # 音频控制按钮
#     audio_button = tk.Button(
#         frame, text="Toggle Audio", command=lambda: toggle_audioTransmission()
#     )
#     audio_button.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

#     # 加载图标（确保你有图标文件在路径中）
#     audio_icon = PhotoImage(file="icons/audio.png")  # 你的音频图标文件
#     video_icon = PhotoImage(file="icons/video.png")  # 你的视频图标文件

#     # 创建带图标的小按钮
#     audio_button = tk.Button(
#         frame,
#         text="Toggle Audio",
#         image=audio_icon,
#         compound="left",  # 图标在文字的左边
#         command=toggle_audioTransmission,
#         height=10,  # 设置按钮高度
#         width=10,  # 设置按钮宽度
#         bg="#4CAF50",  # 设置按钮背景色
#         fg="white",  # 设置字体颜色
#         relief="raised",  # 按钮边框样式
#     )
#     video_button = tk.Button(
#         frame,
#         text="Toggle Video",
#         image=video_icon,
#         compound="left",  # 图标在文字的左边
#         command=toggle_videoTransmission,
#         height=10,  # 设置按钮高度
#         width=10,  # 设置按钮宽度
#         bg="#007BFF",  # 设置按钮背景色
#         fg="white",  # 设置字体颜色
#         relief="raised",  # 按钮边框样式
#     )
#     audio_button.grid(row=3, column=0, padx=2, pady=10, sticky="nsew")
#     video_button.grid(row=4, column=0, padx=2, pady=10, sticky="nsew")
#     frame.grid_columnconfigure(0, weight=1)
#     frame.grid_columnconfigure(1, weight=1)
#     # audio_button = tk.Button(
#     #     frame, text="Toggle Video", command=lambda: toggle_videoTransmission()
#     # )
#     # audio_button.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

#     entry_box.bind("<Return>", lambda event: on_enter_pressed(entry_box))
#     window.protocol("WM_DELETE_WINDOW", close_window)
#     window.mainloop()


# def close_window():
#     global window, Stop
#     Stop = True
#     window.quit()
#     window.destroy()
