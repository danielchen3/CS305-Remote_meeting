# from util import *
import threading
import config
import asyncio
import multiprocessing
import json
import time
from ui import APP
import socket
from new_ui import new_APP


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))  # 绑定到端口0，操作系统自动分配空闲端口
        return s.getsockname()[1]  # 返回绑定的端口号


class ConferenceClient:
    def __init__(
        self,
    ):
        # sync client
        self.is_working = True
        self.on_meeting = False  # status
        self.conns = (
            None  # you may need to maintain multiple conns for a single conference
        )
        self.client_socket = None
        self.support_data_types = ["text"]  # for some types of data
        self.switch = {}
        for i in self.support_data_types:
            self.switch[i] = False
        self.conference_info = (
            None  # you may need to save and update some conference_info regularly
        )
        self.recv_data = None  # you may need to save received streamd data from other clients in conference

    async def create_conference(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "create"}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        if response["status"] == True:
            ID = response["message"].split()[2]
            # port = response['message'].split()[3]
            print(f"Create a meeting {ID}")
            return ID

    async def create_conference_p2p(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "p2p"}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        if response["status"] == True:
            ID = response["message"].split()[2]
            # IP = response["message"].split()[3]
            # PORT = response["message"].split()[4]
            # port = response['message'].split()[3]
            print(f"Create a meeting {ID}")
            return ID

    async def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        reader, writer = self.conns[0], self.conns[1]
        # print(f"conf_id{conference_id}")
        message = {"type": "join", "conference_id": conference_id}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        port, is_p2p, p2p_ip, new_port = None, None, None, None
        if response["status"] == True:
            self.on_meeting = True
            port = response["message"].split()[3]
            is_p2p = response["message"].split()[4]
            # 如果是p2p模式，返回对方的IP，如果不是应该是"successfully"
            p2p_ip = response["message"].split()[5]
            # return port, is_p2p, p2p_ip
        else:
            return None

        from config import P2P_own_IP

        new_port = get_free_port()
        if is_p2p == "1":
            print("Joining p2p mode conference 2")
            message = {
                "type": "join_p2p",
                "conference_id": conference_id,
                "ip": P2P_own_IP,
                "port": new_port,
            }
            writer.write(json.dumps(message).encode())  # 异步发送数据
            await writer.drain()  # 确保数据已发送
            data = await reader.read(100)
            response = json.loads(data.decode())
            print(f"receive response is {response}")
        return port, is_p2p, p2p_ip, new_port

    async def quit_conference(self):
        """
        quit your on-going conference
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "quit"}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        print("sent quit message")
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        if response["status"] == True:
            print(f"Quit successfully")
            self.on_meeting = False

    async def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "cancel"}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        if response["status"] == True:
            print(f"cancel successfully")

    async def send_p2p_ip_port(self, id, ip, port):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "send_p2p", "conference_id": id, "ip": ip, "port": port}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        if response["status"] == True:
            data = await reader.read(100)
            response = json.loads(data.decode())
            print(f"receive response is {response}")
            if response["status"] == True:
                peer_ip = response["peer_ip"]
                peer_port = response["peer_port"]
                return peer_ip, peer_port

    async def keep_share(
        self, writer, data_type, capture_function, compress=None, fps_or_frequency=30
    ):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        while self.on_meeting:
            if self.switch[data_type] == True:
                message = {data_type: "test text!test text!test text!"}
                writer.write(json.dumps(message).encode())  # 异步发送数据
                await writer.drain()  # 确保数据已发送

    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        self.switch[data_type] ^= 1

    async def keep_recv(self, reader, data_type, decompress=None):
        """
        running task: keep receiving certain type of data (save or output)
        you can create other functions for receiving various kinds of data
        """
        while self.on_meeting:
            data = await reader.read(100)
            if not data:
                break
            response = json.loads(data.decode())
            print(f"receive response is {response}")
            self.recv_data = response

    async def view(self):
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "view"}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        # print(f"data is{data}")
        response = json.loads(data.decode("utf-8"))
        print(f"receive response is {response}")

    async def run(self, reader, writer):
        print("In the meeting")
        for type in self.support_data_types:
            # reader, writer = await asyncio.open_connection(config.SERVER_IP, config.MAIN_SERVER_PORT)
            await self.keep_recv(reader, type)
            await self.keep_share(writer, type)
        print("Quit run")

    def start_conference(self, port, ip=config.SERVER_IP):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        app = APP()
        app.start(self.id, ip, port)

    def start_conference_p2p(self, ip, port, peer_ip, peer_port):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        print(f"peer_ip is {peer_ip}, peer_port is {peer_port}")
        print(f"ip is {ip}, port is {port}")
        app = new_APP(port)
        app.start(peer_ip, peer_port, self.id, ip, port)

    def close_conference(self):
        """
        close all conns to servers or other clients and cancel the running tasks
        pay attention to the exception handling
        """
        print("close conference")

    async def connect_to_peer(self, host, port):
        """连接到对等端的服务器"""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            # 保存连接信息用于后续通信
            self.peer_writer = writer
            self.peer_reader = reader
            return True
        except Exception as e:
            print(f"Failed to connect to peer: {e}")
            return False

    async def handle_peer(self, reader, writer):
        """处理新peer连接的回调函数"""
        print("get_user")
        peer_addr = writer.get_extra_info("peername")
        print(f"New peer connected from {peer_addr}")

        # 接收peer发送的消息
        try:
            data = await reader.read(1024)
            message = data.decode()
            print(f"Received from peer: {message}")

            # 解析peer发送的端口信息
            peer_port = int(message)

            # 启动会议
            self.start_conference(peer_port)

        except Exception as e:
            print(f"Error handling peer connection in handle peer: {e}")

        # 保持连接以便后续通信
        await self.handle_peer(reader, writer)

    async def quit_conference_p2p(self):
        reader, writer = self.conns[0], self.conns[1]
        message = {"type": "quitp2p"}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        print("sent quitp2p message")
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f"receive response is {response}")
        if response["status"] == True:
            print(f"Quitp2p successfully")
            self.on_meeting = False

    async def start(self):
        """
        execute functions based on the command line input
        """
        reader, writer = await asyncio.open_connection(
            config.SERVER_IP, config.MAIN_SERVER_PORT
        )
        self.conns = (reader, writer)
        while True:
            self.id = input("please enter your ID:").strip()
            message = self.id
            writer.write(message.encode())  # 异步发送数据
            await writer.drain()  # 确保数据已发送
            data = await reader.read(100)
            print(f"Server response: {data.decode()}\n")
            if "logged in" in data.decode():
                break
        while True:
            if not self.on_meeting:
                status = "Free"
            else:
                status = f"OnMeeting-{self.conference_info}"

            print(f"Now status is {status}")
            recognized = True
            cmd_input = (
                input(f'({status}) Please enter a operation (enter "?" to help): ')
                .strip()
                .lower()
            )
            fields = cmd_input.split(maxsplit=1)
            if len(fields) == 1:
                if cmd_input in ("?", "？"):
                    print(config.HELP)
                elif cmd_input == "create":
                    ID = await self.create_conference()
                    PORT, _, _, _ = await self.join_conference(ID)
                    if PORT is None:
                        print("cofenrence is not exist")
                        continue
                    self.start_conference(PORT)
                    await self.quit_conference()
                    self.close_conference()
                elif cmd_input == "quit":
                    await self.quit_conference()
                    self.close_conference()
                    # message = {"hello!!!!"}
                    # writer.write(json.dumps(message).encode())  # 异步发送数据
                    # await writer.drain()  # 确保数据已发送
                elif cmd_input == "cancel":
                    await self.cancel_conference()
                elif cmd_input == "view":
                    await self.view()
                elif cmd_input == "exit":
                    break
                else:
                    recognized = False
            elif len(fields) == 2:
                if fields[0] == "join":
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        result = await self.join_conference(input_conf_id)
                        print(f"result is {result}")
                        if result is None:
                            print("conference is not exist")
                            continue
                        else:
                            port, is_p2p, p2p_ip, p2p_free_port = result
                            if is_p2p == "1":
                                print("Joining p2p mode conference")
                                # 这个地方开启joiner的服务器
                                from config import P2P_own_IP

                                self.start_conference_p2p(
                                    P2P_own_IP, p2p_free_port, p2p_ip, port
                                )
                                await self.quit_conference_p2p()
                                self.close_conference()
                                # 这个port是给client分配的用来开服务器的端口
                                # self.start_conference(port, p2p_ip)
                            else:
                                self.start_conference(port)
                                await self.quit_conference()
                    else:
                        print("[Warn]: Input conference ID must be in digital form")
                elif fields[0] == "switch":
                    data_type = fields[1]
                    if data_type in self.share_data.keys():
                        self.share_switch(data_type)
                # p2p mode
                elif fields[0] == "create":
                    if fields[1] == "p2p":
                        # 这个PORT是给client分配的用来开服务器的端口
                        ID = await self.create_conference_p2p()
                        from config import P2P_own_IP

                        p2p_free_port = get_free_port()
                        peer_ip, peer_port = await self.send_p2p_ip_port(
                            ID, P2P_own_IP, p2p_free_port
                        )
                        self.start_conference_p2p(
                            P2P_own_IP, p2p_free_port, peer_ip, peer_port
                        )
                        await self.quit_conference_p2p()
                        self.close_conference()
                        # self.p2p_server = await asyncio.start_server(
                        #     self.handle_peer, host=P2P_own_IP, port=p2p_free_port
                        # )
                        # print(
                        #     f"P2P server start on {P2P_own_IP} : {p2p_free_port}, waiting for connection..."
                        # )
                        # self.p2p_server_task = asyncio.create_task(self.p2p_server.serve_forever())
                        # await asyncio.sleep(2)

                        # 方案2: 使用async with确保服务器运行

                        # PORT = await self.join_conference(ID)
                        # port, is_p2p, p2p_ip = await self.join_conference(ID)
                        # self.start_conference(p2p_free_port, P2P_own_IP)
                        # await self.quit_conference_p2p()
                        # self.close_conference()
                        pass
                    else:
                        recognized = False
                else:
                    recognized = False
            else:
                recognized = False

            if not recognized:
                print(f"[Warn]: Unrecognized cmd_input {cmd_input}")
        print("Client closed")


if __name__ == "__main__":
    client1 = ConferenceClient()
    asyncio.run(client1.start())
