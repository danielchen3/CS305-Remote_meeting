import asyncio
import json


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

    async def handle_data(self, reader, writer, data_type):
        while self.running:
            print("handle_data start awaiting")
            data = await reader.read(1024)  # 读取一定量的数据
            print(f"handle_data receive data is{data}")
            if not data:
                break
            # 将数据转发给其他所有客户端
            for client_id, conn in self.writer_list.items():
                if client_id != writer.get_extra_info("client_id"):
                    await conn.write(f"{data_type}:{data}".encode())
        pass

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
        
    async def write_data_video(self, data):
        tasks = []  # 用于存储所有的写入任务
        # x = 0
        for writer in self.writer_list_video.values():
            # x += 1
            # print(x)
            # 创建写入数据的协程任务
            task = asyncio.create_task(_write_data(writer, data))
            tasks.append(task)
            # print(x)
        await asyncio.gather(*tasks)
        # print(0)

    async def handle_client(self, reader, writer):

        data = await reader.read(100)
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
        while self.running:
            # print("handle_client start awaiting")
            if(type == "text"):
                data = await reader.read(100)
                message = data.decode()
                print(f"handle_client receive text is{message}")
                await self.write_data_txt(data)
            elif(type == "video"):
                data = await reader.read(1000000)
                message = data.decode()
                # print(f"handle_client receive video is{message}")
                await self.write_data_video(data)
            # TODO: add audio here
            # if message.startswith('camera:'):
            #     # 启动视频流处理
            #     loop = asyncio.get_event_loop()
            #     loop.create_task(self.handle_data(reader, writer, 'camera'))
            # elif message.startswith('audio:'):
            #     # 启动音频流处理
            #     loop = asyncio.get_event_loop()
            #     loop.create_task(self.handle_data(reader, writer, 'audio'))
            # elif message.startswith('screen:'):
            #     # 启动视频流处理
            #     loop = asyncio.get_event_loop()
            #     loop.create_task(self.handle_data(reader, writer, 'screen'))
            # elif message.startswith('quit'):
            #     del self.reader_list[client_id]
            #     del self.writer_list[client_id]
            #     break
            # print(f"Received message from {client_id}: {message}")
        pass

    async def log(self):
        while self.running:
            print(f"Server status: {len(self.reader_list)} clients connected")

    async def cancel_conference(self):
        self.running = False
        for conn in self.writer_list_text.values():
            conn.close()
        for conn in self.writer_list_video.values():
            conn.close()
        for conn in self.writer_list_audio.values():
            conn.close()
        await asyncio.sleep(1)  # 等待连接关闭
        # del self.main_server.conference_servers[self.conference_id]

    async def start(self):
        print("start")
        print(self.conf_serve_ports)
        loop = asyncio.get_event_loop()
        # loop.create_task(self.log())
        loop.create_task(self.accept_clients())

    async def accept_clients(self):
        server = await asyncio.start_server(
            self.handle_client, "127.0.0.1", self.conf_serve_ports
        )
        print("pass")
        print("pass")
        await server.serve_forever()
