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
from multiprocessing import Process, Queue, Value

# 全局变量
window = None
audio_active = True

def toggle_audioTransmission():
    global audio_active
    if not audio_active:
        # 启动音频传输线程
        audio_active = True
    else:
        audio_active = False


def toggle_videoTransmission(video_active):
    video_active.value ^= 1
    print(f'video_active.value is {video_active.value}')


# 处理回车键输入的函数
def on_enter_pressed(entry_box, text_q):
    entered_text = entry_box.get()
    text_q.put(entered_text)
    entry_box.delete(0, tk.END)


# 更新语音输入并返回语音的函数
def add_message(chat_box, message):
    chat_box.config(state=tk.NORMAL)  # 使聊天框可编辑
    chat_box.insert(tk.END, message + "\n")  # 在聊天框中插入消息
    chat_box.yview(tk.END)  # 滚动到最后一行
    chat_box.config(state=tk.DISABLED)  # 禁用编辑
import asyncio
import json

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


async def video_send_receive(id, ip, port, q, video_active, Stop):
    reader, writer = await asyncio.open_connection(ip, port)
    await asyncio.sleep(0.3)
    labels = {}
    message = {"client_id": id, "type": "video"}
    writer.write(json.dumps(message).encode())
    await writer.drain() 
    print(f"send our id for video : {message}")
    async def capture_video():
        while True:
            if Stop.value == 1:
                message = {"quit": id}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print(f"quit发送成功!: {message}")
                break
            print('in capture')
            if video_active.value == 0:
                message = {"OFF": id}
                writer.write(json.dumps(message).encode())
                await asyncio.sleep(0.1)
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
            print('in display')
            data = await reader.read(100000)
            if not data:
                print("Server closed the connection.")
                break
            objects = parse_multiple_json_objects(data)
            end = False
            for message in objects:
                if "quit" in message:
                    quit_id = message["quit"]
                    if quit_id == id:
                        end = True
                        break
                q.put(message)
            if end == True:
                break
            await asyncio.sleep(0.1)
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
        try:
            while True:
                if not audio_active:
                    await asyncio.sleep(0.001)
                    continue
                data = await reader.read(10300)
                if not data:
                    print("Server no data.")
                    continue
                stream.write(data)
        except ConnectionAbortedError as e:
            print(f"Connection aborted: {e}")

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


async def text_send_receive(id, ip, port, q, text_q, Stop):
    # 建立连接
    reader, writer = await asyncio.open_connection(ip, port)

    await asyncio.sleep(0.3)

    # 发送包含 id 的消息 标注type
    message = {"client_id": id, "type": "text"}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id for text: {message}")

    async def send_messages():
        while True:
            if Stop.value == 1:
                message = {"quit": id}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print(f"quit发送成功!: {message}")
                break
            while not text_q.empty():
                text = text_q.get()
                message = {"text": f"{id}:{text}"}
                writer.write(json.dumps(message).encode())
                await writer.drain()
                print(f"text 发送成功!: {message}")
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
            if "quit" in message:
                quit_id = message["quit"]
                if quit_id == id:
                    break
                else: q.put({"text" : f"------{id} QUIT------"})
            if "text" in message:
                tmp_text = message["text"]
                parts = tmp_text.split(":", 1)
                if parts[0] == id:
                    tmp_text = "Me: " + parts[1]
                q.put({"text":tmp_text})
                # add_message(chat_box, tmp_text)
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


def start_async_task_text(id, ip, port, q, text_q, Stop):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    try:
        loop.run_until_complete(text_send_receive(id, ip, port, q, text_q, Stop))
    except Exception as e:
        print(f"Conn close in text task: {e}")
    finally:
        loop.close()


def start_async_task_video(id, ip, port, q, video_active):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    try:
        loop.run_until_complete(video_send_receive(id, ip, port, q, video_active))
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


def update(root, chat_box, left_frame, q):
    # 循环检查队列
    labels = {}
    cnt = 0
    while not q.empty():
        message = q.get()  # 非阻塞地从队列获取
        if "text" in message:
            add_message(chat_box, message["text"])  # 更新聊天框
        else:
            if "video" in message:
                temp_video = message["video"]
                parts = temp_video.split(":", 1)
                tk_image = decompress_image(parts[1])
                id = parts[0]
            elif "OFF" in message:
                id = message["OFF"]
                tk_image = Image.new("RGB", (200, 150), "black")
            tk_image = ImageTk.PhotoImage(tk_image)
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
    # 每隔20毫秒继续调用更新
    global task_id
    task_id = root.after(20, lambda: update(root, chat_box, left_frame, q))
def start_ui(id, ip, port):
    global window
    # 初始化 pygame 的音频模块（确保只初始化一次）
    # pygame.mixer.init()
    # 创建主窗口
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

    video_active = Value('i', 0)
    Stop = Value('i', 0)
    q = Queue() #通道
    text_q = Queue()
    update(window, text_widget, left_frame, q)
    global send_text, video
    send_text = Process(target=start_async_task_text, args=(id, ip, port, q, text_q, Stop))
    send_text.start()
    video = Process(target=start_async_task_video, args=(id, ip, port, q, video_active, Stop))
    video.start()

    # sendtext_thread = threading.Thread(
    #     target=start_async_task_text, args=(id, ip, port, text_widget)
    # )
    # sendtext_thread.start()
    # global send_video_thread
    # send_video_thread = threading.Thread(
    #     target=start_async_task_video, args=(id, ip, port)
    # )
    # send_video_thread.start()
    
    # send_audio_thread = threading.Thread(
    #     target=start_async_task_audio, args=(id, ip, port)
    # )
    # send_audio_thread.start()

    # 音频控制按钮
    audio_button = tk.Button(
        frame, text="Toggle Audio", command=lambda: toggle_audioTransmission()
    )
    audio_button.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

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
        command=lambda: toggle_videoTransmission(video_active),
        height=10,  # 设置按钮高度
        width=10,  # 设置按钮宽度
        bg="#007BFF",  # 设置按钮背景色
        fg="white",  # 设置字体颜色
        relief="raised",  # 按钮边框样式
    )

    audio_button.grid(row=3, column=0, padx=2, pady=10, sticky="nsew")
    video_button.grid(row=4, column=0, padx=2, pady=10, sticky="nsew")

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    entry_box.bind("<Return>", lambda event: on_enter_pressed(entry_box, text_q))
    window.protocol("WM_DELETE_WINDOW", close_window)
    window.mainloop()


def close_window(Stop):
    global window, task_id
    Stop.value = True
    global send_text
    time.sleep(2)
    send_text.terminate()
    send_text.join()
    video.terminate()
    video.join()
    window.after_cancel(task_id)
    window.quit()
    window.destroy()


if __name__ == "__main__":
    start_ui(1, 1, 1)