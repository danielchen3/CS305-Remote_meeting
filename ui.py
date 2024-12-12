import tkinter as tk
from PIL import Image, ImageTk
import time
from util import *
import pygame
import threading
import socket


async def video_send_receive(id, ip, port, label):
    reader, writer = await asyncio.open_connection(ip, port)

    await asyncio.sleep(0.1)

    # 发送包含 id 的消息
    message = {"client_id": id}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id: {message}")
    
    async def capture_video():
        # 打开视频捕获（默认是第一个摄像头）

        while True:
            camera_image = capture_camera()

            # 压缩图像
            compressed_image = compress_image(camera_image)

            # 发送图像到服务器
            message = {"video": compressed_image}
            writer.write(json.dumps(message).encode())
            await writer.drain()

            # 控制视频发送的频率
            await asyncio.sleep(0.03)

    async def display_video():
        while True:
            data = await reader.read(1000000)
            if not data:
                print("Server closed the connection.")
                break

            message = json.loads(data.decode())
            if "video" in message:
                compressed_data = message["video"]
                received_image = decompress_image(compressed_data)

                tk_image = ImageTk.PhotoImage(received_image)

                label.config(image=tk_image)
                label.image = tk_image  # Keep a reference to avoid garbage collection

    # 创建并发任务
    send_task = asyncio.create_task(capture_video())
    receive_task = asyncio.create_task(display_video())

    # 等待两个任务完成（通常是永不停止，除非连接中断）
    try:
        await asyncio.gather(send_task, receive_task)
    except asyncio.CancelledError:
        print("Tasks were cancelled.")
    finally:
        writer.close()
        await writer.wait_closed()


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


async def send_and_receive(id, ip, port, chat_box):
    # 建立连接
    reader, writer = await asyncio.open_connection(ip, port)

    await asyncio.sleep(0.1)

    # 发送包含 id 的消息
    message = {"client_id": id}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id: {message}")

    async def send_messages():
        # 发送消息
        global text
        message = {"test": False}
        writer.write(json.dumps(message).encode())
        await writer.drain()

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
    loop.run_until_complete(send_and_receive(id, ip, port, chat_box))  # 运行异步函数


def start_async_task_video(id, ip, port, label):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    loop.run_until_complete(video_send_receive(id, ip, port, label))  # 运行异步函数


def start_ui(id, ip, port):
    # 初始化 pygame 的音频模块（确保只初始化一次）
    # pygame.mixer.init()
    # 创建主窗口
    global text
    text = None
    window = tk.Tk()
    window.title("Conference Detail")
    # 创建主界面框架，使用grid布局
    frame = tk.Frame(window)
    frame.pack()
    # 创建左边的图像显示区域
    left_frame = tk.Frame(frame)
    left_frame.grid(row=0, column=0)
    # 创建右边的侧边栏
    right_frame = tk.Frame(frame)
    right_frame.grid(row=0, column=1, padx=20)
    # 创建标签用于显示摄像头图像
    label = tk.Label(left_frame)
    label.pack()
    # 创建输入框和按钮区域
    entry_label = tk.Label(right_frame, text="输入文本:")
    entry_label.pack()
    entry_box = tk.Entry(right_frame)
    entry_box.pack()
    # 用于显示输入文本的标签
    chat_box = tk.Text(right_frame, height=10, width=50, state=tk.DISABLED)
    chat_box.pack()
    # 绑定回车键事件
    sendtext_thread = threading.Thread(
        target=start_async_task_text, args=(id, ip, port, chat_box)
    )
    sendtext_thread.start()

    # thread = threading.Thread(target=start_async_task2, args = (id, ip, port, chat_box))
    # thread.start()

    # 启动视频流发送和接收的异步任务
    # send_video_thread = threading.Thread(
    #     target=start_async_task_video, args=(id, ip, port, label)
    # )
    # send_video_thread.start()

    entry_box.bind("<Return>", lambda event: on_enter_pressed(entry_box))
    # 启动 Tkinter 主循环
    window.mainloop()


# if __name__ == "__main__":
#     start_ui(1, 1, 1)
