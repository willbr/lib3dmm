import lib3dmm
import sys
import os
import time
import difflib
import functools
import io
import struct
import colorama
from colorama import Fore, Back, Style

def log(n):
    h = ''.join(i == 0 and ".." or "{:02X}".format(i) for i in struct.pack('<L', n))
    print("{:8X} : {} : {:8}".format(n, h, n))

def print_tree():
    global movie_file_name
    m = lib3dmm.Movie(movie_file_name)
    m.print_tree()

last_dump = None


def compare(a_text, b_text):
    if a_text == None:
        print(b_text)
        return
    prefix = Back.GREEN + Fore.WHITE
    postfix = Style.RESET_ALL
    a_lines = a_text.split('\n')
    b_lines = b_text.split('\n')
    for y in range(len(b_lines)):
        output = []
        for x in range(len(b_lines[y])):
            try:
                char_a = a_lines[y][x]
                char_b = b_lines[y][x]
                if char_a == char_b:
                    char = char_b
                else:
                    char = prefix + char_b + postfix
            except IndexError:
                char_b = b_lines[y][x]
                char = prefix + char_b + postfix
            output.append(char)
        print(''.join(output))


def dump_ggae():
    global last_dump
    global movie_file_name
    print('=' * 60)
    m = lib3dmm.Movie(movie_file_name)
    for quad in m.quads:
        if quad.type == b'GGAE':
            data_file = io.BytesIO(quad.data)
            read = functools.partial(lib3dmm.read_struct, file=data_file)
            magic = read('L')
            count = read('L')
            offset = read('L')

            # read index
            data_file.seek(offset + 20)
            index = []
            for i in range(count):
                o = read('L')
                l = read('L')
                index.append((o, l))

            # seek to data and read
            section_dumps = []
            for o,l in index:
                # print("{}, {}".format(o, l))
                data_file.seek(o + 20)
                d = data_file.read(l)
                section_dumps.append(lib3dmm.hex_dump_string(d,
                    quad.section_offset + o + 20))

            dump = '\n\n'.join(section_dumps)
            compare(last_dump, dump)
            last_dump = dump

            #lib3dmm.hex_dump_compare(last_dump, quad.data, quad.section_offset)
            # last_dump = quad.data
            return


commands = {
        'tree': print_tree,
        'dump-ggae': dump_ggae
        }

if __name__ == '__main__':
    colorama.init()
    movie_file_name = sys.argv[1]
    command_name = sys.argv[2]
    command = commands[command_name]

    old_mtime = os.stat(movie_file_name).st_mtime
    command()
    print()

    while 1:
        time.sleep(1)
        new_mtime = os.stat(movie_file_name).st_mtime
        if new_mtime != old_mtime:
            old_mtime = new_mtime
            command()
            print()

