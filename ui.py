import asyncio
import tkinter as tk
from tkinter import scrolledtext
import threading

class ChatClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.root = tk.Tk()
        self.root.title("聊天客户端")

        # 聊天窗口，使用 ScrolledText 可以让聊天内容滚动
        self.chat_box = scrolledtext.ScrolledText(self.root, width=50, height=20, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_box.grid(row=0, column=0, columnspan=2)

        # 用户输入框
        self.entry = tk.Entry(self.root, width=40)
        self.entry.grid(row=1, column=0)

        # 发送按钮
        self.send_button = tk.Button(self.root, text="发送", width=10, command=self.send_message)
        self.send_button.grid(row=1, column=1)

        # 绑定回车键发送消息
        self.entry.bind("<Return>", self.on_enter_pressed)

    def display_message(self, msg):
        """ 将消息显示到聊天框中，确保在主线程中执行 """
        def update_chat_box():
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.insert(tk.END, f"{msg}\n")
            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.yview(tk.END)  # 自动滚动到底部

        # 使用 after() 确保 GUI 更新在主线程中执行
        self.root.after(0, update_chat_box)

    def send_message(self, event=None):
        message = self.entry.get()
        if message:
            self.entry.delete(0, tk.END)  # 清空输入框
            asyncio.create_task(self.send_message_async(message))  # 发送消息

    def on_enter_pressed(self, event):
        """ 当按下回车键时发送消息 """
        self.send_message()

    async def send_message_async(self, message):
        if self.writer:
            # 发送消息到服务器
            self.writer.write(message.encode())
            await self.writer.drain()  # 确保消息已发送
            self.display_message(f"你: {message}")

    async def receive_messages(self):
        while True:
            data = await self.reader.read(100)  # 假设最多接收 100 字节数据
            if not data:
                print("服务器断开连接")
                break
            self.display_message(f"服务器: {data.decode()}")

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        print(f"连接到服务器 {self.ip}:{self.port} 成功!")

        # 启动接收消息的协程
        asyncio.create_task(self.receive_messages())

    def run(self):
        # 显式为当前线程设置事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect())

    def start_gui(self):
        # 启动 tkinter GUI 主循环
        self.root.mainloop()

def run(ip, port):
    client = ChatClient(ip, port)
    # 启动后台异步任务
    threading.Thread(target=client.run, daemon=True).start()
    # 启动 GUI
    client.start_gui()

# import tkinter as tk
# from PIL import Image, ImageTk
# import time
# from util import *
# import pygame
# import threading


# # 更新图像的函数
# def update_image(label):
#     print("start image")
#     while True:
#         # 捕获摄像头图像
#         camera_image = capture_camera()

#         # 将捕获的图像转换为 Tkinter 可显示的格式
#         camera_image_tk = ImageTk.PhotoImage(camera_image)

#         # 更新标签上的图像
#         label.config(image=camera_image_tk)
#         label.image = camera_image_tk  # 保持对图像的引用，否则图像会被垃圾回收

#         # 延时更新（这里每500毫秒更新一次）
#         time.sleep(0.01)


# # 处理回车键输入的函数
# async def on_enter_pressed(entry_box, output_label):
#     entered_text = entry_box.get()
#     message = {'text':entered_text}
#     writer.write(json.dumps(message).encode())  # 异步发送数据
#     await writer.drain()  # 确保数据已发送
#     data = await reader.read(100)
#     response = json.loads(data.decode())
#     print(f'receive response is {response}')
#     output_label.config(text=response['text'])
#     entry_box.delete(0, tk.END)


# # 更新语音输入并返回语音的函数
# def update_voice():
#     print("start voice")
#     while True:
#         audio_data = capture_voice()  # 捕获语音数据
#         if audio_data:
#             try:
#                 # print("播放音频数据...")
#                 # print(type(audio_data))  # 打印类型
#                 # print(len(audio_data))  # 打印数据的长度
#                 pygame.mixer.Sound(audio_data).play()  # 播放捕获到的音频数据
#             except pygame.error as e:
#                 print(f"音频播放错误: {e}")
#         else:
#             print("没有捕获到音频数据")
#         time.sleep(0.01)  # 每秒检测一次语音输入
# import asyncio
# import json

# async def start(ip, port):
#     # 初始化 pygame 的音频模块（确保只初始化一次）
#     # pygame.mixer.init()
#     # 创建主窗口
#     global reader, writer
#     reader, writer = await asyncio.open_connection(ip, port)
#     window = tk.Tk()
#     window.title("Conference Detail")

#     # 创建主界面框架，使用grid布局
#     frame = tk.Frame(window)
#     frame.pack()
#     # 创建左边的图像显示区域
#     left_frame = tk.Frame(frame)
#     left_frame.grid(row=0, column=0)
#     # 创建右边的侧边栏
#     right_frame = tk.Frame(frame)
#     right_frame.grid(row=0, column=1, padx=20)
#     # 创建标签用于显示摄像头图像
#     label = tk.Label(left_frame)
#     label.pack()
#     # 创建输入框和按钮区域
#     entry_label = tk.Label(right_frame, text="输入文本:")
#     entry_label.pack()
#     entry_box = tk.Entry(right_frame)
#     entry_box.pack()
#     # 用于显示输入文本的标签
#     output_label = tk.Label(right_frame, text="显示的文本会出现在这里")
#     output_label.pack()
#     # 绑定回车键事件
#     entry_box.bind("<Return>", lambda event: asyncio.create_task(on_enter_pressed(entry_box, output_label)))

#     # # # 启动图像更新线程
#     # image_thread = threading.Thread(target=update_image, args=(label,), daemon=True)
#     # image_thread.start()

#     # # 启动语音更新线程
#     # voice_thread = threading.Thread(target=update_voice, daemon=True)
#     # voice_thread.start()

#     # 启动 Tkinter 主循环
#     window.mainloop()