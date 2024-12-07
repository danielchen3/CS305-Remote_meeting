import asyncio
import json
import config

class ConferenceServer:
    def __init__(self, conference_id, reader_main, writer_main):
        self.conference_id = conference_id
        self.conf_serve_ports = config.CF_PORT
        self.data_serve_ports = {}
        self.data_types = ['text']
        self.reader_list = set()
        self.writer_list = set()
        self.reader_main = reader_main
        self.writer_main = writer_main
        self.running = True

    async def handle_data(self, reader, writer, data_type):
        while self.running:
            data = await reader.read(1024)  # 读取一定量的数据
            if not data:
                break
            # 将数据转发给其他所有客户端
            for client_id, conn in self.writer_list:
                if client_id != writer.get_extra_info('client_id'):
                    await conn.write(f"{data_type}:{data}".encode())
        pass

    async def handle_client(self, reader, writer):
        print("success handle")
        while self.running:
            data = await reader.read(100)
            print(data)
            message = data.decode()
            print(message)
            if message.startswith('camera:'):
                # 启动视频流处理
                loop = asyncio.get_event_loop()
                loop.create_task(self.handle_data(reader, writer, 'camera'))
            elif message.startswith('audio:'):
                # 启动音频流处理
                loop = asyncio.get_event_loop()
                loop.create_task(self.handle_data(reader, writer, 'audio'))
            elif message.startswith('screen:'):
                # 启动视频流处理
                loop = asyncio.get_event_loop()
                loop.create_task(self.handle_data(reader, writer, 'screen'))
            elif message.startswith('quit'):
                self.reader_list.remove(reader)
                self.writer_list.remove(writer)
                break
            # print(f"Received message from {client_id}: {message}")
        pass

    async def log(self):
        while self.running:
            print(f'Server {self.conference_id} status: {len(self.reader_list)} clients connected')
            await asyncio.sleep(100)

    async def cancel_conference(self):
        self.running = False
        for conn in self.writer_list.values():
            conn.close()
        await asyncio.sleep(1)  # 等待连接关闭
        del self.main_server.conference_servers[self.conference_id]

    async def start(self):
        print("start")
        self.running = True

    async def accept_clients(self, reader, writer):
        self.reader_list.add(reader)
        self.writer_list.add(writer)
        await self.handle_client(reader, writer)

