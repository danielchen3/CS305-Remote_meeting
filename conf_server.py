import asyncio
import base64
import json

import numpy as np

import config
from util import parse_multiple_json_objects


async def _write_data(writer, data):
    writer.write(data)
    await writer.drain()


class ConferenceServer:
    def __init__(self, free_port, owner):
        self.conf_serve_ports = free_port
        self.data_serve_ports = {}
        self.data_types = ["screen", "camera", "audio"]
        # 不同类型中存储不同类型对应用户的reader,writer 对应关系ex. id -> text writer/reader
        self.reader_list_audio = {}
        self.writer_list = {}
        self.running = True
        self.owner = owner

    async def write_data_txt(self, data):
        tasks = []  # 用于存储所有的写入任务
        # x = 0
        for writer in self.writer_list_text.values():
            task = asyncio.create_task(_write_data(writer, data))
            tasks.append(task)
            # print(x)
        await asyncio.gather(*tasks)
        # print(0)

    async def write_data_video(self, data, id):
        tasks = []  # 用于存储所有的写入任务
        # x = 0
        for key, writer in self.writer_list_video.items():
            # x += 1
            # print(x)
            # 创建写入数据的协程任务
            if key != id:
                await _write_data(writer=writer, data=data)

        await asyncio.gather(*tasks)

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
        data_read = 50000
        while self.running:
            # asyncio.sleep(0.1)
            data = await reader.read(data_read)
            print(data)
            if not data:
                print("client disconnected!")
                break
            # print(f"data is {data}")
            objects = parse_multiple_json_objects(data)
            for message in objects:
                client_id = message.get("client_id")
                type = message.get("type")
                if type == "receive":
                    self.writer_list[client_id] = writer
                    return
                if type == "quit":
                    if client_id == self.owner:
                        await self.cancel_conference()
                    else:
                        await self.quit(client_id)
                    break
            for message in objects:
                tasks = []
                print(f"receive is {message['type']}")
                for key, writer in self.writer_list.items():
                    # print(f"send to {key}")
                    tasks.append(asyncio.create_task(_write_data(writer, data)))
                await asyncio.gather(*tasks)
        print(f"quit handle")

    async def log(self):
        while self.running:
            print(f"Server status: {len(self.reader_list)} clients connected")

    async def quit(self, id):
        if id in self.writer_list:
            message = {"type": "quit", "client_id": id}
            writer = self.writer_list[id]
            writer.write(json.dumps(message).encode())
            await writer.drain()
            print(f"sent quit message {message} to {id}")
            del self.writer_list[id]

    async def cancel_conference(self):
        print(f"conf_server start canceling server")
        self.running = False
        for key in list(self.writer_list.keys()):
            # key = next(iter(self.writer_list))
            print(f"start quit {key}")
            await self.quit(key)

    async def start(self):
        print("start")
        print(self.conf_serve_ports)
        await self.accept_clients()

    # loop = asyncio.get_event_loop()
    # loop.create_task(self.log())
    # loop.create_task(self.accept_clients())
    # loop.create_task(self.handle_audio())

    async def accept_clients(self):
        server = await asyncio.start_server(
            self.handle_client, config.SERVER_IP, self.conf_serve_ports
        )
        await server.serve_forever()

    async def handle_audio(self):
        await asyncio.sleep(5)
        while self.running:
            print("begin handle")
            all_data = []
            for client_id, reader in list(self.reader_list_audio.items()):
                if (
                    not client_id in self.reader_list_audio
                ):  # or not self.on_audio[client_id]:
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
                audio_arrays[i] = np.pad(
                    audio_arrays[i], (0, max_length - len(audio_arrays[i])), "constant"
                )

        # 将音频数组按帧逐个叠加
        combined_audio = np.zeros(max_length, dtype=np.int16)
        for arr in audio_arrays:
            combined_audio += arr

        # 将叠加后的音频数据转换为字节
        return combined_audio.tobytes()
