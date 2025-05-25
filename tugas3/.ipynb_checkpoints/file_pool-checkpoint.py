from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor

from file_protocol import FileProtocol

fp = FileProtocol()

def process_client(connection, address):
    rcv = ""
    while True:
        try:
            data = connection.recv(32)
            if data:
                d = data.decode()
                rcv += d
                if rcv.endswith("\r\n\r\n"):
                    hasil = fp.proses_string(rcv.strip())
                    hasil = hasil + "\r\n\r\n"
                    connection.sendall(hasil.encode())
                    rcv = ""
                    break
            else:
                break
        except Exception as e:
            logging.warning(f"Error: {str(e)}")
            break
    connection.close()

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=6666, max_workers=20):
        self.ipinfo = (ipaddress, port)
        self.max_workers = max_workers
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        logging.warning(f"Server berjalan di {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(10)

        with ThreadPoolExecutor(self.max_workers) as executor:
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"Connection from {client_address}")
                executor.submit(process_client, connection, client_address)

def main():
    svr = Server(ipaddress='0.0.0.0', port=56666)
    svr.run()

if __name__ == "__main__":
    main()
