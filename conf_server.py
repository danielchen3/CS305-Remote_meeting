import asyncio
import json
import config


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

    async def write_data_video(self, data, OFF_video = None):
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
                    message = data.decode()
                    print(f"handle_client receive text is{message}")
                    await self.write_data_txt(data)
                elif type == "video":
                    data = await reader.read(100000)
                    message = data.decode()
                    # print(f"message is {message}")
                    # if "OFF" in message:
                    #     OFF_video.add(writer)
                    #     print("Already turn off the video")
                    #     await self.write_data_video(data, OFF_video)
                    print(f"handle_client receive video is{message}")
                    # else:
                    await self.write_data_video(data)
                elif type == "audio":
                    data = await reader.read(10300)
                    print(f"handle_client receive video is{data}")
                    await self.write_data_audio(data)
        except ConnectionResetError as e:
            print(f"Connection lost with client: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    async def log(self):
        while self.running:
            print(f"Server status: {len(self.reader_list)} clients connected")
    def cancel_conference(self):
        self.running = False
    async def start(self):
        print("start")
        print(self.conf_serve_ports)
        loop = asyncio.get_event_loop()
        # loop.create_task(self.log())
        loop.create_task(self.accept_clients())

    async def accept_clients(self):
        server = await asyncio.start_server(
            self.handle_client, config.SERVER_IP, self.conf_serve_ports
        )
        print("pass")
        await server.serve_forever()
