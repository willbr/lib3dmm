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
        output.append("{:08X} | {:47} | {}".format(line + line_offset,
            hex_data, str_data))
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
        print("{:8X} | {:3} | {:47}".format(i + line_offset,
            i + line_offset, hex_data))

def read_struct(fmt, file, byte_order='<'):
    size = struct.calcsize(fmt)
    # all 3dmm files use little endian
    data_tuple = struct.unpack(byte_order + fmt, file.read(size))
    return data_tuple[0] if len(data_tuple) == 1 else data_tuple


class Quad:
    def __init__(self, file, length):
        self.load(file, length)

    def load(self, file, length):
        read = functools.partial(read_struct, file=file)
        self.type = read('4s')[::-1]
        self.id = read('L')
        self.section_offset = read('L')
        self.mode = read('B')

        self.section_length = struct.unpack('<L',
                file.read(3) + b'\0')[0]

        self.references=[]
        self.reference_count = read('H')
        self.references_to_this_quad = read('H')

        length_of_references = 12 * self.reference_count


        # parse references
        for i in range(self.reference_count):
            reference = {
                    'type': read('4s')[::-1],
                    'id': read('L'),
                    'reference_id': read('L')
                    }
            self.references.append(reference)

        quad_header_length = 20
        if length_of_references + quad_header_length != length:
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
        return '<Quad {} {} {} offset={:04X} lenth={}>'.format(
                self.type, self.id,
                self.string, self.section_offset, self.section_length)


class Movie:
    def __init__(self, name):
        self.movie_file_name = name
        self.movie_file = open(name, 'rb')
        read = functools.partial(read_struct, file=self.movie_file)

        self.id = read('8s')
        self.version = read('2H')
        self.marker = read('4B')
        self.file_length = read('L')
        self.index_offset = read('L')
        self.index_length = read('L')
        self.dummy = read('L')

        self.movie_file.seek(self.index_offset)
        
        self.quad_marker = read('4B')
        self.quad_count = read('L')
        self.quad_length = read('L')
        self.quad_unk = read('ll')

        self.quad_start = self.movie_file.tell()

        # load quad index
        self.movie_file.seek(self.quad_start+self.quad_length)
        self.quad_indexes = []
        for i in range(self.quad_count):
            self.quad_indexes.append(read('2L'))

        # load quads
        self.quads = []
        for offset, length in self.quad_indexes:
            self.movie_file.seek(self.quad_start + offset)
            self.quads.append(Quad(self.movie_file, length))

        self.movie_file.close()
        return


    def print_tree(self):
        for indent, quad in self.walk(0, self.get_root_quad()):
            print("{}{}".format(indent * '    ', quad))

    def get_tree(self):
        for indent, quad in self.walk(0, self.get_root_quad()):
            yield (indent, quad)

    def walk(self, level, quad):
        if quad:
            yield level, quad
            for ref in quad.references:
                for l, q in self.walk(level + 1, self.get_quad(ref)):
                    yield l, q

    def get_quad(self, ref):
        ref_type = ref['type']
        ref_id = ref['id']
        for quad in self.quads:
            if quad.type == ref_type and quad.id == ref_id:
                return quad

    def get_root_quad(self):
        root = None
        for quad in self.quads:
            if quad.mode == 2:
                root = quad
        return root



if __name__ == '__main__':
    pass
