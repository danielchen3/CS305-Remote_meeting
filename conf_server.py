import asyncio
from util import *


class ConferenceServer:
    def __init__(
        self,
    ):
        # async server
        self.conference_id = None  # conference_id for distinguish difference conference
        self.conf_serve_ports = None
        self.data_serve_ports = {}
        self.data_types = [
            "screen",
            "camera",
            "audio",
        ]  # example data types in a video conference
        self.clients_info = None
        self.client_conns = None
        self.mode = "Client-Server"  # or 'P2P' if you want to support peer-to-peer conference mode

    async def handle_data(self, reader, writer, data_type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """

    async def handle_client(self, reader, writer):
        """
        running task: handle the in-meeting requests or messages from clients
        """

    async def log(self):
        while self.running:
            print("Something about server status")
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """

    def start(self):
        """
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        """
        pass
