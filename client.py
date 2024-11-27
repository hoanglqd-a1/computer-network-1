import socket
import threading
import pickle
import os
import time
from torrent import torrent
import hashlib
from file import completeFile, incompleteFile, PIECE_LENGTH
from piece_mapping import piece_mapping

PEERS_DIR = "./Peers/"
CONN_STAY_TIME = 2
PEER_TIMEOUT = 4
TRACKER_PORT = 1234

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

class Peer:
    manager_conn_socket: socket.socket
    my_socket: socket.socket
    manager_addr: tuple
    def __init__(self, port: int, name: str):
        self.port = port
        self.name = name
        self.ip = get_local_ip()
        self.directory = PEERS_DIR + name + "/"
        self.torrent_dir = self.directory + 'torrents/'
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)
        if not os.path.isdir(self.torrent_dir):
            os.mkdir(self.torrent_dir)
        
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.bind((self.ip, self.port))

    def connect_to_manager(self, ip, port=TRACKER_PORT):
        self.manager_conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.manager_addr = (ip, port)
        self.manager_conn_socket.connect(self.manager_addr)
        message = pickle.dumps({
            'type': 'connect',
            'addr': (self.ip, self.port),
        })
        self.manager_conn_socket.sendall(message)
    
    def periodically_announce_manager(self):
        while True:
            message = pickle.dumps({"type": "stay connected"})
            self.manager_conn_socket.sendall(message)
            time.sleep(CONN_STAY_TIME)

    def connect_to_peer(self, addr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(addr)
        except:
            print("Could not connect to ", addr)
        return sock
    def get_chunk_from_peer(self, torrent_file: torrent, peer_addr, chunk_no, incomp_file: incompleteFile, successed, world_chunk_no, file_index, i):
        sock = self.connect_to_peer(peer_addr)
        filename = torrent_file.info['files'][file_index]['name']
        message = pickle.dumps({
            "type": "request chunk",
            "filename": filename,
            "chunk_no": chunk_no,
        })
        sock.sendall(message)
        sock.settimeout(PEER_TIMEOUT)
        try:
            message = sock.recv(PIECE_LENGTH + 8192)
            # print(len(message), "bytes received")
            message = pickle.loads(message)
            if message['type'] == "response_chunk":
                assert hashlib.sha1(message['chunk']).hexdigest() == torrent_file.info['pieces'][world_chunk_no], "Hashes do not match"
                incomp_file.write_chunk(message['chunk'], chunk_no)
        except socket.timeout:
            print(f"peer {peer_addr} did not send the file")
        except pickle.UnpicklingError:
            print(f"failed to receive the chunk {chunk_no + 1}/{incomp_file.n_chunks} from {peer_addr}")
        except Exception as e:
            print("Error", e)
        else:
            print(f"received the chunk {chunk_no + 1}/{incomp_file.n_chunks} of file {filename} from {peer_addr}")
            successed[i][0] = True
        sock.sendall(pickle.dumps({"type": "close"}))
        sock.close()
    def accept_peers_connection(self):
        self.my_socket.listen(10)
        while True:
            try:
                conn, _ = self.my_socket.accept()
                recv_msg_peer_thread = threading.Thread(target=self.receive_message_from_peer, args=(conn,), daemon=True)
                recv_msg_peer_thread.start()
            except Exception as e:
                print("Exception 2", e)
    def receive_message_from_peer(self, conn:socket.socket):
        while True:
            try:
                conn.settimeout(PEER_TIMEOUT)
                message = conn.recv(8192)
                # print(len(message), "bytes received")
                message = pickle.loads(message)
                if message['type'] == 'request chunk':
                    filename = message['filename']
                    chunk_no = message['chunk_no']
                    file = completeFile(filename, self.name)
                    chunk = file.get_chunk_no(chunk_no)
                    message = pickle.dumps({
                        'type': 'response_chunk',
                        'chunk': chunk,
                    })
                    # message = pickle.dumps({
                    #     'type': 'test',
                    # })
                    # print(len(message), "bytes sent")
                    conn.sendall(message)
                    # print(len(message), "bytes sent")
                    # print(f"sent the chunk {chunk_no + 1}/{file.n_chunks}")
                elif message['type'] == 'close':
                    conn.close()
                    break
            except Exception as e:
                print("Exception 1", e)
                break
    
    def upload_file(self, filenames):
        file_names = filenames.split(',')
        file_dirs = []
        for file_name in file_names:
            file_dir = self.directory + file_name
            file_dirs.append(file_dir)
            if not os.path.isfile(file_dir):
                print(f"File {file_name} does not exist")
                file_dirs.remove(file_dir)

        torrent_file = torrent(file_dirs, PIECE_LENGTH, self.manager_addr[0], self.manager_addr[1])
        info_hash = torrent_file.get_info_hash()
        torrent_file.write_torrent(self.torrent_dir)
        message = pickle.dumps({
            'type': 'upload',
            'info_hash': info_hash,
            'addr': (self.ip, self.port),
            'torrent': torrent_file,
        })
        # print(len(message))
        self.manager_conn_socket.sendall(message)
        return info_hash
    
    def download_file(self, info_hash):
        self.manager_conn_socket.sendall(pickle.dumps({'type': 'get peers', 'info_hash': info_hash}))
        message = pickle.loads(self.manager_conn_socket.recv(8192))
        if message['type'] == 'not available':
            print("File is not available")
            return
        torrent_file = message['torrent']
        torrent_file.write_torrent(self.torrent_dir)
        file_infos = torrent_file.info['files']
        # receiving_file = incompleteFile(torrent_file.info['name'], self.name, torrent_file.info['size'])
        receiving_files = []
        for file_info in file_infos:
            receiving_file = incompleteFile(file_info['name'], self.name, file_info['size'])
            receiving_files.append(receiving_file)
        
        mapping = piece_mapping(file_infos, PIECE_LENGTH)
        total_chunks = sum(file_info['piece_cnt'] for file_info in mapping.file_infos)
        received_chunks = [False for _ in range(total_chunks)]
        
        start = time.time()
        while not all(received_chunks):
            self.manager_conn_socket.sendall(pickle.dumps({'type': 'get peers', 'info_hash': info_hash}))
            message = pickle.loads(self.manager_conn_socket.recv(8192))
            if message['type'] == 'not available':
                print("File is not available")
                return
            peers_with_file = message['peers with file']
            running_thread = []
            missing_chunks = [i for i in range(total_chunks) if not received_chunks[i]]
            successed = []
            for i, (missing_chunk, peer_addr) in enumerate(zip(missing_chunks, peers_with_file)):
                successed.append([False, missing_chunk])
                file_index, chunk_no = mapping.get_file_chunk_no(missing_chunk)
                receiving_file = receiving_files[file_index]
                get_chunk_thread = threading.Thread(
                    target=self.get_chunk_from_peer,
                    args=(torrent_file, peer_addr, chunk_no, receiving_file, successed, missing_chunk, file_index, i),
                    daemon=True,
                )
                get_chunk_thread.start()
                running_thread.append(get_chunk_thread)
            for thread in running_thread:
                thread.join()

            for success, missing_chunk in successed:
                received_chunks[missing_chunk] = success

            time.sleep(0.1)

        end = time.time()
        print(f"Time taken to download {torrent_file.info['name']} is {end - start} seconds")

        for receiving_file in receiving_files:
            receiving_file.write_file()
        print(f"File {torrent_file.info['name']} downloaded")
        self.manager_conn_socket.sendall(pickle.dumps({'type': 'downloaded', 'info_hash': info_hash, 'addr': (self.ip, self.port)}))

    def run(self):
        print("Running")
        tracker_ip = input("Enter tracker ip: ")
        tracker_port = int(input("Enter tracker port: "))
        self.connect_to_manager(tracker_ip, tracker_port)
        stay_conn_manager_thread = threading.Thread(target=self.periodically_announce_manager, daemon=True)
        stay_conn_manager_thread.start()
        accept_peers_connection_thread = threading.Thread(target=self.accept_peers_connection, daemon=True)
        accept_peers_connection_thread.start()
        while True:
            inp = input("Enter command: ")
            if inp == 'c' or inp == 'close':
                self.manager_conn_socket.sendall(pickle.dumps({'type': 'close'}))
                self.manager_conn_socket.close()
                break
            elif inp == 'upload':
                file_names = input("Enter file names: ")
                info_hash = self.upload_file(file_names)
                print("Info hash:", info_hash)
            elif inp == 'download':
                info_hash = input("Enter info hash: ")
                self.download_file(info_hash)
            elif inp == 'connect':
                peer_addr = input("Enter peer address: ")
                peer_addr = (peer_addr.split(':')[0], int(peer_addr.split(':')[1]))
                self.connect_to_peer(peer_addr)
            else:
                print("Invalid command, try again")

def main():
    port = int(input("Enter port: "))
    name = input("Enter name: ")
    peer = Peer(port, name)
    peer.run()

if __name__ == "__main__":
    main()