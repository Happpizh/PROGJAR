import os
import socket
import json
import base64
import logging
import argparse
import time
import csv
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_command(server_ip, server_port, command_str=""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, server_port))
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = ""
        while True:
            data = sock.recv(1048576)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        return json.loads(data_received.strip())
    except Exception as e:
        return {"status": "ERROR", "data": str(e)}
    finally:
        sock.close()

def remote_upload(server_ip, server_port, filepath=""):
    try:
        with open(filepath, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
        filename = os.path.basename(filepath)
        command_str = f"UPLOAD {filename} {encoded}"
        return send_command(server_ip, server_port, command_str)
    except Exception as e:
        return {"status": "ERROR", "data": str(e)}

def remote_download(server_ip, server_port, filename=""):
    command_str = f"GET {filename}"
    result = send_command(server_ip, server_port, command_str)
    if result.get('status') == 'OK':
        namafile = result.get('data_namafile')
        isifile = base64.b64decode(result.get('data_file'))
        save_path = f"download_{namafile}"
        with open(save_path, 'wb') as fp:
            fp.write(isifile)
            fp.flush()
            os.fsync(fp.fileno())
        #print("File saved, size:", os.path.getsize(save_path))
    return result

def worker_task(server_ip, server_port, operation, filepath):
    start_time = time.time()
    if operation == "upload":
        result = remote_upload(server_ip, server_port, filepath)
        byte_size = os.path.getsize(filepath) if result.get('status') == 'OK' else 0
    elif operation == "download":
        result = remote_download(server_ip, server_port, filepath)
        try:
            byte_size = os.path.getsize(f"download_{filepath}") if result.get('status') == 'OK' else 0
        except:
            byte_size = 0
    else:
        result = {"status": "ERROR", "data": "Unknown operation"}
        byte_size = 0
    duration = time.time() - start_time
    return (result.get('status') == 'OK', duration, byte_size)

def stress_test(server_ip, server_port, operation, file_path, pool_mode, pool_size, server_workers, nomor, output_csv):
    executor_cls = ThreadPoolExecutor if pool_mode == "thread" else ProcessPoolExecutor
    results = []
    start_all = time.time()

    with executor_cls(max_workers=pool_size) as executor:
        futures = [executor.submit(worker_task, server_ip, server_port, operation, file_path) for _ in range(pool_size)]
        for f in futures:
            results.append(f.result())

    total_time = time.time() - start_all
    success_count = sum(1 for r in results if r[0])
    fail_count = pool_size - success_count
    total_bytes = sum(r[2] for r in results)
    throughput = total_bytes / total_time if total_time > 0 else 0
    avg_time = total_time / pool_size if pool_size > 0 else 0

    if operation == "download":
        save_path = f"download_{file_path}"
        file_volume = os.path.getsize(save_path) if os.path.exists(save_path) else 0
    else:
        file_volume = os.path.getsize(file_path) if os.path.exists(file_path) else 0

    file_volume_str = f"{round(file_volume / 1024 / 1024)}MB"
    
    header = [
        "Nomor", "Operasi", "Volume", "Jumlah client worker pool", "Jumlah server worker pool",
        "Waktu total per client", "Throughput per client",
        "Jumlah worker client yang sukses dan gagal", "Jumlah worker server yang sukses dan gagal"
    ]
    row = [
        nomor, operation, file_volume_str, pool_size, server_workers,
        round(avg_time, 3), round(throughput / pool_size, 3),
        f"{success_count} sukses, {fail_count} gagal",
        f"{server_workers} server worker (manual input)"
    ]
    write_header = not os.path.exists(output_csv)

    with open(output_csv, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)

    print(f"Hasil stress test disimpan ke {output_csv}")
    print("Data:", row)

    # Logging output
    log_message = f"""
[STRESS TEST RESULT]
Nomor                                : {nomor}
Operasi                              : {operation}
Volume                               : {file_volume_str}
Jumlah client worker pool            : {pool_size}
Jumlah server worker pool            : {server_workers}
Waktu total per client               : {round(avg_time, 3)} detik
Throughput per client                : {round(throughput / pool_size, 3)} byte/detik
Jumlah worker client sukses/gagal    : {success_count} sukses, {fail_count} gagal
"""
    logging.info(log_message)

def main():
    parser = argparse.ArgumentParser(description="Simple stress test client")
    parser.add_argument("--server", default="172.16.16.102", help="Server IP address")
    parser.add_argument("--port", type=int, default=5666, help="Server port")
    parser.add_argument("--file", required=True, help="File path for upload or filename for download")
    parser.add_argument("--pool_size", type=int, default=1, help="Number of concurrent workers")
    args = parser.parse_args()

    # default yang tidak perlu dikontrol dari command line
    mode = "stress"
    pool_mode = "process"       # bisa diganti 'process' atau 'threa' jika diinginkan
    server_workers = 0         # placeholder, karena seharusnya dari sisi server
    nomor = 1
    output = "stress_test_report.csv"

    stress_test(
        args.server, args.port, "download", args.file,
        pool_mode, args.pool_size, server_workers,
        nomor, output
    )

if __name__ == "__main__":
    main()
