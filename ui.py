import socket
import config

def start_server(host='127.0.0.1', port=config.UI_PORT):
    # 创建 TCP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 绑定到指定的 IP 地址和端口
    server_socket.bind((host, port))
    
    # 开始监听连接
    server_socket.listen(5)
    print(f"服务器启动，正在监听 {host}:{port}...")

    while True:
        # 等待客户端连接
        client_socket, client_address = server_socket.accept()
        print(f"客户端 {client_address} 已连接。")
        
        try:
            # 接收客户端发送的数据
            while True:
                data = client_socket.recv(1024)  # 每次接收 1024 字节数据
                if not data:
                    break  # 客户端关闭连接，退出循环
                print(f"收到数据: {data.decode('utf-8')}")  # 输出接收到的数据
        except Exception as e:
            print(f"接收数据时发生错误: {e}")
        finally:
            # 关闭与客户端的连接
            client_socket.close()
            print(f"客户端 {client_address} 断开连接。")
            break
            

if __name__ == "__main__":
    start_server()
