import socket
import threading
import pickle
import os
import time
from swarm import swarm

CONN_TEST_TIME = 4

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def is_socket_closed(s):
    try:
        obj = pickle.dumps('testing conn')
        s.sendall(obj)
    except BlockingIOError:
        return False  # socket is open and reading from it would block
    except ConnectionResetError:
        return True  # socket was closed for some other reason
    except Exception as e:
        # logger.exception("unexpected exception when checking if a socket is closed")
        return True
    return False

class Manager:
    PORT = 1234
    s: socket.socket
    connections: dict[(str, int), socket.socket]
    last_check: dict[(str, int), float]
    def __init__(self, port=1234):
        
        self.IP = get_local_ip()
        self.PORT = port
        print(f"Tracker is running on {self.IP}:{self.PORT}")

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.IP, self.PORT))
        self.s.listen(10)

        self.connections = {}
        self.check_conn = {}
        self.torrent_dict = {}
        self.last_check = {}
    
    def remove_peer(self, addr):
        conn = self.connections[addr]
        conn.close()
        self.connections.pop(addr)
        self.last_check.pop(addr)
        for info_hash in self.torrent_dict.keys():
            if addr in self.torrent_dict[info_hash].peers.keys():
                self.torrent_dict[info_hash].remove_peer(addr)
        print(f"Peers {addr}'s connection has stopped")

    def periodically_check_connection(self):
        while True:
            current_time = time.time()
            closed_connections = []  # stores the keys for closed connections
            for addr, last_time in self.last_check.items():
                if current_time - last_time > CONN_TEST_TIME:
                    closed_connections.append(addr)

            for addr in closed_connections:
                self.remove_peer(addr)

            time.sleep(CONN_TEST_TIME)
    def receive_message_from_peer(self, conn:socket.socket, addr):
        while True:
            try:
                message = pickle.loads(conn.recv(1024 * 1024))
                if message['type'] == 'stay connected':
                    self.last_check[addr] = time.time()
                elif message['type'] == 'close':
                    self.remove_peer(addr)
                    break
                elif message['type'] == 'upload':
                    info_hash = message['info_hash']
                    torrent_file = message['torrent']
                    if info_hash not in self.torrent_dict:
                        self.torrent_dict[info_hash] = swarm(torrent_file)
                    self.torrent_dict[info_hash].add_peer(message['addr'], True)
                    print(message['info_hash'], message['torrent'].info['name'], message['addr'])
                elif message['type'] == 'get peers':
                    info_hash = message['info_hash']
                    if info_hash not in self.torrent_dict or self.torrent_dict[info_hash].complete_peers == set():
                        message = pickle.dumps({
                            'type': 'not available',
                        })
                        conn.sendall(message)
                        continue
                    self.torrent_dict[info_hash].add_peer(addr, False)
                    peers = list(self.torrent_dict[info_hash].complete_peers)
                    message = pickle.dumps({
                        'type': 'available',
                        'peers with file': peers,
                        'torrent': self.torrent_dict[info_hash].torrent_file,
                    })
                    conn.sendall(message)
                elif message['type'] == 'downloaded chunk':
                    chunk_no = message['chunk_no']
                    info_hash = message['info_hash']
                    self.torrent_dict[info_hash].update(addr, chunk_no)
                elif message['type'] == 'get rarest chunks':
                    info_hash = message['info_hash']
                    available_peer_num = message['available_peer_num']
                    received_chunks = message['received_chunks']
                    message = pickle.dumps({
                        'type': 'rarest chunk',
                        'chunks': self.torrent_dict[info_hash].get_rarest_chunks(available_peer_num, received_chunks),
                    })
                    conn.sendall(message)
                elif message['type'] == 'downloaded':
                    info_hash = message['info_hash']
                    self.torrent_dict[info_hash].complete_peers.add(addr)
                    print("Peers holding file:", list(self.torrent_dict[info_hash].complete_peers))
                        
            except Exception as e:
                print(e)
                print(f"Connection from peer {addr} is closed")
                return

    def accept_connetions(self):
        while True:
            try:
                self.s.listen()
                conn, _ = self.s.accept()
                try:
                    message = pickle.loads(conn.recv(1024))
                except Exception as e:
                    print(e)
                    return
                
                if message['type'] != 'connect':
                    return
                addr = message['addr']
                print("Accept connection from peer:", addr)
                self.connections[addr] = conn

                recv_msg_peer_thread = threading.Thread(target=self.receive_message_from_peer, args=(conn, addr), daemon=True)
                recv_msg_peer_thread.start()
            except Exception as e:
                print(e)
    
    # def periodically_check_connection(self):
    #     while True:
    #         closed_connections = []  # stores the keys for closed connections
    #         for addr, c in self.connections.items():
    #             if is_socket_closed(c):
    #                 closed_connections.append(addr)

    #         for addr in closed_connections:
    #             self.connections.pop(addr)

    #         time.sleep(CONN_TEST_TIME)

    def run(self):
        print("Tracker is up and running")
        accept_thread = threading.Thread(target=self.accept_connetions, daemon=True)
        accept_thread.start()
        periodically_check_connection_thread = threading.Thread(target=self.periodically_check_connection, daemon=True)
        periodically_check_connection_thread.start()
        while True:
            inp = input()
            if inp == "close":
                os._exit(0)
            elif inp == "get peers":
                for addr in self.connections.keys():
                    print(addr)

def main():
    t = Manager()
    t.run()

if __name__ == "__main__":
    main()

