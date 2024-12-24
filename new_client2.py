import asyncio
import threading

from new_ui import APP

if __name__ == "__main__":
    app = APP("8889","2")
    print("start_connection")
    app.start("1", '10.27.96.101', "8887", "2", '10.27.96.101', "8889")