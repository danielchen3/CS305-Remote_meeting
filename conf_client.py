from util import *
import config
import asyncio

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
        self.share_conns = {}
        self.recv_conns = {}
        for i in self.support_data_types:
            self.share_conns = {i:None}
            self.recv_conns = {i:None}
        self.conference_info = (
            None  # you may need to save and update some conference_info regularly
        )
        self.recv_data = None  # you may need to save received streamd data from other clients in conference
    def TcpGet(self, request_message): # return a string
        print(f'send to server {request_message}')
        self.client_socket.sendall(request_message.encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        print(f'The response is {response}')
        return response
    def create_conference(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        """
        pass
        response = self.TcpGet(request_message = 'create')
        print(f'Create a meeting {response}')
        self.join_conference(response)
    def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        pass
        response = self.TcpGet(request_message = f'join {int(conference_id)}')
        if response is not 'error':
            self.on_meeting = True
            self.conference_info = conference_id
            self.start_conference()
    def quit_conference(self):
        """
        quit your on-going conference
        """
        pass
        response = self.TcpGet(request_message = 'quit')
        if response is not 'error':
            self.on_meeting = False
            self.conference_info = None
            self.close_conference()
            
    def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        pass
        response = self.TcpGet(request_message = 'cancel')
        if response is not 'error':
            self.on_meeting = False
            self.conference_info = None
            self.close_conference()
        
    def keep_share(
        self, data_type, send_conn, capture_function, compress=None, fps_or_frequency=30
    ):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        pass

    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        if self.share_conns[data_type] is None:
            self.share_conns[data_type] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.share_conns[data_type].connect((config.SERVER_IP, config.MAIN_SERVER_PORT))
        else:
            self.share_conns[data_type].close()
            self.share_conns[data_type] = None

    def keep_recv(self, recv_conn, data_type, decompress=None):
        """
        running task: keep receiving certain type of data (save or output)
        you can create other functions for receiving various kinds of data
        """
        self.recv_data = self.client_socket.recv(1024).decode('utf-8')

    def output_data(self):
        """
        running task: output received stream data
        """ 
        self.conns.sendall(self.recv_data.encode('utf-8'))

    async def run(self):
        print('In the meeting')
        for type in self.support_data_types:
            self.recv_conns[type] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.recv_conns[type].connect((config.SERVER_IP, config.MAIN_SERVER_PORT))
        while True:
            for key, value in self.share_conns():
                if value != None:
                    self.keep_share(value, key)
            for type in self.support_data_types:
                self.keep_recv()
                self.output_data()
            if self.recv_data == 'quit': #收到quit则终止
                break
        for type in self.support_data_types:
            self.recv_conns[type].close()
            self.recv_conns[type] = None
        print('Quit')

    def start_conference(self):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        import os
        os.system("python ui.py")
        self.conns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conns.connect(('127.0.0.1', UI_PORT))
        asyncio.create_task(self.run())

    def close_conference(self):
        """
        close all conns to servers or other clients and cancel the running tasks
        pay attention to the exception handling
        """
        self.conns.close()
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
            print(f"Server response: {data.decode()}")
            if "logged in" in data.decode():
                break
        while True:
            if not self.on_meeting:
                status = "Free"
            else:
                status = f"OnMeeting-{self.conference_id}"

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
                    self.create_conference()
                elif cmd_input == "quit":
                    self.quit_conference()
                elif cmd_input == "cancel":
                    self.cancel_conference()
                elif cmd_input == "exit":
                    break
                else:
                    recognized = False
            elif len(fields) == 2:
                if fields[0] == "join":
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        self.join_conference(input_conf_id)
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
