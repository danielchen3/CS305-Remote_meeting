import asyncio
import base64
import json

import numpy as np

import config
from ui import parse_multiple_json_objects


async def _write_data(writer, data):
    writer.write(data)
    await writer.drain()


class ConferenceServer:
    def __init__(self, free_port):
        self.conf_serve_ports = free_port
        self.data_serve_ports = {}
        self.data_types = ["screen", "camera", "audio"]
        # 不同类型中存储不同类型对应用户的reader,writer 对应关系ex. id -> text writer/reader
        self.reader_list_text = {}
        self.writer_list_text = {}
        self.reader_list_video = {}
        self.writer_list_video = {}
        self.reader_list_audio = {}
        self.writer_list_audio = {}
        self.running = True

    async def write_data_txt(self, data):
        tasks = []  # 用于存储所有的写入任务
        # x = 0
        for writer in self.writer_list_text.values():
            # x += 1
            # print(x)
            # 创建写入数据的协程任务
            task = asyncio.create_task(_write_data(writer, data))
            tasks.append(task)
            # print(x)
        await asyncio.gather(*tasks)
        # print(0)

    async def write_data_video(self, data, OFF_video=None):
        tasks = []  # 用于存储所有的写入任务
        # x = 0
        for writer in self.writer_list_video.values():
            # x += 1
            # print(x)
            # 创建写入数据的协程任务
            await _write_data(writer=writer, data=data)
            # task = asyncio.create_task(_write_data(writer, data))
            # tasks.append(task)
            # print(x)
        # await asyncio.gather(*tasks)
        # print(0)

    async def write_data_audio(self, data):
        tasks = []  # 用于存储所有的写入任务
        # x = 0
        for writer in self.writer_list_audio.values():

            # x += 1
            # print(x)
            # 创建写入数据的协程任务
            await _write_data(writer=writer, data=data)
            # task = asyncio.create_task(_write_data(writer, data))
            # tasks.append(task)
            # print(x)
        # await asyncio.gather(*tasks)
        # print(0)

    async def handle_client(self, reader, writer):

        data = await reader.read(100)
        print(f"data is {data}")
        message = json.loads(data.decode())
        client_id = message.get("client_id")
        type = message.get("type")

        print(f"get client: {client_id}")

        if type == "text" and client_id:
            self.reader_list_text[client_id] = reader
            self.writer_list_text[client_id] = writer
            print(
                f"handle_client in id text {client_id} with writer_list length is{len(self.writer_list_text)}"
            )
        elif type == "video" and client_id:
            self.reader_list_video[client_id] = reader
            self.writer_list_video[client_id] = writer
            print(
                f"handle_client in id video {client_id} with writer_list length is{len(self.writer_list_video)}"
            )
        elif type == "audio" and client_id:
            self.reader_list_audio[client_id] = reader
            self.writer_list_audio[client_id] = writer
            print(
                f"handle_client in id audio {client_id} with writer_list length is{len(self.writer_list_audio)}"
            )
        try:
            while self.running:
                # print("handle_client start awaiting")
                if type == "text":
                    data = await reader.read(100)
                    if not data:
                        continue
                    message = data.decode()
                    if "quit" in message:
                        id = message['quit']
                        await self.write_data_video(data)
                        del self.reader_list_video[id]
                        del self.writer_list_video[id]
                        break                    
                    print(f"handle_client receive text is{message}")
                    await self.write_data_txt(data)
                elif type == "video":
                    data = await reader.read(100000)
                    message = data.decode()
                    if "quit" in message:
                        id = message['quit']
                        await self.write_data_video(data)
                        del self.reader_list_video[id]
                        del self.writer_list_video[id]
                        break
                    print(f"handle_client receive video is{message}")
                    # else:
                    await self.write_data_video(data)
                elif type == "audio":
                    await asyncio.sleep(1)
        except ConnectionResetError as e:
            print(f"Connection lost with client: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        print('conference end!')
    async def log(self):
        while self.running:
            print(f"Server status: {len(self.reader_list)} clients connected")

    def cancel_conference(self):
        print(f"conf_server start canceling server")
        # if self.conf_server:
        #     self.conf_server.close()
        #     self.conf_server.wait_closed()
        #     print("Conference server stopped")
        self.running = False
        # for conn in self.writer_list_text.values():
        #     conn.close()
        # for conn in self.writer_list_video.values():
        #     conn.close()
        # for conn in self.writer_list_audio.values():
        #     conn.close()
        # asyncio.sleep(1)  # 等待连接关闭
        # del self.main_server.conference_servers[self.conference_id]

    async def start(self):
        print("start")
        print(self.conf_serve_ports)
        loop = asyncio.get_event_loop()
        # loop.create_task(self.log())
        loop.create_task(self.accept_clients())
        # loop.create_task(self.handle_audio())

    async def accept_clients(self):
        server = await asyncio.start_server(
            self.handle_client, config.SERVER_IP, self.conf_serve_ports
        )
        print("pass")
        await server.serve_forever()

    async def handle_audio(self):
        await asyncio.sleep(5)
        while self.running:
            print("begin handle")
            all_data = []
            for client_id, reader in list(self.reader_list_audio.items()):
                if not client_id in self.reader_list_audio:  # or not self.on_audio[client_id]:
                    continue
                print(client_id)
                data = await reader.read(10300)
                print(data)
                objects = parse_multiple_json_objects(data)
                for message in objects:
                    if "audio" in message:
                        temp_audio = message["audio"]
                        bytes_audio = base64.b64decode(temp_audio)
                        print(bytes_audio)
                        print(len(bytes_audio))
                        all_data.append(bytes_audio)

            if len(all_data) == 0:
                continue
            over_data = self.overlay_audio(*all_data)
            await self.write_data_audio(over_data)

    def overlay_audio(*audio_data):
        print(audio_data)
        audio_arrays = []
        # 将音频数据转换为 numpy 数组（假设音频格式是 int16）
        for data in audio_data:
            if isinstance(data, bytes):
                audio_arrays.append(np.frombuffer(data, dtype=np.int16))
            else:
                continue
        # 获取最大音频长度
        max_length = max(len(arr) for arr in audio_arrays)

        # 补齐音频数组
        for i in range(len(audio_arrays)):
            if len(audio_arrays[i]) < max_length:
                audio_arrays[i] = np.pad(audio_arrays[i], (0, max_length - len(audio_arrays[i])), 'constant')

        # 将音频数组按帧逐个叠加
        combined_audio = np.zeros(max_length, dtype=np.int16)
        for arr in audio_arrays:
            combined_audio += arr

        # 将叠加后的音频数据转换为字节
        return combined_audio.tobytes()
