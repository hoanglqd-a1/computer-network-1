import socket
import threading
import pickle
import os
import time
from torrent import torrent
import hashlib
from file import completeFile, incompleteFile, PIECE_LENGTH
from piece_mapping import piece_mapping

#ui
import queue
import customtkinter as ctk
from ui.ui import CenterWindowToDisplay, change_appearanceMode, change_widgetSize, login
from PIL import Image

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

        self.file_list = []
        
        #ui
        self.command_queue = queue.Queue()
        self.ui()

    def ui(self):
        self.root = ctk.CTk()
        self.root.title(self.name)
        self.root.geometry(CenterWindowToDisplay(self.root, 600, 600))
        ctk.set_default_color_theme("themes/my_theme.json")
        
        self.sidebar_frame = ctk.CTkFrame(self.root, width=80, corner_radius=6)
        self.sidebar_frame.pack_configure(side="left", fill="both", padx=10, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appreance Mode", anchor="w", corner_radius=0, 
                                                    fg_color="transparent", text_color="#ffffff", text_color_disabled="#ffffff")
        self.appearance_mode_label.pack_configure(padx=10, pady=10)
        self.appearance_mode_optionMenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command = change_appearanceMode, corner_radius=6)
        self.appearance_mode_optionMenu.set("Dark")
        self.appearance_mode_optionMenu.pack_configure(padx=10, pady=10)

        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling", anchor="w", corner_radius=0, 
                                                    fg_color="transparent", text_color="#ffffff", text_color_disabled="#ffffff")
        self.scaling_label.pack_configure(padx=10, pady=10)
        self.scaling_option = ctk.CTkOptionMenu(self.sidebar_frame, values=["60%", "80%", "100%", "120%", "150%"], command = change_widgetSize, corner_radius=6)
        self.scaling_option.set("100%")
        self.scaling_option.pack_configure(padx=10, pady=10)
        
        #shared file frame        
        self.shared_file_frame = ctk.CTkScrollableFrame(self.sidebar_frame, corner_radius=6, width=80)
        self.shared_file_frame.pack(padx=10, pady=10, fill="both", expand=True)

        folder_image_data = Image.open("icons/folder.png")
        folder_image = ctk.CTkImage(light_image=folder_image_data, dark_image=folder_image_data, size=(15,15))
        
        shared_file_label =  ctk.CTkButton(self.shared_file_frame, corner_radius=0, border_spacing=0, text=f"Peer {self.port}", 
                                            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                            image=folder_image, anchor="w")
        shared_file_label.pack(padx=5, pady=5, anchor="w")

        self.chat_area = ctk.CTkFrame(self.root, corner_radius=6)
        self.chat_area.pack_configure(side="right", expand=True, fill="both", padx=10, pady=10)
        
        ctk.CTkLabel(self.chat_area, text="Command:", font=ctk.CTkFont("Arial", size=14), height=12, text_color="#FFFFFF").pack(anchor="w", padx=5, pady=5)
        
        command_texts = [
            "> close: Close the program",
            "> upload: Upload file torrent",
            "> download: Download file torrent",
            "> clear: Clear command text box",
        ]
        for text in command_texts:
            ctk.CTkLabel(self.chat_area, text=text, font=ctk.CTkFont("Arial", size=12), height=12, text_color="#FFCC70").pack(anchor="w", padx=5, pady=5)

        self.text_box = ctk.CTkTextbox(self.chat_area, corner_radius=6)
        self.text_box.pack(fill="both", expand=True)   

        self.message_entry_frame = ctk.CTkFrame(self.chat_area, height=100)
        self.message_entry_frame.pack_configure(side="bottom", fill="x", padx=10, pady=10)
        self.message_entry_frame.grid_columnconfigure(0, weight=9)
        self.message_entry_frame.grid_columnconfigure(1, weight=1)
        self.message_entry_text = ctk.CTkEntry(self.message_entry_frame, placeholder_text="Type your message here...")
        self.message_entry_text.grid(row=0, column=0, stick="nsew", padx=5, pady=5)
        
        self.message_entry_text.bind("<Return>", command= lambda event: self.send_message())
        
        self.message_entry_button = ctk.CTkButton(self.message_entry_frame, text="Send Message", command= self.send_message)
        self.message_entry_button.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    def update_file_frame(self):
        file_image_data = Image.open("icons/file.png")
        file_image = ctk.CTkImage(light_image=file_image_data, dark_image=file_image_data, size=(15,15)) 

        if self.file_list:
            for files in self.file_list:

                file_button = ctk.CTkButton(self.shared_file_frame, corner_radius=0, border_spacing=0, text=files, 
                                            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                image=file_image, anchor="w")
                file_button.pack(padx=5, pady=5)    
        
    def send_message(self):
        message = self.message_entry_text.get()
        self.message_entry_text.delete(0, ctk.END)
        self.text_box.insert("end", f"{self.name}| {message}\n")
        self.command_queue.put(message)

    def process_commands(self):
        ti = "89.0.142.86"
        tp = 1000

        while True:
            message = self.command_queue.get()
            try:
                if message == "close":
                    os._exit(0)
                
                elif message == "upload":
                    dialog = ctk.CTkInputDialog(text="Enter tracker ip:", title="Get tracker ip")
                    tracker_ip = dialog.get_input()
                    dialog2 = ctk.CTkInputDialog(text="Enter tracker port:", title="Get tracker port")
                    tracker_port = dialog2.get_input()
                    tracker_port = int(tracker_port)
                    
                    if tracker_ip != ti or tracker_port != tp:
                        self.connect_to_manager(tracker_ip, tracker_port)
                        stay_conn_manager_thread = threading.Thread(target=self.periodically_announce_manager, daemon=True)
                        stay_conn_manager_thread.start()
                        accept_peers_connection_thread = threading.Thread(target=self.accept_peers_connection, daemon=True)
                        accept_peers_connection_thread.start()
                        # threading.Thread(target=self.process_commands, daemon=True).start()
                        
                        ti = tracker_ip
                        tp = tracker_port

                    dialog = ctk.CTkInputDialog(text="Enter file names:", title="Get file names")
                    file_names = dialog.get_input()
                    self.upload_file(file_names)
                    self.update_file_frame()
                
                elif message == "download":
                    dialog = ctk.CTkInputDialog(text="Enter torrent file:", title="Get torrent file")
                    torrent_file_name = dialog.get_input()
                    with open(self.torrent_dir + torrent_file_name, 'rb') as f:
                        torrent_content = pickle.load(f)
                        announce = torrent_content['announce']
                        info = torrent_content['info']
                    info_hash = hashlib.sha1(pickle.dumps(info)).hexdigest()
                    tracker_ip = announce['ip']
                    tracker_port = announce['port']
                    self.connect_to_manager(tracker_ip, tracker_port)
                    stay_conn_manager_thread = threading.Thread(target=self.periodically_announce_manager, daemon=True)
                    stay_conn_manager_thread.start()
                    accept_peers_connection_thread = threading.Thread(target=self.accept_peers_connection, daemon=True)
                    accept_peers_connection_thread.start()
                    threading.Thread(target=self.process_commands, daemon=True).start()

                    self.download_file(info_hash)
                    self.update_file_frame()

                elif message == "clear": 
                    self.text_box.delete(0.0, ctk.END)
                
                else:
                    self.text_box.insert("end", "server| Please enter correct command!\n")
            except Exception as e:
                    self.text_box.insert("end", f"server| Error: {e}\n")
     
        
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
            # print("Could not connect to ", addr)
            self.text_box.insert("end", f"server| Could not connect to {addr}\n")
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
            # print(f"peer {peer_addr} did not send the file")
            self.text_box.insert("end", f"server| peer {peer_addr} did not send the file\n")
        except pickle.UnpicklingError:
            # print(f"failed to receive the chunk {chunk_no + 1}/{incomp_file.n_chunks} from {peer_addr}")
            self.text_box.insert("end", f"server| failed to receive the chunk {chunk_no + 1}/{incomp_file.n_chunks} from {peer_addr}\n")
        except Exception as e:
            # print("Error", e)
            self.text_box.insert("end", f"server| {e}\n")
        else:
            # print(f"received the chunk {chunk_no + 1}/{incomp_file.n_chunks} of file {filename} from {peer_addr}")
            self.text_box.insert("end", f"server| received the chunk {chunk_no + 1}/{incomp_file.n_chunks} of file {filename} from {peer_addr}\n")
            self.text_box.see("end")
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
                # print("Exception 2", e)
                self.text_box.insert(f"server| Exception 2 {e}\n")
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
                # print("Exception 1", e)
                self.text_box.insert(f"server| Exception 1 {e}\n")
                break
    
    def upload_file(self, filenames):
        # print("Uploading file")
        self.text_box.insert("end", "server| Uploading file\n")
        file_names = filenames.split(',')
        file_dirs = []
        for file_name in file_names:
            file_dir = self.directory + file_name
            file_dirs.append(file_dir)
            if not os.path.isfile(file_dir):
                # print(f"File {file_name} does not exist")
                self.text_box.insert("end", f"server| File {file_name} does not exist\n")
                file_dirs.remove(file_dir)
                file_names.remove(file_name)

        torrent_file = torrent(file_dirs, PIECE_LENGTH, self.manager_addr[0], self.manager_addr[1])
        info_hash = torrent_file.get_info_hash()
        torrent_file.write_torrent(self.torrent_dir)
        message = pickle.dumps({
            'type': 'upload',
            'info_hash': info_hash,
            'addr': (self.ip, self.port),
            'torrent': torrent_file,
        })
        for file_name in file_names:
            self.file_list.append(file_name)
        # print(len(message))
        self.manager_conn_socket.sendall(message)
        return info_hash
    
    def download_file(self, info_hash):
        self.manager_conn_socket.sendall(pickle.dumps({'type': 'get peers', 'info_hash': info_hash}))
        message = pickle.loads(self.manager_conn_socket.recv(8192))
        if message['type'] == 'not available':
            # print("File is not available")
            self.text_box.insert("end", "server| File is not available\n")
            return
        torrent_file = message['torrent']
        # torrent_file.write_torrent(self.torrent_dir)
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
                # print("File is not available")
                self.text_box.insert("end", "server| File is not available\n")
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
        # print(f"Time taken to download {torrent_file.info['name']} is {end - start} seconds")
        self.text_box.insert("end", f"server| Time taken to download {torrent_file.info['name']} is {end - start} seconds\n")
        for receiving_file in receiving_files:
            receiving_file.write_file()
            self.file_list.append(receiving_file.filename)
        # print(f"File {torrent_file.info['name']} downloaded")
        self.text_box.insert("end", f"server| File {torrent_file.info['name']} downloaded\n")
        self.text_box.see("end")
        self.manager_conn_socket.sendall(pickle.dumps({'type': 'downloaded', 'info_hash': info_hash, 'addr': (self.ip, self.port)}))

    def run(self):
        # print("Running")
        self.text_box.insert("end", f"Peer {self.port}: Running\n")

        threading.Thread(target=self.process_commands, daemon=True).start()
        self.root.mainloop()
        
def main():
    # port = int(input("Enter port: "))
    # name = input("Enter name: ")
    myApp = login()
    port = int(myApp.port_no)
    name = str(myApp.folder_name)
    peer = Peer(port, name)
    peer.run()

if __name__ == "__main__":
    main()