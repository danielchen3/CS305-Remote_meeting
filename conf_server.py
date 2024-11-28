import asyncio


class ConferenceServer:
    def __init__(self, conference_id, main_server):
        self.conference_id = conference_id
        self.conf_serve_ports = None
        self.data_serve_ports = {}
        self.data_types = ['screen', 'camera', 'audio']
        self.clients_info = {}
        self.client_conns = {}
        self.main_server = main_server
        self.running = True

    async def handle_data(self, reader, writer, data_type):
        while True:
            data = await reader.read(1024)  # 读取一定量的数据
            if not data:
                break
            # 将数据转发给其他所有客户端
            for client_id, conn in self.client_conns.items():
                if client_id != writer.get_extra_info('client_id'):
                    await conn.write(f"{data_type}:{data}".encode())

    async def handle_client(self, reader, writer):
        client_id = writer.get_extra_info('client_id')
        self.clients_info[client_id] = writer
        self.client_conns[client_id] = writer
        while self.running:
            data = await reader.read(100)
            message = data.decode()
            if message.startswith('camera:'):
                # 启动视频流处理
                loop = asyncio.get_event_loop()
                loop.create_task(self.handle_data(reader, writer, 'camera'))
            elif message.startswith('quit'):
                del self.clients_info[client_id]
                del self.client_conns[client_id]
                break
            print(f"Received message from {client_id}: {message}")

    async def log(self):
        while self.running:
            print(f'Server {self.conference_id} status: {len(self.clients_info)} clients connected')
            await asyncio.sleep(10)

    async def cancel_conference(self):
        self.running = False
        for conn in self.client_conns.values():
            conn.close()
        await asyncio.sleep(1)  # 等待连接关闭
        del self.main_server.conference_servers[self.conference_id]

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.log())
        loop.create_task(self.accept_clients())

    async def accept_clients(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.conf_serve_ports)
        await server.serve_forever()