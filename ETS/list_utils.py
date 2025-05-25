import socket
import json
import argparse

def send_command(server_ip, server_port, command_str=""):
    # Pastikan command diakhiri \r\n\r\n sesuai protokol
    if not command_str.endswith("\r\n\r\n"):
        command_str += "\r\n\r\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, server_port))
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            data_received += data.decode()
            if "\r\n\r\n" in data_received:
                break
        return json.loads(data_received.strip())
    except Exception as e:
        return {"status": "ERROR", "data": str(e)}
    finally:
        sock.close()

def remote_list(server_ip, server_port):
    result = send_command(server_ip, server_port, "LIST")
    if result.get('status') == 'OK':
        print("Files on server:")
        for fname in result.get('data', []):
            print("-", fname)
    else:
        print("Failed to list files:", result.get('data'))

def main():
    parser = argparse.ArgumentParser(description="List files from server")
    parser.add_argument("--server", default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=5666, help="Server port")
    args = parser.parse_args()
    
    remote_list(args.server, args.port)

if __name__ == "__main__":
    main()

