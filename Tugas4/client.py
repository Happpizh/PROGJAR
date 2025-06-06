import socket
import sys
import os

SERVER_HOST = '172.16.16.101'
SERVER_PORT = 8885
CHUNK_SIZE = 1024

def send_request(request, data=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall(request.encode())
        if data:
            s.sendall(data)
        response = b''
        while True:
            chunk = s.recv(CHUNK_SIZE)
            if not chunk:
                break
            response += chunk
    return response.decode(errors='ignore')

def list_files():
    request = "LIST / HTTP/1.0\r\n\r\n"
    response = send_request(request)
    print("Response:\n", response)

def delete_file(filename):
    request = f"DELETE /{filename} HTTP/1.0\r\n\r\n"
    response = send_request(request)
    print("Response:\n", response)

def upload_file(filepath):
    if not os.path.exists(filepath):
        print("File not found:", filepath)
        return
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    request_header = f"UPLOAD /{filename} HTTP/1.0\r\nContent-Length: {file_size}\r\n\r\n"
    with open(filepath, 'rb') as f:
        file_data = f.read()
    response = send_request(request_header, file_data)
    print("Response:\n", response)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python client.py [list|upload|delete] [filename]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'list':
        list_files()
    elif command == 'upload' and len(sys.argv) == 3:
        upload_file(sys.argv[2])
    elif command == 'delete' and len(sys.argv) == 3:
        delete_file(sys.argv[2])
    else:
        print("Invalid command or missing filename.")

