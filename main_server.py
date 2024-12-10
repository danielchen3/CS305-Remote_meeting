import asyncio
from config import *
# from util import *
from conf_server import ConferenceServer
import json
from collections import defaultdict
import socket

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))  # 绑定到端口0，操作系统自动分配空闲端口
        return s.getsockname()[1]  # 返回绑定的端口号


class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None

        self.conference_conns = {}
        self.conference_servers = defaultdict(
            set
        )  # self.conference_servers[conference_id] = ConferenceManager
        self.conference_creators = defaultdict(
            set
        )  # 会议创建者：conference_id -> creator_user_id
        self.user_conferences = defaultdict(
            set
        )  # 用户参与的会议：user_id -> conference_id
        self.client_connections = defaultdict(
            set
        )  # writer -> user_id # writer对于每个连接都是唯一的，所以可以直接使用，然后exit之后会清理writer
        self.writer_connect = defaultdict(set)  # user_id -> writer
        self.reader_connect = defaultdict(set)  # user_id -> reader
        self.conference_port = {}
    async def authenticate_user(self, reader, writer):
        """
        Authenticate the user on connection and store user ID.
        """
        while True:
            # writer.write(b"Please type in your ID:\n")
            await writer.drain()

            data = await reader.read(100)
            user_id = data.decode().strip()

            if not user_id:
                writer.write(b"Authentication failed. Disconnecting.\n")
                writer.close()
                await writer.wait_closed()
                return None

            # 检查用户ID是否已经存在
            if user_id in self.client_connections.values():
                # 如果ID已存在，提示用户重新输入
                writer.write(
                    b"Authentication failed. ID already exists, please try again: "
                )
                await writer.drain()
            else:
                self.client_connections[writer] = user_id
                self.writer_connect[user_id] = writer
                self.reader_connect[user_id] = reader
                print(f"User {user_id} authenticated.")
                writer.write(b"logged in")
                await writer.drain()
                break

        return user_id

    def get_user_id(self, writer):
        """
        Retrieve the user ID associated with a given writer.
        """
        return self.client_connections.get(writer)

    def handle_create_conference(self, user_id):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """
        print("Start create conf...")
        conference_id = len(self.conference_servers) + 1
        free_port = get_free_port()
        conf_server = ConferenceServer(
            free_port
        )
        print(f"user_id:{user_id} create conference:{conference_id}Port:{free_port}")
        self.conference_servers[conference_id] = conf_server
        # 将user_id加入创建者名单
        self.conference_creators[conference_id] = user_id
        self.client_connections[user_id] = conference_id
        asyncio.create_task(conf_server.start())
        print(f"Conference {conference_id}:{free_port} created by {user_id}.")
        self.conference_port[conference_id] = free_port
        return {
            "status": True,
            "message": f"Create conference {conference_id} {free_port} successfully",
        }

    def handle_join_conference(self, user_id, conference_id):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        conference_id = int(conference_id)
        print(f"conf:{conference_id}")
        if conference_id not in self.conference_servers.keys():
            return {"status": False, "error": "Conference not found"}

        # # 将user_id的会议集中加入会议, 触发conf_server类中的加入用户方法
        # asyncio.create_task(self.conference_servers[conference_id].accept_clients(self.reader_connect[user_id], self.writer_connect[user_id]))
        print(f"User {user_id} joined Conference {conference_id} held by {self.conference_creators[conference_id]}.")
        return {
            "status": True,
            "message": f"Joined Conference {conference_id} {self.conference_port[conference_id]} successfully",
        }

    def handle_quit_conference(self, user_id):
        """
        quit conference (in-meeting request & or no need to request)
        """
        # 如果不是这个会议的创建者，那么就只是退出，把会议从他的参与会议中移除
        conference_id = self.client_connections[user_id]

        if self.conference_creators.get(conference_id) != user_id:
            self.conference_servers[conference_id].quit_client(
                self.reader_connect[user_id], self.writer_connect[user_id]
            )
            return {
                "status": True,
                "message": f"User {user_id} has left conference {conference_id}.",
            }

        return self.handle_cancel_conference(
            user_id=user_id, conference_id=conference_id
        )

    def handle_cancel_conference(self, user_id, conference_id):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """

        conference_id = self.client_connections[user_id]

        if conference_id not in self.conference_servers:
            return {"status": False, "error": "Conference not found"}

        if self.conference_creators.get(conference_id) != user_id:
            return {"status": False, "error": "Only the creator can cancel"}

        # 取消的话，就把会议从会议列表中移除
        conf_server = self.conference_servers.pop(conference_id)
        # 调用conf_server的取消会议函数
        asyncio.create_task(conf_server.cancel_conference())
        del self.conference_creators[conference_id]

        # 把会议编号从每个参会者参会列表中移除
        for participants in self.user_conferences.values():
            participants.discard(conference_id)

        print(f"Conference {conference_id} canceled by {user_id}.")
        return {"status": True, "message": f"Conference {conference_id} canceled"}

    def get_active_conferences(self):
        if not self.conference_servers:
            return {"status": False, "message": "No active conferences available."}

        active_conferences = [
            {"conference_id": conf_id, "creator": self.conference_creators[conf_id]}
            for conf_id in self.conference_servers
        ]
        return {"status": True, "message": active_conferences}

    async def request_handler(self, reader, writer):
        """
        running task: handle out-meeting (or also in-meeting) requests from clients
        """
        # 第一次连接请求用户发送自己的id进行认证
        
        print("get_user")
        
        user_id = self.get_user_id(writer)
        # 如果没有认证，需要进行认证
        if not user_id:
            user_id = await self.authenticate_user(reader, writer)
            if not user_id:
                return  # 认证失败，断开连接
        while True:
            try:
                print("start awaiting")
                data = await reader.read(100)
                print("finish awaiting")
                if not data:
                    break  # 客户端断开连接

                message = json.loads(data.decode())
                print(f'receive {message}')
                response = {}

                # 根据请求类型处理
                if message["type"] == "create":
                    response = self.handle_create_conference(user_id)
                elif message["type"] == "join":
                    conference_id = message["conference_id"]
                    response = self.handle_join_conference(user_id, conference_id)
                elif message["type"] == "quit":
                    response = self.handle_quit_conference(user_id)
                elif message["type"] == "cancel":
                    # conference_id = message["conference_id"]
                    response = self.handle_cancel_conference(user_id)
                elif message["type"] == "view":
                    response = self.get_active_conferences()
                elif message["type"] == "exit":
                    break
                else:
                    response = {"status": False, "error": "Unknown request type"}
                print(response)
                writer.write(json.dumps(response).encode())
                await writer.drain()
                print("finish writing")
            except Exception as e:
                print(f"Error: {e}")
                break

        # 连接断开时清理信息
        self.client_connections.discard(writer)
        self.user_conferences.discard(user_id)
        writer.close()
        await writer.wait_closed()
        print(f"User {user_id} disconnected.")

    def start(self):
        """
        start MainServer
        """

        async def main():
            server = await asyncio.start_server(
                self.request_handler, self.server_ip, self.server_port
            )
            async with server:
                print(f"Server started on {self.server_ip}:{self.server_port}")
                await server.serve_forever()

        asyncio.run(main())


if __name__ == "__main__":
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    server.start()
