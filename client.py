#from util import *
import config
import asyncio
import multiprocessing
import json
import time
from ui import start_ui
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
        self.support_data_types = ['text']  # for some types of data
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
        message = {'type':'create'}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f'receive response is {response}')
        if response['status'] == True:
            ID = response['message'].split()[2]
            # port = response['message'].split()[3]
            print(f'Create a meeting {ID}')
            return ID
    async def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        reader, writer = self.conns[0], self.conns[1]
        # print(f"conf_id{conference_id}")
        message = {'type':'join', 'conference_id':conference_id}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f'receive response is {response}')
        if response['status'] == True:
            self.on_meeting = True
            port = response['message'].split()[3]
            return port

    async def quit_conference(self):
        """
        quit your on-going conference
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {'type':'quit'}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f'receive response is {response}')
        if response['status'] == True:
            print(f'Quit successfully')
            self.on_meeting = False
            
    async def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        reader, writer = self.conns[0], self.conns[1]
        message = {'type':'cancel'}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f'receive response is {response}')
        if response['status'] == True:
            print(f'cancel successfully')
        
    async def keep_share(
        self, writer, data_type, capture_function, compress=None, fps_or_frequency=30
    ):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        while self.on_meeting:
            if self.switch[data_type] == True:
                message = {data_type:'test text!test text!test text!'}
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
            print(f'receive response is {response}')
            self.recv_data = response
    async def view(self):
        reader, writer = self.conns[0], self.conns[1]
        message = {'type':'view'}
        writer.write(json.dumps(message).encode())  # 异步发送数据
        await writer.drain()  # 确保数据已发送
        data = await reader.read(100)
        response = json.loads(data.decode())
        print(f'receive response is {response}')

    async def run(self, reader, writer):
        print('In the meeting')
        for type in self.support_data_types:
            #reader, writer = await asyncio.open_connection(config.SERVER_IP, config.MAIN_SERVER_PORT)
            await self.keep_recv(reader, type)
            await self.keep_share(writer, type)
        print('Quit run')

    async def start_conference(self, port):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        start_ui(self.id, config.SERVER_IP, port)

    def close_conference(self):
        """
        close all conns to servers or other clients and cancel the running tasks
        pay attention to the exception handling
        """
        print('close conference')
    async def start(self):
        """
        execute functions based on the command line input
        """
        reader, writer = await asyncio.open_connection(config.SERVER_IP, config.MAIN_SERVER_PORT)
        self.conns = (reader, writer)
        while True:
            self.id = input('please enter your ID:').strip()
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

            print(f'Now status is {status}')
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
                    PORT = await self.join_conference(ID)
                    await self.start_conference(PORT)
                    await self.quit_conference()
                elif cmd_input == "quit":
                    await self.quit_conference()
                    self.close_conference()
                elif cmd_input == "cancel":
                    await self.cancel_conference()
                elif cmd_input == 'view':
                    await self.view()
                elif cmd_input == "exit":
                    break
                else:
                    recognized = False
            elif len(fields) == 2:
                if fields[0] == "join":
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        PORT = await self.join_conference(input_conf_id)
                        await self.start_conference(PORT)
                        await self.quit_conference()
                    else:
                        print("[Warn]: Input conference ID must be in digital form")
                elif fields[0] == "switch":
                    data_type = fields[1]
                    if data_type in self.share_data.keys():
                        self.share_switch(data_type)
                else:
                    recognized = False
            else:
                recognized = False

            if not recognized:
                print(f"[Warn]: Unrecognized cmd_input {cmd_input}")
        writer.close()
        print('Client closed')


if __name__ == "__main__":
    client1 = ConferenceClient()
    asyncio.run(client1.start())
