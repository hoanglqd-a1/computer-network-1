import math
import os

PIECE_LENGTH = 256 * 1024

class file:
    chunk_size = PIECE_LENGTH

    def __init__(self, filename: str, owner: str):
        self.filename = filename
        self.path = "./Peers/" + owner + "/" + filename

class completeFile(file):

    def __init__(self, filename: str, owner: str):
        super().__init__(filename, owner)
        self.size = self.get_size(self.path)
        self.n_chunks = math.ceil(self.size / self.chunk_size)
        self.fp = open(self.path, 'rb')

    def get_chunk_no(self, chunk_no):
        
        return self._get_chunk(chunk_no * self.chunk_size)

    def _get_chunk(self, offset):
        self.fp.seek(offset, 0)
        chunk = self.fp.read(self.chunk_size)
        return chunk

    @staticmethod
    def get_size(path):
        return os.path.getsize(path)


class incompleteFile(file):
    def __init__(self, filename, owner, size):
        super().__init__(filename, owner)
        self.size = size
        self.n_chunks = math.ceil(self.size / self.chunk_size)
        self.needed_chunks = [i for i in range(self.n_chunks)]
        self.received_chunks = {}
        self.fp = open(self.path, 'wb')

    def get_needed(self):
        self.needed_chunks = []
        for i in range(self.n_chunks):
            if i not in self.received_chunks:
                self.needed_chunks.append(i)
        return self.needed_chunks

    def write_chunk(self, buf, chunk_no):
        self.received_chunks[chunk_no] = buf

    def write_file(self):
        if len(self.get_needed()) == 0:
            with open(self.path, 'wb') as filep:
                for i in range(self.n_chunks):
                    filep.write(self.received_chunks[i])