import math

class piece_mapping:
    def __init__(self, file_infos, piece_length):
        self.file_infos = file_infos
        self.piece_length = piece_length
        for file_info in self.file_infos:
            file_info['piece_cnt'] = math.ceil(file_info['size'] / self.piece_length)
    def get_file_chunk_no(self, world_chunk_no):
        file_chunk_no = world_chunk_no
        index = 0
        while file_chunk_no >= self.file_infos[index]['piece_cnt']:
            file_chunk_no -= self.file_infos[index]['piece_cnt']
            index += 1
        return index, file_chunk_no