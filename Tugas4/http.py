import sys
import os.path
import uuid
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.thedir = './'

    def response(self, kode=404, message='Not Found', messagebody=b'', headers=None):
        if headers is None:
            headers = {}
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n".format(kode, message))
        resp.append("Date: {}\r\n".format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n".format(len(messagebody)))
        for kk in headers:
            resp.append("{}: {}\r\n".format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ''.join(resp)
        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        return response

    def proses(self, data):
        print("DEBUG: Received raw data:\n", data)  # DEBUG
        # Pisahkan header dan body (jika ada)
        parts = data.split("\r\n\r\n", 1)
        header_part = parts[0]
        body_part = parts[1] if len(parts) > 1 else ''

        requests = header_part.split("\r\n")
        if not requests or len(requests[0].split()) < 2:
            print("DEBUG: Bad request line or no request found")  # DEBUG
            return self.response(400, 'Bad Request', '', {})

        baris = requests[0]
        all_headers = [n for n in requests[1:] if n != '']

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()
            print(f"DEBUG: Method={method}, Path={object_address}")  # DEBUG

            headers = {}
            for h in all_headers:
                if ':' in h:
                    k, v = h.split(':', 1)
                    headers[k.strip().lower()] = v.strip()
            print("DEBUG: Headers:", headers)  # DEBUG

            if method == 'GET':
                return self.http_get(object_address, headers)
            elif method == 'POST':
                return self.http_post(object_address, headers, body_part)
            elif method == 'UPLOAD':
                return self.http_upload(object_address, headers, body_part)
            elif method == 'LIST':
                return self.http_list(object_address, headers)
            elif method == 'DELETE':
                return self.http_delete(object_address, headers)
            else:
                print("DEBUG: Unsupported method")  # DEBUG
                return self.response(400, 'Bad Request', 'Unsupported method', {})
        except IndexError:
            print("DEBUG: IndexError in parsing request")  # DEBUG
            return self.response(400, 'Bad Request', '', {})

    def http_get(self, object_address, headers):
        print(f"DEBUG: http_get called with path={object_address}")  # DEBUG
        if object_address == '/':
            return self.response(200, 'OK', 'Ini Adalah web Server percobaan', {})

        if object_address == '/video':
            return self.response(302, 'Found', '', {'Location': 'https://youtu.be/katoxpnTf04'})

        if object_address == '/santai':
            return self.response(200, 'OK', 'santai saja', {})

        object_address = object_address[1:]
        filepath = os.path.join(self.thedir, object_address)
        print(f"DEBUG: Trying to read file at {filepath}")  # DEBUG

        if not os.path.isfile(filepath):
            print("DEBUG: File not found")  # DEBUG
            return self.response(404, 'Not Found', 'File tidak ditemukan', {})

        with open(filepath, 'rb') as fp:
            isi = fp.read()
        print(f"DEBUG: File read success, size={len(isi)} bytes")  # DEBUG

        fext = os.path.splitext(filepath)[1]
        content_type = self.types.get(fext, 'application/octet-stream')
        headers = {'Content-Type': content_type}

        return self.response(200, 'OK', isi, headers)

    def http_post(self, object_address, headers, body):
        print(f"DEBUG: http_post called on {object_address}")  # DEBUG
        return self.response(200, 'OK', 'POST request diterima', {})

    def http_upload(self, object_address, headers, body):
        print(f"DEBUG: http_upload called on {object_address}")  # DEBUG
        object_address = object_address[1:]
        if object_address == '':
            print("DEBUG: Upload failed, filename kosong")  # DEBUG
            return self.response(400, 'Bad Request', 'Nama file tidak boleh kosong', {})

        filepath = os.path.join(self.thedir, object_address)
        print(f"DEBUG: Upload filepath = {filepath}")  # DEBUG
        try:
            content_length = int(headers.get('content-length', len(body)))
            print(f"DEBUG: Content-Length header = {content_length}, actual body length = {len(body)}")  # DEBUG

            if len(body) < content_length:
                print("DEBUG: Data upload tidak lengkap")  # DEBUG
                return self.response(400, 'Bad Request', 'Data upload tidak lengkap', {})

            if isinstance(body, str):
                body_bytes = body.encode()
            else:
                body_bytes = body

            with open(filepath, 'wb') as f:
                f.write(body_bytes)
            print("DEBUG: File upload successful")  # DEBUG

            return self.response(201, 'Created', 'File berhasil diupload', {})
        except Exception as e:
            print(f"DEBUG: Exception during upload: {e}")  # DEBUG
            return self.response(500, 'Internal Server Error', 'Gagal upload: {}'.format(str(e)), {})

    def http_list(self, object_address, headers):
        files = os.listdir(self.thedir)
        files = [f for f in files if os.path.isfile(os.path.join(self.thedir, f))]
        file_list_str = "\n".join(files)
        return self.response(200, 'OK', file_list_str, {'Content-Type': 'text/plain'})

    def http_delete(self, object_address, headers):
        object_address = object_address[1:]
        filepath = os.path.join(self.thedir, object_address)
        if not os.path.isfile(filepath):
            return self.response(404, 'Not Found', 'File tidak ditemukan', {})

        try:
            os.remove(filepath)
            return self.response(200, 'OK', 'File berhasil dihapus', {})
        except Exception as e:
            return self.response(500, 'Internal Server Error', 'Gagal menghapus file: {}'.format(str(e)), {})


if __name__ == "__main__":
    httpserver = HttpServer()

    # Test manual (bisa dihapus nanti)
    d = httpserver.proses('LIST / HTTP/1.0\r\n\r\n')
    print(d.decode())

    upload_data = 'UPLOAD /testupload.txt HTTP/1.0\r\nContent-Length: 13\r\n\r\nHello, upload!'
    d = httpserver.proses(upload_data)
    print(d.decode())

    d = httpserver.proses('GET /testupload.txt HTTP/1.0\r\n\r\n')
    print(d.decode())

    d = httpserver.proses('DELETE /testupload.txt HTTP/1.0\r\n\r\n')
    print(d.decode())
