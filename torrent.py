import hashlib
import pickle
import math
import os

class torrent:
    def __init__(self, file_path, piece_length, tracker_ip='127.0.0.1', tracker_port=2000):
        self.tracker_ip  = tracker_ip
        self.tracker_port = tracker_port
        self.piece_length = piece_length
        self.announce = {
            'ip': self.tracker_ip,
            'port': self.tracker_port,
        }
        self.info = {
            'name': file_path.split('/')[-1],
            'size': os.path.getsize(file_path),
            'piece_length': self.piece_length,
            'pieces': [],
        }
        with open(file_path, 'rb') as f:
            for _ in range(math.ceil(self.info['size']/self.info['piece_length'])):
                self.info['pieces'].append(hashlib.sha1(f.read(self.info['piece_length'])).hexdigest())
    
    def get_info_hash(self):
        return hashlib.sha1(pickle.dumps(self.info)).hexdigest()
    
    def write_torrent(self, torrent_dir):
        assert os.path.isdir(torrent_dir)      
        path = torrent_dir + self.info['name'].split('.')[0] + '.torrent'    
        if os.path.isfile(path):
            os.remove(path)        
        with open(path, 'wb') as f:
            content = {
                'announce': self.announce,
                'info': self.info,
            }
            f.write(pickle.dumps(content))