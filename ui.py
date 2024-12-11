
import tkinter as tk
from PIL import Image, ImageTk
import time
from util import *
import pygame
import threading
import socket

# 更新图像的函数
def update_image(label):
    print("start image")
    while True:
        # 捕获摄像头图像
        camera_image = capture_camera()
        # 将捕获的图像转换为 Tkinter 可显示的格式
        camera_image_tk = ImageTk.PhotoImage(camera_image)
        # 更新标签上的图像
        label.config(image=camera_image_tk)
        label.image = camera_image_tk  # 保持对图像的引用，否则图像会被垃圾回收
        # 延时更新（这里每500毫秒更新一次）
        time.sleep(0.01)


# 处理回车键输入的函数
def on_enter_pressed(entry_box):
    global text
    entered_text = entry_box.get()
    text = entered_text
    entry_box.delete(0, tk.END)
# 更新语音输入并返回语音的函数
def add_message(chat_box, message):
    chat_box.config(state=tk.NORMAL)  # 使聊天框可编辑
    chat_box.insert(tk.END, message + '\n')  # 在聊天框中插入消息
    chat_box.yview(tk.END)  # 滚动到最后一行
    chat_box.config(state=tk.DISABLED)  # 禁用编辑

def update_voice():
    print("start voice")
    while True:
        audio_data = capture_voice()  # 捕获语音数据
        if audio_data:
            try:
                # print("播放音频数据...")
                # print(type(audio_data))  # 打印类型
                # print(len(audio_data))  # 打印数据的长度
                pygame.mixer.Sound(audio_data).play()  # 播放捕获到的音频数据
            except pygame.error as e:
                print(f"音频播放错误: {e}")
        else:
            print("没有捕获到音频数据")
        time.sleep(0.01)  # 每秒检测一次语音输入
import asyncio
import json
async def send(id, ip, port):
    reader, writer = await asyncio.open_connection(ip, port)
    global text
    message = {'test':False}
    writer.write(json.dumps(message).encode())
    await writer.drain()
    while True:
        if text:
            message = {'text': id + ':' + text}
            writer.write(json.dumps(message).encode())
            await writer.drain()
            print('text 发送成功!')
            # data = await reader.read(100)
            # response = json.loads(data.decode())
            # print(f'receive response is {response}')
            text = None
async def update(id, ip, port, chat_box):
    reader, writer = await asyncio.open_connection(ip, port)
    message = {'test':True}
    writer.write(json.dumps(message).encode())
    await writer.drain()
    while True:
        data = await reader.read(100)
        message = json.loads(data.decode())
        if 'text' in message:
            tmp_text = message['text']
            if tmp_text.startwith(id):
                tmp_text = 'Me' + tmp_text[len(id):]
                add_message(chat_box, tmp_text)
def start_async_task1(id, ip, port):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    loop.run_until_complete(send(id, ip, port))  # 运行异步函数

def start_async_task2(id, ip, port, chat_box):
    loop = asyncio.new_event_loop()  # 为每个线程创建独立的事件循环
    asyncio.set_event_loop(loop)  # 设置事件循环
    loop.run_until_complete(update(id, ip, port, chat_box))  # 运行异步函数


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
    sendtext_thread = threading.Thread(target=start_async_task1, args = (id, ip, port))
    sendtext_thread.start()
    
    #thread = threading.Thread(target=start_async_task2, args = (id, ip, port, chat_box))
    #thread.start()
    
    entry_box.bind("<Return>", lambda event: on_enter_pressed(entry_box))

    # # # 启动图像更新线程
    # image_thread = threading.Thread(target=update_image, args=(label,), daemon=True)
    # image_thread.start()

    # # 启动语音更新线程
    # voice_thread = threading.Thread(target=update_voice, daemon=True)
    # voice_thread.start()
    # 启动 Tkinter 主循环
    window.mainloop()