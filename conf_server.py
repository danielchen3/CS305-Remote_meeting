import asyncio
import json


class ConferenceServer:
    def __init__(self, free_port):
        self.conf_serve_ports = free_port
        self.data_serve_ports = {}
        self.data_types = ['screen', 'camera', 'audio']
        self.reader_list = {}
        self.writer_list = {}
        self.running = True

    async def handle_data(self, reader, writer, data_type):
        while self.running:
            data = await reader.read(1024)  # 读取一定量的数据
            if not data:
                break
            # 将数据转发给其他所有客户端
            for client_id, conn in self.writer_list.items():
                if client_id != writer.get_extra_info('client_id'):
                    await conn.write(f"{data_type}:{data}".encode())
        pass

    async def handle_client(self, reader, writer):
        client_id = writer.get_extra_info('client_id')
        self.reader_list[client_id] = writer
        self.writer_list[client_id] = writer
        while self.running:
            data = await reader.read(100)
            #message = data.decode()
            await writer.write(data)
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
            print(f'Server status: {len(self.reader_list)} clients connected')

    async def cancel_conference(self):
        self.running = False
        for conn in self.writer_list.values():
            conn.close()
        await asyncio.sleep(1)  # 等待连接关闭
        del self.main_server.conference_servers[self.conference_id]

    async def start(self):
        print("start")
        print(self.conf_serve_ports)
        loop = asyncio.get_event_loop()
        loop.create_task(self.log())
        loop.create_task(self.accept_clients())

    async def accept_clients(self):
        server = await asyncio.start_server(self.handle_client, '127.0.0.1', self.conf_serve_ports)
        await server.serve_forever()
        print("pass")