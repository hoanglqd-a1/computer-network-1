import hashlib
import pickle
import math
import os

class torrent:
    def __init__(self, file_paths: list, piece_length, tracker_ip='127.0.0.1', tracker_port=2000):
        self.tracker_ip  = tracker_ip
        self.tracker_port = tracker_port
        self.piece_length = piece_length
        self.announce = {
            'ip': self.tracker_ip,
            'port': self.tracker_port,
        }
        name = ""
        size = 0
        for file_path in file_paths:
            name += file_path.split('/')[-1] + ' '
            size += os.path.getsize(file_path)
        
        self.info = {
            'name': name[:-1],
            'size': size,
            'piece_length': self.piece_length,
            'pieces': [],
            'files': [
                {
                    'name': file_path.split('/')[-1],
                    'size': os.path.getsize(file_path)
                } for file_path in file_paths
            ]
        }
        for i in range(len(file_paths)):
            with open(file_paths[i], 'rb') as f:
                for _ in range(math.ceil(self.info['files'][i]['size']/self.info['piece_length'])):
                    self.info['pieces'].append(hashlib.sha1(f.read(self.info['piece_length'])).hexdigest())
    
    def get_info_hash(self):
        return hashlib.sha1(pickle.dumps(self.info)).hexdigest()
    
    def write_torrent(self, torrent_dir):
        assert os.path.isdir(torrent_dir)
        path_name = ""
        for file in self.info['files']:
            path_name += file['name'].split('.')[0]
        path = torrent_dir + path_name + '.torrent'    
        if os.path.isfile(path):
            os.remove(path)        
        with open(path, 'wb') as f:
            content = {
                'announce': self.announce,
                'info': self.info,
            }
            pickle.dump(content, f)