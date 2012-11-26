from tkinter import *
from tkinter.scrolledtext import ScrolledText
import lib3dmm
import os
import io
import functools
import struct
import time
from os import system

def clear():
    enable()
    t.delete('1.0', 'end')
    disable()

def enable():
    t['state'] = 'normal'

def disable():
    t['state'] = 'disabled'

def double_button_1(e):
    if selection_offset != None:
        pass

def button_1(e):
    global selection_offset
    global selection_value
    global selection_start
    global selection_end

    root.focus()

    # reset last selection
    try:
        selection_value = current_data[selection_offset]
        update_selection_value()
    except:
        pass

    c = '@{},{}'.format(e.x, e.y)
    index = t.index(c)
    y, x = [int(i) for i in index.split('.')]

    # skip offset
    x -= 10
    long_offset = x // 12
    hit = x % 12 != 0

    start_x = 11 + (12 * long_offset)
    start = '{}.{}'.format(y, start_x)
    end = '{}.{}'.format(y, start_x + 11)
    selection_start = start
    selection_end = end

    selection = t.get(start, end)


    # reset to default
    t.tag_remove('selection', '1.0', 'end')
    selection_offset = None

    if 0 <= long_offset <= 3 and hit:
        # store offset
        line = t.get('%s linestart' % c, '%s lineend' % c)
        line_offset = int(line[:8], 16) if line != '' else None
        offset = line_offset + (4 * long_offset)

        if selection.strip() != '':
            #t.tag_add('selection', start, end)
            selection_offset = offset
            selection_value = current_data[offset]
            update_selection_value()
    return "break"

def update_selection_value():
    if selection_offset == None:
        return

    enable()
    hex_data = ' '.join(i == 0 and ".." or "{:02X}".format(i) for i in
            selection_value)
    t.replace(selection_start, selection_end, hex_data, 'selection')
    signed_long.set(struct.unpack('<l', selection_value)[0])
    unsigned_long.set(struct.unpack('<L', selection_value)[0])
    hexed_long.set('0X' + ''.join('{:02X}'.format(i) for i in
        selection_value[::-1]))
    disable()

def dump_quad():
    m = lib3dmm.Movie(movie_file_name)
    section_dumps = []
    for quad in m.quads:
        if quad.type == b'THUM':
            continue

        section_dumps.append(quad.type)
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
            for o,l in index:
                data_file.seek(o + 20)
                d = data_file.read(l)
                section_dumps.append(lib3dmm.hex_dump(d,
                    quad.section_offset + o + 20))
        else:
            data_file = io.BytesIO(quad.data)
            d = data_file.read(quad.section_length)
            section_dumps.append(lib3dmm.hex_dump(d,
                quad.section_offset))

    return section_dumps

def update_display(new_dump):
    global current_data
    if new_dump == None:
        clear()
        return
    clear()
    enable()
    new_data = {}
    for section in new_dump:
        if type(section) == bytes:
            t.insert('end-1c', section.decode('ascii') + '\n\n')
            continue
        for offset, data, characters in section:
            t.insert('end-1c', '{:8X} | '.format(offset))
            for i in range(0, 16, 4):
                d = data[i:i+4]
                key = offset + i

                if len(d) != 0:
                    new_data[key] = d

                try:
                    old_d = current_data[key]
                except:
                    old_d = None

                hex_data = ' '.join(i == 0 and ".." or "{:02X}".format(i) for i in d)

                if d == old_d or old_d == None:
                    t.insert('end-1c', hex_data)
                else:
                    t.insert('end-1c', hex_data, 'diff')

                if len(d) == 0:
                    t.insert('end-1c', ' ' * 11)
                t.insert('end-1c', ' ')
                #t.insert('end-1c', ' ')
            t.insert('end-1c', '| ')
            t.insert('end-1c', characters)
            t.insert('end-1c', '\n')
        t.insert('end-1c', '\n')
    disable()
    current_data = new_data

def check_if_modified():
    global last_time_modified
    try:
        time_modified = os.stat(movie_file_name).st_mtime
        if time_modified != last_time_modified:
            current_dump = dump_quad()
            update_display(current_dump)
            last_time_modified = time_modified
    except FileNotFoundError:
        # 3DMM uses a temp file while saving
        pass

    root.after(1000, check_if_modified)

def update_file(e):
    if selection_offset == None:
        return
    print('update file')
    # run none
    system('start none.3mm')
    time.sleep(0.1)
    # make change
    try:
        f = open(movie_file_name,"rb+")
        f.seek(selection_offset)
        f.write(selection_value)
        f.close()
    except:
        print('file write failed')
    # run test movie
    system('start test_movie.3mm')
    time.sleep(0.2)
    root.focus_force()

def change_value_reset():
    global selection_value
    if selection_offset == None:
        return
    selection_value = current_data[selection_offset]
    update_selection_value()

def change_value_to_zero():
    global selection_value
    if selection_offset == None:
        return
    selection_value = struct.pack('<L', 0)
    update_selection_value()

def change_value(direction):
    global selection_value
    if selection_offset == None:
        return
    if direction == 'up':
        s = step.get() 
    else:
        s = step.get()  * -1

    try:
        ul = struct.unpack('<L', selection_value)[0]
        ul += s
        selection_value = struct.pack('<L', ul)
    except struct.error:
        sl = struct.unpack('<l', selection_value)[0]
        sl += s
        selection_value = struct.pack('<l', sl)

    update_selection_value()
    
root = Tk()

root.title('3mm monitoring tool')

movie_file_name = 'test_movie.3mm'
last_time_modified = None
current_data = None
selection_offset = None


t = ScrolledText(font='TkFixedFont', width=80, height=40,
        state='disabled', wrap='none',
        padx=5, pady=5)

t.tag_config('diff', background='yellow')
t.tag_config('selection', background='grey')


t.bind('<Double-Button-1>', double_button_1)
t.bind('<Button-1>', button_1)
root.bind('<Escape>', lambda e: root.focus())
root.bind('<Return>', update_file)

root.bind('j', lambda e: change_value('down'))
root.bind('k', lambda e: change_value('up'))
root.bind('x', lambda e: change_value_to_zero())
root.bind('u', lambda e: change_value_reset())

#root.bind('<KeyPres-a>', lambda e: print('key'))
#root.bind('<KeyRelease-a>', lambda e: print('key'))

bottom_section = Frame()

signed_long = IntVar()
unsigned_long = IntVar()
step = IntVar(value=1000)
hexed_long = IntVar()

entry_signed_long = Entry(bottom_section, textvariable=signed_long)
entry_unsigned_long = Entry(bottom_section, textvariable=unsigned_long)
entry_hexed_long = Entry(bottom_section, textvariable=hexed_long)
entry_step = Entry(bottom_section, textvariable=step)

t.pack(fill=BOTH, expand = YES)
bottom_section.pack(side=BOTTOM)

entry_signed_long.pack()
entry_unsigned_long.pack()
entry_hexed_long.pack()
entry_step.pack(side=RIGHT)


check_if_modified()

root.mainloop()

