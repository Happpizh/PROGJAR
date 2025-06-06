from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection,address):
    rcv = ""
    headers_received = False
    content_length = 0
    body = b""

    while True:
        try:
            data = connection.recv(1024)
            if not data:
                break
            if not headers_received:
                rcv += data.decode()
                if '\r\n\r\n' in rcv:
                    headers_part, rest = rcv.split('\r\n\r\n', 1)
                    headers_received = True
                    # Parsing Content-Length
                    lines = headers_part.split('\r\n')
                    for line in lines:
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    body = rest.encode()
                    if len(body) >= content_length:
                        # sudah lengkap
                        full_request = headers_part + '\r\n\r\n' + body.decode(errors='ignore')
                        hasil = httpserver.proses(full_request)
                        hasil += b"\r\n\r\n"
                        connection.sendall(hasil)
                        connection.close()
                        return
            else:
                body += data
                if len(body) >= content_length:
                    # Sudah lengkap body
                    headers_part = rcv.split('\r\n\r\n',1)[0]
                    full_request = headers_part + '\r\n\r\n' + body.decode(errors='ignore')
                    hasil = httpserver.proses(full_request)
                    hasil += b"\r\n\r\n"
                    connection.sendall(hasil)
                    connection.close()
                    return
        except OSError as e:
            pass
    connection.close()
    return




def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 8885))
	my_socket.listen(1)

	with ThreadPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				#logging.warning("connection from {}".format(client_address))
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)
				#menampilkan jumlah process yang sedang aktif
				jumlah = ['x' for i in the_clients if i.running()==True]
				print(jumlah)





def main():
	Server()

if __name__=="__main__":
	main()

