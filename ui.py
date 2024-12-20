import tkinter as tk
from PIL import Image, ImageTk
import time
from util import *
import pygame
import threading
import socket
import base64
import re
from scipy.fftpack import fft, ifft
from collections import defaultdict
from tkinter import PhotoImage
from multiprocessing import Process

# 全局变量
window = None
audio_active = True
video_active = True
Stop = False

def toggle_audioTransmission():
    global audio_active
    if not audio_active:
        # 启动音频传输线程
        audio_active = True
    else:
        audio_active = False


def toggle_videoTransmission():
    global video_active
    if not video_active:
        # 启动视频传输线程
        video_active = True
    else:
        video_active = False


# 处理回车键输入的函数
def on_enter_pressed(entry_box):
    global text
    entered_text = entry_box.get()
    text = entered_text
    entry_box.delete(0, tk.END)


# 更新语音输入并返回语音的函数
def add_message(chat_box, message):
    chat_box.config(state=tk.NORMAL)  # 使聊天框可编辑
    chat_box.insert(tk.END, message + "\n")  # 在聊天框中插入消息
    chat_box.yview(tk.END)  # 滚动到最后一行
    chat_box.config(state=tk.DISABLED)  # 禁用编辑


import asyncio
import json

cnt = 0


# def parse_multiple_json_objects(data_str):
#     objects = []
#     while data_str:
#         try:
#             # 尝试解码一个 JSON 对象
#             obj, idx = json.JSONDecoder().raw_decode(data_str)
#             objects.append(obj)
#             # 剩余的部分
#             data_str = data_str[idx:].strip()
#         except json.JSONDecodeError as e:
#             print("Error decoding JSON:", e)
#             break
#     return objects


def parse_multiple_json_objects(data):
    # 使用正则表达式查找所有JSON对象
    json_objects = re.findall(r"\{.*?\}", data.decode(), re.DOTALL)

    # 解析每个JSON对象，丢弃不完整或无效的JSON对象
    parsed_objects = []
    for obj in json_objects:
        try:
            parsed_objects.append(json.loads(obj))
        except json.JSONDecodeError:
            # 如果解析失败，直接跳过这个对象
            continue
    return parsed_objects


async def video_send_receive(id, ip, port):
    reader, writer = await asyncio.open_connection(ip, port)
    await asyncio.sleep(0.3)
    labels = {}
    global cnt
    global video_active
    message = {"client_id": id, "type": "video"}
    writer.write(json.dumps(message).encode())
    await writer.drain() 
    print(f"send our id for video : {message}")
    async def capture_video():
        while True:
            if Stop == True:
                print('stop capture')
                break
            print('in capture')
            if not video_active:
                message = {"OFF": id}
                writer.write(json.dumps(message).encode())
                await asyncio.sleep(0.001)
                continue
            camera_image = capture_camera()
            camera_image = camera_image.resize((200, 150), Image.LANCZOS)
            compressed_image = compress_image(camera_image)
            compressed_image_base64 = base64.b64encode(compressed_image).decode("utf-8")
            message = {"video": f"{id}:{compressed_image_base64}"}
            writer.write(json.dumps(message).encode())
            await writer.drain()
            await asyncio.sleep(0.1)

    async def display_video():
        global cnt
        while True:
            if Stop == True:
                print('stop display')
                break
            print('in display')
            data = await reader.read(100000)
            if not data:
                print("Server closed the connection.")
                break
            objects = parse_multiple_json_objects(data)
            for message in objects:
                try:
                    if "video" in message:
                        temp_video = message["video"]
                        parts = temp_video.split(":", 1)
                        received_image = decompress_image(parts[1])
                        tk_image = ImageTk.PhotoImage(received_image)
                        id = parts[0]
                        if id in labels.keys():
                            label1 = labels.get(id)
                            label1.config(image=tk_image)
                            label1.image = (
                                tk_image  # Keep reference to avoid garbage collection
                            )
                        else:
                            label1 = tk.Label(
                                left_frame, relief="solid", image=tk_image
                            )
                            label1.image = (
                                tk_image  # Keep reference to avoid garbage collection
                            )
                            label1.grid(
                                row=0, column=cnt, padx=10, pady=10
                            )
                            cnt += 1
                            labels[id] = label1
                    elif "OFF" in message:
                        id = message["OFF"]
                        label1 = labels.get(id)
                        black_image = Image.new("RGB", (200, 150), "black")  # 创建黑色图像
                        tk_black_image = ImageTk.PhotoImage(black_image) 
                        label1.config(image=tk_black_image)
                        label1.image = (tk_black_image)
                except:
                    print('error')
                    pass
    send_task = asyncio.create_task(capture_video())
    receive_task = asyncio.create_task(display_video())
    try:
        await asyncio.gather(send_task, receive_task)
    except asyncio.CancelledError:
        print("Tasks were cancelled.")
    finally:
        writer.close()
        await writer.wait_closed()


async def audio_send_receive(id, ip, port):
    reader, writer = await asyncio.open_connection(ip, port)

    await asyncio.sleep(0.3)

    labels = {}
    global cnt

    # 发送包含 id 的消息
    message = {"client_id": id, "type": "audio"}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id for audio : {message}")

    async def capture_audios():
        stream = pyaudio.PyAudio().open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        # 捕获音频数据

        while True:
            if not audio_active:
                await asyncio.sleep(0.001)
                continue
            cap_audio = stream.read(CHUNK)

            cap_audio_base64 = base64.b64encode(cap_audio).decode("utf-8")

            message = {"audio": f"{cap_audio_base64}"}

            writer.write(json.dumps(message).encode())
            await writer.drain()

            # 控制视频发送的频率
            await asyncio.sleep(0.001)

    async def display_audio():
        global cnt
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        while True:
            if not audio_active:
                await asyncio.sleep(0.001)
                continue
            data = await reader.read(10300)
            if not data:
                print("Server closed the connection.")
                break
            objects = parse_multiple_json_objects(data)
            # print(objects)
            for message in objects:
                # print(message)

                if "audio" in message:
                    # compressed_data = message["video"]
                    # received_image = decompress_image(compressed_data)
                    temp_audio = message["audio"]
                    bytes_audio = base64.b64decode(temp_audio)
                    audio_data = np.frombuffer(bytes_audio, dtype=np.int16)
                    # 应用 FFT
                    fft_data = fft(audio_data)
                    # 设定阈值，过滤噪声
                    threshold = 100  # 阈值需要根据实际情况调整
                    fft_data[np.abs(fft_data) < threshold] = 0
                    # 应用逆 FFT
                    denoised_data = ifft(fft_data)
                    # 将数据转换回字节串并播放
                    denoised_data = np.real(denoised_data).astype(np.int16)
                    stream.write(denoised_data.tobytes())

    # 创建并发任务
    send_task = asyncio.create_task(capture_audios())
    receive_task = asyncio.create_task(display_audio())

    try:
        await asyncio.gather(send_task, receive_task)
    except asyncio.CancelledError:
        print("Tasks were cancelled.")
    finally:
        writer.close()
        await writer.wait_closed()


async def text_send_receive(id, ip, port, chat_box):
    # 建立连接
    reader, writer = await asyncio.open_connection(ip, port)

    await asyncio.sleep(0.3)

    # 发送包含 id 的消息 标注type
    message = {"client_id": id, "type": "text"}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id for text: {message}")

    async def send_messages():
        # 发送消息
        global text
        while True:
            if text:
                message = {"text": f"{id}:{text}"}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print(f"text 发送成功!: {message}")
                text = None
            await asyncio.sleep(0.1)

    async def receive_messages():
        # 接收消息
        while True:
            print("awaiting data in receive_messages...")
            data = await reader.read(100)
            if not data:
                print("Server closed the connection.")
                break

            message = json.loads(data.decode())
            print(f"receive data: {message}")

            if "text" in message:
                tmp_text = message["text"]
                parts = tmp_text.split(":", 1)
                if parts[0] == id:
                    tmp_text = "Me: " + parts[1]
                add_message(chat_box, tmp_text)
                # await asyncio.sleep(0.1)

            await asyncio.sleep(0.1)

    send_task = asyncio.create_task(send_messages())
    receive_task = asyncio.create_task(receive_messages())

    try:
        await asyncio.gather(send_task, receive_task)
    except asyncio.CancelledError:
        print("Tasks were cancelled.")
    finally:
        writer.close()
        await writer.wait_closed()


def start_async_task_text(id, ip, port, chat_box):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    try:
        loop.run_until_complete(text_send_receive(id, ip, port, chat_box))
    except Exception as e:
        print(f"Conn close in video task: {e}")
    finally:
        loop.close()


def start_async_task_video(id, ip, port):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    try:
        loop.run_until_complete(video_send_receive(id, ip, port))
    except Exception as e:
        print(f"Conn close in video task: {e}")
    finally:
        loop.close()


def start_async_task_audio(id, ip, port):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    try:
        loop.run_until_complete(audio_send_receive(id, ip, port))
    except Exception as e:
        print(f"Conn close in video task: {e}")
    finally:
        loop.close()


def start_ui(id, ip, port):
    global window
    # 初始化 pygame 的音频模块（确保只初始化一次）
    # pygame.mixer.init()
    # 创建主窗口
    global text
    text = None
    window = tk.Tk()
    window.title("Video Conference")
    window.geometry("1500x1000")  # 设置窗口大小
    # 创建主界面框架，使用grid布局
    frame = tk.Frame(window)
    frame.pack(expand=True, fill=tk.BOTH)
    global left_frame
    # 左侧：用于显示摄像头图像的占位符（空白块）
    left_frame = tk.Frame(frame, bg="gray")  # 设置背景颜色为灰色，模拟空白区域
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    left_frame.pack_propagate(False)  # 防止frame根据内容自适应大小
    left_frame.config(width=800, height=1500)  # 固定大小

    global convas, label_frame
    # 创建一个 Canvas 用于滚动
    canvas = tk.Canvas(left_frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    # 添加垂直滚动条
    scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.config(yscrollcommand=scrollbar.set)
    # 创建一个 Frame 来放置所有的 Label，实际的 Label 会放在这个 Frame 中
    label_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=label_frame, anchor="nw")

    # label = tk.Label(left_frame)
    # label.pack(expand=True, fill=tk.BOTH)
    # # TODO: 应该是要创造一个新的label,然后按照一定的排列方式呈现
    # labels[cnt] = label

    # 右侧：输入文本区域
    right_frame = tk.Frame(frame)
    right_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
    entry_label = tk.Label(right_frame, text="输入文本:")
    entry_label.pack(pady=5)
    entry_box = tk.Entry(right_frame)
    entry_box.pack(padx=5, pady=5)

    # 用于显示输入文本的Text控件
    scrollbar = tk.Scrollbar(right_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget = tk.Text(
        right_frame,
        height=15,
        width=50,
        state=tk.DISABLED,
        yscrollcommand=scrollbar.set,
    )
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
    scrollbar.config(command=text_widget.yview)
    
    # global send_video
    # send_video = Process(target=start_async_task_video, args=(id, ip, port))
    # send_video.start()

    # sendtext_thread = threading.Thread(
    #     target=start_async_task_text, args=(id, ip, port, text_widget)
    # )
    # sendtext_thread.start()
    global send_video_thread
    send_video_thread = threading.Thread(
        target=start_async_task_video, args=(id, ip, port)
    )
    send_video_thread.start()
    
    # send_audio_thread = threading.Thread(
    #     target=start_async_task_audio, args=(id, ip, port)
    # )
    # send_audio_thread.start()

    # 音频控制按钮
    # audio_button = tk.Button(
    #     frame, text="Toggle Audio", command=lambda: toggle_audioTransmission()
    # )
    # audio_button.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

    # 加载图标（确保你有图标文件在路径中）
    audio_icon = PhotoImage(file="icons/audio.png")  # 你的音频图标文件
    video_icon = PhotoImage(file="icons/video.png")  # 你的视频图标文件

    # 创建带图标的小按钮
    audio_button = tk.Button(
        frame,
        text="Toggle Audio",
        image=audio_icon,
        compound="left",  # 图标在文字的左边
        command=toggle_audioTransmission,
        height=10,  # 设置按钮高度
        width=10,  # 设置按钮宽度
        bg="#4CAF50",  # 设置按钮背景色
        fg="white",  # 设置字体颜色
        relief="raised",  # 按钮边框样式
    )

    video_button = tk.Button(
        frame,
        text="Toggle Video",
        image=video_icon,
        compound="left",  # 图标在文字的左边
        command=toggle_videoTransmission,
        height=10,  # 设置按钮高度
        width=10,  # 设置按钮宽度
        bg="#007BFF",  # 设置按钮背景色
        fg="white",  # 设置字体颜色
        relief="raised",  # 按钮边框样式
    )

    # 使用 grid 布局放置按钮
    audio_button.grid(row=3, column=0, padx=2, pady=10, sticky="nsew")
    video_button.grid(row=4, column=0, padx=2, pady=10, sticky="nsew")

    # 调整列的权重，使按钮适应父容器大小
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    # audio_button = tk.Button(
    #     frame, text="Toggle Video", command=lambda: toggle_videoTransmission()
    # )
    # audio_button.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

    entry_box.bind("<Return>", lambda event: on_enter_pressed(entry_box))
    # 启动 Tkinter 主循环
    window.protocol("WM_DELETE_WINDOW", close_window)
    window.mainloop()


def close_window():
    global window, Stop
    Stop = True
    # global send_video
    # if send_video is not None:
    #     send_video.terminate()
    #     send_video.join()     
    time.sleep(100)
    window.quit()
    window.destroy()


if __name__ == "__main__":
    start_ui(1, 1, 1)