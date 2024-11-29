from torrent import torrent
import numpy as np

class swarm:
    def __init__(self, torrent_file: torrent):
        self.peers = dict()
        self.torrent_file = torrent_file
        self.total_pieces = len(torrent_file.info['pieces'])
        self.complete_peers = set()
        self.rarest_piecces = np.zeros(self.total_pieces)
    def get_rarest_chunks(self, available_peer_num, received_chunks):
        self.rarest_pieces = np.zeros(self.total_pieces)
        for pieces in self.peers.values():
            self.rarest_pieces += pieces
        for i in range(len(self.rarest_pieces)):
            if received_chunks[i]:
                self.rarest_pieces[i] = np.inf
        
        # indices = np.argsort(self.rarest_pieces)
        indices = sorted(range(len(self.rarest_pieces)), key=lambda k: (self.rarest_pieces[k], k))
        j = 0
        while j < available_peer_num and not received_chunks[indices[j]]:
            j += 1

        return list(indices[:j])
    def update(self, peer, index):
        self.peers[peer][index] = 1
    def add_peer(self, peer, has_file: bool):
        if peer in self.peers.keys():
            return
        if has_file:
            self.peers[peer] = np.ones(self.total_pieces)
            self.complete_peers.add(peer)
        else:
            self.peers[peer] = np.zeros(self.total_pieces)
    def remove_peer(self, peer):
        self.peers.pop(peer)
        self.complete_peers.discard(peer)
