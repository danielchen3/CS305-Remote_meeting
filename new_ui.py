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
import asyncio
import base64
import json

import numpy as np

import config
from util import parse_multiple_json_objects

class new_APP:
    def __init__(self, free_port):
        self.server = None
        self.conf_serve_ports = free_port
        self.data_serve_ports = {}
        self.data_types = ["screen", "camera", "audio"]
        # 不同类型中存储不同类型对应用户的reader,writer 对应关系ex. id -> text writer/reader
        self.reader_list_audio = {}
        self.writer_list = {}
        self.running = 0
        self.Stop = False
        self.video_active = False
        self.audio_active = False
        self.text = None
        self.imgs = {}
        self.window = tk.Tk()
        self.window.title("Video Conference(p2p)")
        self.window.geometry("1000x900")
        self.window.resizable(False, False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(expand=True, fill=tk.BOTH)
        self.audios = {}
        self.left_frame = tk.Frame(
            self.frame, bg="gray"
        )  # 设置背景颜色为灰色，模拟空白区域
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.pack_propagate(False)  # 防止frame根据内容自适应大小
        self.left_frame.config(width=150, height=800)  # 固定大小

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

        self.video_icon_on = self.resize_image(image_path="icons/video_on.png")
        self.video_icon_off = self.resize_image(image_path="icons/video_off.png")

        self.audio_icon_on = self.resize_image(image_path="icons/audio_on.png")
        self.audio_icon_off = self.resize_image(image_path="icons/audio_off.png")

        # self.audio_icon = self.audio_icon_on
        self.video_icon = self.video_icon_off
        self.audio_icon = self.audio_icon_off
        self.video_button = tk.Button(
            self.frame,
            image=self.video_icon,
            padx=10,
            command=self.toggle_videoTransmission,
        )
        self.audio_button = tk.Button(
            self.frame,
            image=self.audio_icon,
            padx=10,
            command=self.toggle_audioTransmission,
        )

        self.audio_button.config(width=60, height=80)  # 设置按钮的宽度和高度
        self.audio_button.grid(row=1, column=0, padx=10, pady=10, sticky="sw")
        self.video_button.config(width=60, height=80)  # 设置按钮的宽度和高度
        self.video_button.grid(row=2, column=0, padx=10, pady=10, sticky="sw")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.entry_box.bind(
            "<Return>", lambda event: self.on_enter_pressed(self.entry_box, self.text_widget)
        )
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.labels = {}
        # 图像摆放
        # 退出时候删去client
        # 会议结束时候删去所有client以及会议名字

    def resize_image(self, image_path, size=(32, 32)):
        img = Image.open(image_path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return PhotoImage(file=image_path).subsample(3, 3)

    def toggle_videoTransmission(self):
        self.video_active = not self.video_active
        if self.video_active:
            self.video_icon = self.video_icon_on
            self.video_button.config(image=self.video_icon)
        else:
            self.video_icon = self.video_icon_off
            self.video_button.config(image=self.video_icon)
            
    def toggle_audioTransmission(self):
        if not self.audio_active:
            self.audio_active = True
            self.audio_icon = self.audio_icon_on
            self.audio_button.config(image=self.audio_icon)
        else:
            self.audio_active = False
            self.audio_icon = self.audio_icon_off
            self.audio_button.config(image=self.audio_icon)

    def on_enter_pressed(self, entry_box, chat_box):
        entered_text = entry_box.get()
        self.text = entered_text
        self.add_message(chat_box, "Me: " + entered_text)
        entry_box.delete(0, tk.END)

    def close_window(self):
        self.Stop = True
        for thread in threading.enumerate():
            print(thread)
            if thread != threading.main_thread():
                thread.join()
        if self.window:
            self.window.after_cancel(self.task)
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
                print(f"send stop! video")
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
            self.imgs[id] = compressed_image_base64
            message = {
                "client_id": id,
                "type": "video",
                "data": compressed_image_base64,
            }
            writer.write(json.dumps(message).encode())
            await writer.drain()
            await asyncio.sleep(0.1 if not self.video_active else 0.025)

    async def display(self, id, ip, port, chat_box):
        reader, writer = await asyncio.open_connection(ip, port)
        message = {"client_id": id, "type": "receive"}
        writer.write(json.dumps(message).encode())
        await writer.drain()
        while True:
            if self.Stop:
                break
            data = await reader.read(50000)
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
                elif message["type"] == "audio":
                    audio_data = message["data"]
                    audio_id = message["client_id"]
                    self.audios[audio_id] = audio_data
            await asyncio.sleep(0.001)
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
            label.grid(row=cnt % 4, column=cnt // 4, padx=10, pady=10)
            cnt += 1
            label.config(image=tk_image)
            label.image = tk_image
        self.task = self.window.after(10, self.update_video)

    def start_async_task_server(self, id, port):
        loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
        asyncio.set_event_loop(loop)  # 设置事件循环
        try:
            loop.run_until_complete(self.accept_clients())
        except Exception as e:
            print(f"Conn close in video task: {e}")
        finally:
            loop.close()

    def start_async_task_video(self, id, ip, port):
        loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
        asyncio.set_event_loop(loop)  # 设置事件循环
        try:
            loop.run_until_complete(self.video_send(id, ip, port))
        except Exception as e:
            print(f"Conn close in video task: {e}")
        finally:
            loop.close()

    def start_async_task_audio(self, id, ip, port):
        loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
        asyncio.set_event_loop(loop)  # 设置事件循环
        stream = pyaudio.PyAudio().open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        try:
            loop.run_until_complete(self.audio_send(stream, id, ip, port))
        except Exception as e:
            print(f"Conn close in audio task: {e}")
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
                print("send stop! text")
                message = {"type": "quit", "client_id": id}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print("drain text")
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

    def start(self, other_ip, other_port, id, ip, port):
        print("ui")
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        server_thread = threading.Thread(
            target=self.start_async_task_server,args=(id, port)
        )
        server_thread.start()
        
        time.sleep(5)
        
        send_video_thread = threading.Thread(
            target=self.start_async_task_video, args=(id, other_ip, other_port)
        )
        send_video_thread.start()
        send_audio_thread = threading.Thread(
            target=self.start_async_task_audio, args=(id, other_ip, other_port)
        )
        send_audio_thread.start()
        send_text_thread = threading.Thread(
            target=self.start_async_task_text, args=(id, other_ip, other_port)
        )
        send_text_thread.start()

        # display_thread = threading.Thread(
        #     target=self.start_async_task_display, args=(id, ip, port, self.text_widget)
        # )
        # display_thread.start()

        self.update_video()
        self.update_audio(stream, None)

        self.window.mainloop()

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

    async def audio_send(self, stream, id, ip, port):
        reader, writer = await asyncio.open_connection(ip, port)
        await asyncio.sleep(0.3)
        while True:
            if self.Stop:
                print("send stop! audio")
                message = {"type": "quit", "client_id": id}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print(f"send quit message: {message} to client {id}")
                break
            if not self.audio_active:
                cap_audio_base64 = ""
            else:
                cap_audio = stream.read(CHUNK)
                cap_audio_base64 = base64.b64encode(cap_audio).decode("utf-8")
            message = {
                "client_id": id,
                "type": "audio",
                "data": cap_audio_base64,
            }
            writer.write(json.dumps(message).encode())
            await writer.drain()
            await asyncio.sleep(0.002 if self.audio_active else 0.1)
            # if not self.audio_active:
            #     await asyncio.sleep(0.1)
            # await asyncio.sleep(0.001)

    def update_audio(self, stream, pre_audio):
            audio_arrays = []
            if self.Stop:
                self.close_window()
                return
            for _, data in self.audios.copy().items():
                bytes_audio = base64.b64decode(data)
                audio_arrays.append(np.frombuffer(bytes_audio, dtype=np.int16))
            # if len(audio_arrays) == 0:
            #     print("sleep")
            #     time.sleep(1)
            #     self.window.after(10, self.update_audio, stream, pre_audio)
            if len(audio_arrays) == 0:
                max_length = 0
            else:
                max_length = max(len(arr) for arr in audio_arrays)
            for i in range(len(audio_arrays)):
                if len(audio_arrays[i]) < max_length:
                    audio_arrays[i] = np.pad(
                        audio_arrays[i],
                        (0, max_length - len(audio_arrays[i])),
                        "constant",
                    )
            combined_audio = np.zeros(max_length, dtype=np.int16)
            for arr in audio_arrays:
                combined_audio += arr
            final_audio = combined_audio.tobytes()
            # if final_audio == pre_audio:
            #     self.window.after(10, self.update_audio, stream, pre_audio)
            # else:
            #     pre_audio = final_audio
            # print(final_audio)
            stream.write(final_audio)
            self.window.after(10, lambda :self.update_audio(stream, pre_audio))

    async def stop_server(self):
        print(self.running)
        while True:
            if self.running == 3:
                self.server.close()  # 关闭服务器，停止接受新的连接
                await self.server.wait_closed()  # 等待已存在的连接关闭
                print("Server stopped")
                return
            await asyncio.sleep(0.01)

    async def accept_clients(self):
        print("accept_clients")
        self.server = await asyncio.start_server(
            self.handle_client, config.P2P_own_IP, self.conf_serve_ports
        )
        try:
            task1 = asyncio.create_task(self.server.serve_forever())
            task2 = asyncio.create_task(self.stop_server())
            await asyncio.gather(task1, task2)
        except asyncio.CancelledError:
            print("cancelled")
        finally:
            print("quit")
            self.Stop =True
        # await self.server.serve_forever()
        # await self.stop_server()

    async def handle_client(self, reader, writer):
        print("handle_client")
        while True:
            data = await reader.read(50000)
            # print(f"data is {data}")
            objects = parse_multiple_json_objects(data)
            # print(f'receive message {message["type"]} len = {len(objects)}')
            for message in objects:
                if message["type"] == "quit":
                    print(message)
                    self.running += 1
                    print(self.running)
                    # quit_client_id = message["client_id"]
                    return
                    # print(f"first imgs length is {len(self.imgs)}")
                    # print(f"first quit_client_id is {quit_client_id}")
                    # if quit_client_id in self.imgs.keys():
                    #     self.labels[quit_client_id].destroy()
                    #     del self.labels[quit_client_id]
                    #     del self.imgs[quit_client_id]
                    # print(f"then imgs length is {len(self.imgs)}")
                    # print(f"then quit_client_id is {quit_client_id}")
                    # break
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
                    self.add_message(self.text_widget, text)
                elif message["type"] == "audio":
                    audio_data = message["data"]
                    audio_id = message["client_id"]
                    self.audios[audio_id] = audio_data
            await asyncio.sleep(0.001)
        print("display STOP !!")
