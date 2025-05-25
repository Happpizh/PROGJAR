import socket
import os
import argparse
import logging
import base64
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process

HOST = '0.0.0.0'
PORT = 5666
BUFFER_SIZE = 1048576
STORAGE_DIR = 'storage'
LOG_FILE = 'server.log'

os.makedirs(STORAGE_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

def handle_client(conn, addr):
    thread_name = threading.current_thread().name
    try:
        logging.info(f"Connection from {addr}")

        data_received = ""
        while True:
            data = conn.recv(BUFFER_SIZE).decode()
            if not data:
                break
            data_received += data
            if "\r\n\r\n" in data_received:
                break
        logging.debug(f"Received data (truncated): {data_received[:100]}")

        #parts = data_received.strip().split()
        #if len(parts) < 2:
            #resp = json.dumps({"status": "ERROR", "data": "Invalid command format"}) + "\r\n\r\n"
            #conn.sendall(resp.encode())
            #return
        parts = data_received.strip().split()
        if not parts:
            resp = json.dumps({"status": "ERROR", "data": "Empty command"}) + "\r\n\r\n"
            conn.sendall(resp.encode())
            return

        command = parts[0].upper()

        # Tangani LIST secara terpisah karena tidak butuh argumen
        if command == "LIST":
            try:
                files = os.listdir(STORAGE_DIR)
                resp = json.dumps({
                    "status": "OK",
                    "data": files
                }) + "\r\n\r\n"
                conn.sendall(resp.encode())
                logging.info(f"Sent list of files to {addr}")
            except Exception as e:
                logging.error(f"Error listing files: {e}")
                resp = json.dumps({"status": "ERROR", "data": str(e)}) + "\r\n\r\n"
                conn.sendall(resp.encode())
            return

        # Untuk perintah lain, pastikan ada minimal 2 bagian
        if len(parts) < 2:
            resp = json.dumps({"status": "ERROR", "data": "Invalid command format"}) + "\r\n\r\n"
            conn.sendall(resp.encode())
            return


        command = parts[0].upper()
        filename = parts[1]
        filepath = os.path.join(STORAGE_DIR, filename)

        if command == "UPLOAD":
            if len(parts) < 3:
                resp = json.dumps({"status": "ERROR", "data": "No data to upload"}) + "\r\n\r\n"
                conn.sendall(resp.encode())
                return
            encoded_data = " ".join(parts[2:])
            try:
                file_data = base64.b64decode(encoded_data)
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                logging.info(f"Saved file {filename} from {addr}")
                resp = json.dumps({"status": "OK", "data": f"Uploaded {filename}"}) + "\r\n\r\n"
                conn.sendall(resp.encode())
            except Exception as e:
                logging.error(f"Error decoding/saving file {filename}: {e}")
                resp = json.dumps({"status": "ERROR", "data": str(e)}) + "\r\n\r\n"
                conn.sendall(resp.encode())

        elif command == "GET":
            if not os.path.exists(filepath):
                resp = json.dumps({"status": "ERROR", "data": "File not found"}) + "\r\n\r\n"
                conn.sendall(resp.encode())
                return
            with open(filepath, 'rb') as f:
                file_data = f.read()
            encoded_data = base64.b64encode(file_data).decode()
            resp = json.dumps({
                "status": "OK",
                "data_namafile": filename,
                "data_file": encoded_data
            }) + "\r\n\r\n"
            conn.sendall(resp.encode())
            logging.info(f"Sent file {filename} to {addr}")

        elif command == "LIST":
            try:
                files = os.listdir(STORAGE_DIR)
                resp = json.dumps({
                    "status": "OK",
                    "data": files
                }) + "\r\n\r\n"
                conn.sendall(resp.encode())
                logging.info(f"Sent list of files to {addr}")
            except Exception as e:
                logging.error(f"Error listing files: {e}")
                resp = json.dumps({"status": "ERROR", "data": str(e)}) + "\r\n\r\n"
                conn.sendall(resp.encode())

        else:
            resp = json.dumps({"status": "ERROR", "data": "Invalid command"}) + "\r\n\r\n"
            conn.sendall(resp.encode())

    except Exception as e:
        logging.error(f"Exception handling client {addr}: {e}")
        resp = json.dumps({"status": "ERROR", "data": str(e)}) + "\r\n\r\n"
        try:
            conn.sendall(resp.encode())
        except:
            pass
    finally:
        conn.close()
        logging.info(f"Closed connection from {addr}")

def start_server_threaded(workers):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(100)
        logging.info(f"Thread-pool server started on {HOST}:{PORT} with {workers} workers")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            while True:
                conn, addr = server_socket.accept()
                logging.info(f"Accepted connection from {addr}")
                executor.submit(handle_client, conn, addr)

def start_server_process(workers):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(100)
        logging.info(f"Process server started on {HOST}:{PORT} using multiprocessing.Process")

        active_processes = []
        while True:
            conn, addr = server_socket.accept()
            logging.info(f"Accepted connection from {addr}")
            p = Process(target=handle_client, args=(conn, addr))
            p.start()
            active_processes.append(p)

            # Optional: bersihkan proses yang sudah selesai
            active_processes = [proc for proc in active_processes if proc.is_alive()]

def main():
    parser = argparse.ArgumentParser(description="File server with multiple concurrency modes.")
    parser.add_argument('--mode', choices=['thread', 'process'], default='thread', help="Mode to run the server")
    parser.add_argument('--workers', type=int, default=1, help="Number of worker threads or processes")
    args = parser.parse_args()

    if args.mode == 'thread':
        start_server_threaded(args.workers)
    elif args.mode == 'process':
        start_server_process(args.workers)
    else:
        logging.error("Invalid mode selected.")

if __name__ == '__main__':
    main()
