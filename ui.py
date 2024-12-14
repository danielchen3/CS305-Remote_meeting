import tkinter as tk
from PIL import Image, ImageTk
import time
from util import *
import pygame
import threading
import socket
import base64
import re

from collections import defaultdict


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

    # 发送包含 id 的消息
    message = {"client_id": id, "type": "video"}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id for video : {message}")

    async def capture_video():

        while True:
            camera_image = capture_camera()
            camera_image = camera_image.resize((200, 150), Image.LANCZOS)
            # 压缩图像
            compressed_image = compress_image(camera_image)

            compressed_image_base64 = base64.b64encode(compressed_image).decode("utf-8")

            message = {"video": f"{id}:{compressed_image_base64}"}
            writer.write(json.dumps(message).encode())
            await writer.drain()

            # 控制视频发送的频率
            await asyncio.sleep(0.015)

    async def display_video():
        global cnt
        while True:
            data = await reader.read(1000000)
            if not data:
                print("Server closed the connection.")
                break
            objects = parse_multiple_json_objects(data)
            # print(objects)
            for message in objects:
                # print(message)
                try:
                    if "video" in message:
                        # compressed_data = message["video"]
                        # received_image = decompress_image(compressed_data)

                        temp_video = message["video"]
                        # 按照id:image的格式把他们分开
                        parts = temp_video.split(":", 1)
                        received_image = decompress_image(parts[1])
                        # print(f"part0 is {parts[0]}")
                        # print(f"part1 is {parts[1]}")

                        tk_image = ImageTk.PhotoImage(received_image)
                        id = parts[0]
                        
                        # 使用 .keys() 方法获取所有的键
                        # print("All keys in labels:", list(labels.keys())) 
                        if id in labels.keys():
                            print(f"detect exist id: {id}")
                            print(f"For now, we have label is {labels[id]}")
                            label1 = labels.get(id)
                            label1.config(image=tk_image)
                            label1.image = (
                                tk_image  # Keep reference to avoid garbage collection
                            )
                        else:
                            # If the label doesn't exist, create a new one
                            print(f"detect not exist id {id}")
                            # Create the first label
                            label1 = tk.Label(
                                left_frame, relief="solid", image=tk_image
                            )
                            label1.image = (
                                tk_image  # Keep reference to avoid garbage collection
                            )
                            label1.grid(
                                row=0, column=cnt, padx=10, pady=10
                            )  # Place in grid at (row=0, column=0)
                            cnt += 1

                            labels[id] = label1

                            # TODO: reschedule

                            # label.pack(
                            #     fill="x", anchor="w"
                            # )  # Only pack if it's a new label
                            # label.grid(row=2, column=1, sticky="w")
                            # labels[id] = label  # Store the label in the dictionary
                        #     label = tk.Label(left_frame, relief="solid")
                        #     label.pack(fill=tk.X)
                        #     labels[id] = label
                        # label.config(image=tk_image)
                        # label.image = (
                        #     tk_image  # Keep a reference to avoid garbage collection
                        # )

                        # # 更新 canvas 滚动区域
                        # global label_frame, canvas
                        # label_frame.update_idletasks()  # 更新 Frame 高度
                        # canvas.config(scrollregion=canvas.bbox("all"))  # 设置可滚动区域
                except:
                    # print('error!!!!!!!!!!')
                    pass

    # 创建并发任务
    send_task = asyncio.create_task(capture_video())
    receive_task = asyncio.create_task(display_video())

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

    await asyncio.sleep(0.1)

    # 发送包含 id 的消息 标注type
    message = {"client_id": id, "type": "text"}
    writer.write(json.dumps(message).encode())
    await writer.drain()  # 确保消息已发送

    print(f"send our id for text: {message}")

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
    loop.run_until_complete(text_send_receive(id, ip, port, chat_box))  # 运行异步函数


def start_async_task_video(id, ip, port):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    loop.run_until_complete(video_send_receive(id, ip, port))  # 运行异步函数


# cnt = 0


def start_ui(id, ip, port):
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
    # 用于显示输入文本的标签
    # chat_box = tk.Text(right_frame, height=10, width=50, state=tk.DISABLED)
    # chat_box.pack()
    # 绑定回车键事件
    sendtext_thread = threading.Thread(
        target=start_async_task_text, args=(id, ip, port, text_widget)
    )
    sendtext_thread.start()

    # thread = threading.Thread(target=start_async_task2, args = (id, ip, port, chat_box))
    # thread.start()

    # 启动视频流发送和接收的异步任务
    send_video_thread = threading.Thread(
        target=start_async_task_video, args=(id, ip, port)
    )
    send_video_thread.start()

    entry_box.bind("<Return>", lambda event: on_enter_pressed(entry_box))
    # 启动 Tkinter 主循环
    window.mainloop()


if __name__ == "__main__":
    start_ui(1, 1, 1)
