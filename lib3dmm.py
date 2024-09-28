import struct
import functools
from colorama import Fore, Back, Style

def hex_dump(data, line_offset=0):
    output = []
    for line in range(0, len(data), 16):
        d = data[line: line + 16]
        str_data = ''.join(31 < i < 127 and chr(i) or '.' for i in d)
        output.append((line + line_offset, d, str_data))
    return output

def hex_dump_string(data, line_offset=0):
    output = []
    for line in range(0, len(data), 16):
        d = data[line: line + 16]
        hex_data = ' '.join(i == 0 and ".." or "{:02X}".format(i) for i in d)
        str_data = ''.join(31 < i < 127 and chr(i) or ' ' for i in d)
        output.append("{:08X} | {:47} | {}".format(line + line_offset, hex_data, str_data))
    return '\n'.join(output)

def hex_dump_compare(a_data, b_data, line_offset=0):
    prefix = Back.GREEN + Fore.WHITE
    postfix = Style.RESET_ALL
    a_data = a_data or b_data
    for i in range(0, len(b_data), 16):
        a_line = a_data[i: i + 16]
        b_line = b_data[i: i + 16]
        output = []
        for j in range(0, len(b_line)):
            try:
                a = a_line[j]
                b = b_line[j]
                char = (b == 0) and '..' or "{:02X}".format(b)
                if a != b:
                    char = prefix + char + postfix
                output.append(char)
            except IndexError:
                b = b_line[j]
                char = (b == 0) and '..' or "{:02X}".format(b)
                char = prefix + char + postfix
                output.append(char)
        hex_data = ' '.join(output)
        print("{:8X} | {:3} | {:47}".format(i + line_offset, i + line_offset, hex_data))

def read_struct(fmt, file, byte_order='<'):
    size = struct.calcsize(fmt)
    data_tuple = struct.unpack(byte_order + fmt, file.read(size))
    return data_tuple[0] if len(data_tuple) == 1 else data_tuple

class Chunk:
    def __init__(self, file, length):
        self.load(file, length)

    def load(self, file, length):
        read = functools.partial(read_struct, file=file)
        self.type = read('4s')[::-1]
        self.id = read('L')
        self.section_offset = read('L')
        self.mode = read('B')
        self.section_length = struct.unpack('<L', file.read(3) + b'\0')[0]

        self.references = []
        self.reference_count = read('H')
        self.references_to_this_chunk = read('H')

        length_of_references = 12 * self.reference_count

        # parse references
        for i in range(self.reference_count):
            reference = {
                'type': read('4s')[::-1],
                'id': read('L'),
                'reference_id': read('L')
            }
            self.references.append(reference)

        chunk_header_length = 20
        if length_of_references + chunk_header_length != length:
            # We have a string
            marker = read('2B')
            string_length = read('B')
            if marker == (3, 3):
                # ASCII
                self.string = read('{}s'.format(string_length))
            elif marker == (5, 5):
                # Unicode
                characters = []
                for i in range(string_length):
                    character = read('H', '!')
                    characters.append(character)
                self.string = u''.join(characters)
            else:
                # Unknown marker
                raise TypeError
        else:
            self.string = None

        # read data
        file.seek(self.section_offset)
        self.data = file.read(self.section_length)

    def __str__(self):
        return '<Chunk {} {} {} offset={:04X} length={}>'.format(
            self.type, self.id, self.string, self.section_offset, self.section_length)

class ChunkFile:
    def __init__(self, name):
        self.chunk_file_name = name
        self.chunk_file = open(name, 'rb')
        read = functools.partial(read_struct, file=self.chunk_file)

        self.id = read('8s')
        self.version = read('2H')
        self.marker = read('4B')
        self.file_length = read('L')
        self.index_offset = read('L')
        self.index_length = read('L')
        self.dummy = read('L')

        self.chunk_file.seek(self.index_offset)
        
        self.chunk_marker = read('4B')
        self.chunk_count = read('L')
        self.chunk_length = read('L')
        self.chunk_unk = read('ll')

        self.chunk_start = self.chunk_file.tell()

        # load chunk index
        self.chunk_file.seek(self.chunk_start + self.chunk_length)
        self.chunk_indexes = []
        for i in range(self.chunk_count):
            self.chunk_indexes.append(read('2L'))

        # load chunks
        self.chunks = []
        for offset, length in self.chunk_indexes:
            self.chunk_file.seek(self.chunk_start + offset)
            self.chunks.append(Chunk(self.chunk_file, length))

        self.chunk_file.close()
        return

    def print_tree(self):
        for indent, chunk in self.walk(0, self.get_root_chunk()):
            print("{}{}".format(indent * '    ', chunk))

    def get_tree(self):
        for indent, chunk in self.walk(0, self.get_root_chunk()):
            yield (indent, chunk)

    def walk(self, level, chunk):
        if chunk:
            yield level, chunk
            for ref in chunk.references:
                for l, q in self.walk(level + 1, self.get_chunk(ref)):
                    yield l, q

    def get_chunk(self, ref):
        ref_type = ref['type']
        ref_id = ref['id']
        for chunk in self.chunks:
            if chunk.type == ref_type and chunk.id == ref_id:
                return chunk

    def get_root_chunk(self):
        root = None
        for chunk in self.chunks:
            if chunk.mode == 2:
                root = chunk
        return root

if __name__ == '__main__':
    pass
