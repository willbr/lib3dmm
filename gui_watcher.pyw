from tkinter import *
from tkinter.scrolledtext import ScrolledText
import lib3dmm
import os
import io
import functools
import struct
import time
import pprint
from collections import namedtuple, OrderedDict
from os import system
import math

Vec3 = namedtuple('Vec3', ['x', 'y', 'z'])

pformat = pprint.PrettyPrinter(indent=4).pformat

ggae_sections = {
        0: 'init',
        1: 'action',
        2: 'outfit',
        3: 'rotation-reset',
        4: 'squish',
        5: 'size',
        6: 'sound',
        7: 'move',
        8: 'action-marker',
        9: 'single-frame-move',
        10: 'unknown-10',
        11: 'cut',
        12: 'rotation',
        }
#add reverse lookup
ggae_sections.update({(v,k) for k,v in ggae_sections.items()})

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
        try:
            line_offset = int(line[:8], 16)
        except ValueError:
            return "break"

        offset = line_offset + (4 * long_offset)

        if selection.strip() != '':
            #t.tag_add('selection', start, end)
            selection_offset = offset
            selection_value = current_data[offset]
            update_selection_value()
    t.focus()
    return "break"

def update_selection_value():
    if selection_offset == None:
        return

    enable()
    hex_data = ' '.join(i == 0 and ".." or "{:02X}".format(i) for i in
            selection_value)
    t.replace(selection_start, selection_end, hex_data, 'selection')
    unsigned_short.set(struct.unpack('<hh', selection_value)[0])
    #print(struct.unpack('<hh', selection_value))
    signed_long.set(struct.unpack('<l', selection_value)[0])
    unsigned_long.set(struct.unpack('<L', selection_value)[0])
    double.set(struct.unpack('<f', selection_value)[0])
    hexed_long.set('0X' + ''.join('{:02X}'.format(i) for i in
        selection_value[::-1]))
    disable()

def dump_quad():
    m = lib3dmm.Movie(movie_file_name)
    section_dumps = []
    ignore_list = [s.upper() for s in ignore_list_string.get().split()]
    for quad in m.quads:
        if quad.type.decode('ascii').strip() in ignore_list:
            continue

        dump_section = True
        print_header = False
        header_length = 20
        quad_dumps = []

        data_file = io.BytesIO(quad.data)
        #read = functools.partial(lib3dmm.read_struct, file=data_file)
        def read(fmt):
            r = functools.partial(lib3dmm.read_struct, file=data_file)
            if fmt == "scalar":
                return r('l') / 65536
            elif fmt == "angle":
                return (r('h') / 65536) * 360
            elif fmt == "vec3":
                return Vec3(read('scalar'), read('scalar'), read('scalar'))
            elif fmt == 'matrix34':
                return [
                        [read('scalar'), read('scalar'), read('scalar'), 0.0],
                        [read('scalar'), read('scalar'), read('scalar'), 0.0],
                        [read('scalar'), read('scalar'), read('scalar'), 0.0],
                        [read('scalar'), read('scalar'), read('scalar'), 1.0]
                        ]
            elif fmt == "section-header":
                return OrderedDict([
                        ('L frame', read('L')),
                        ('L b unknown', read('L')),
                        ('L c unknown', read('L')),
                        ('L frame creation offset', read('L'))])
            else:
                return r(fmt)

        if quad.type == b'GST ':
            magic = read('L')
            gst_type = read('L')
            count = read('L')
            offset = read('L')
            data_file.seek(offset + header_length)

            if gst_type == 0x20:
                actors = []
                for i in range(count):
                    actor = {}
                    actor['name_offset'] = read('L')
                    actor['id'] = read('L')
                    actor['unknown_c'] = read('L')
                    actor['actor_or_prop'] = read('L')
                    actor['unknown_e'] = read('L')
                    actor['unknown_f'] = read('L')
                    actor['label'] = read('4s')[::-1]
                    actor['actor_id'] = read('L')
                    actors.append(actor)

                length = 4 * 8
                for i in range(count):
                    o = offset + header_length + i * length
                    data_file.seek(o)
                    d = data_file.read(length)
                    quad_dumps.append(lib3dmm.hex_dump(d,
                        quad.section_offset + o))

                for i in range(len(actors)):
                    actor = actors[i]
                    data_file.seek(header_length + actor['name_offset'])
                    length = read('B')
                    actor['name'] = read('%ds' % length)

                print(pformat (actors))

            elif gst_type == 0x08:
                data_file.seek(header_length)
                d = data_file.read(quad.section_length -
                        (quad.section_length -offset))
                quad_dumps.append(lib3dmm.hex_dump(d,
                    quad.section_offset + header_length))

                data_file.seek(header_length + offset)
                d = data_file.read(quad.section_length)
                quad_dumps.append(lib3dmm.hex_dump(d,
                    quad.section_offset + header_length + offset))

                data_file.seek(header_length + offset)
                index = []
                for i in range(count):
                    offset = read('L')
                    id = read('L')
                    index.append((offset, id))

                strings = []
                for o, id in index:
                    o += header_length
                    data_file.seek(o)
                    length = read('B')
                    name = read('%ds' % length)
                    strings.append((id, name))
                strings.sort()
                print(pformat(strings))
            else:
                print ('unknown gst_type: {}'.format(gst_type))

        elif quad.type == b'GGAE':
            dump_section = False
            header = OrderedDict()
            header['magic'] = read('L')
            header['count'] = read('L')
            header['offset'] = read('L')
            header['unknown d'] = read('L')
            header['unknown e'] = read('L')

            # read index
            data_file.seek(header['offset'] + header_length)
            index = []
            for i in range(header['count']):
                o = read('L')
                l = read('L')
                index.append((o, l))
            header['index'] = index

            if dump_section:
                quad_dumps.append(pformat(header))
                quad_dumps.append('\n\n')

            # seek to data and read
            for o,l in index:
                section = OrderedDict()
                # section header
                data_file.seek(o + header_length)
                id = read('L')
                section['id'] = ggae_sections.get(id, 'unknown')
                if section["id"].upper() not in ignore_list:
                    quad_dumps.append(section['id'])
                section['header'] = read('section-header')
                #section['L frame'] = read('L')
                #section['L unknown c'] = read('L')
                #section['L unknown d'] = read('L')
                #section['L frame creation offset'] = read('L')


                # section body
                if id == ggae_sections['init']:
                    section['lll offset vector'] = read('vec3')
                    section['h rotation pitch'] = read('angle')
                    section['h rotation yaw'] = read('angle')
                    section['h rotation roll'] = read('angle')
                    section['h unknown'] = read('angle')
                    #print(pformat(section))
                elif id == ggae_sections['action']:
                    section['action id'] = read('L')
                    section['action frame'] = read('L')
                elif id == ggae_sections['action-marker']:
                    section['stop'] = read('L') != 0
                elif id == ggae_sections['outfit']:
                    section['part'] = read('L')
                    section['outfit'] = read('L')
                    section['unknown h'] = read('L')
                    section['unknown i'] = read('L')
                    section['unknown j'] = read('L')
                    section['label'] = read('4s')[::-1]
                    section['mtrl id'] = read('L')
                    #print(pformat(section))
                elif id == ggae_sections['squish']:
                    section['scale'] = read('vec3')
                    #print(pformat(section))
                elif id == ggae_sections['size']:
                    section['size'] = read('scalar')
                    #print(pformat(section))
                elif id == ggae_sections['sound']:
                    section['loop'] = read('L')
                    section['unknown g'] = read('L')
                    section['volume'] = read('L')
                    section['unknown i'] = read('L')
                    section['channel'] = read('L')
                    section['stopper'] = read('L')
                    section['unknown l'] = read('L')
                    section['unknown m'] = read('L')
                    section['data set'] = read('L')
                    section['label'] = read('4s')[::-1]
                    section['sound id'] = read('L')
                    #print(pformat(section))
                elif id == ggae_sections['move']:
                    section['offset vector'] = read('vec3')
                    #print(pformat(section))
                elif id == ggae_sections['single-frame-move']:
                    section['offset vector'] = read('vec3')
                    #print(pformat(section))
                elif id == ggae_sections['rotation-reset']:
                    section['rotation matrix'] = read('matrix34')
                elif id == ggae_sections['rotation']:
                    section['rotation matrix'] = read('matrix34')
                elif id == ggae_sections['cut']:
                    pass
                else:
                    print('unkown id: %d' % id)

                if section["id"].upper() not in ignore_list:
                    data_file.seek(o + header_length)
                    d = data_file.read(l)
                    quad_dumps.append(lib3dmm.hex_dump(d,
                        quad.section_offset + o + header_length))
                    quad_dumps.append(pformat(section))
                    quad_dumps.append("\n\n")

        elif quad.type == b'ACTR':
            actor = {}

            magic = read('L')

            actor['pos_x'] = read('L')
            actor['pos_y'] = read('L')
            actor['pos_z'] = read('L')
            actor['instance'] = read('L')

            actor['frame a'] = read('L')
            actor['frame b'] = read('L')
            actor['unknown_g'] = read('L')
            actor['unknown_h'] = read('L')

            actor['unknown_i'] = read('4s')[::-1]
            actor['actor id'] = read('L')

            print(pformat (actor))
        elif quad.type == b'PATH':
            print_header = False
            path = {}

            magic = read('L')
            path['unknown id'] = read('L')
            count = read('L')
            steps = []
            for i in range(count):
                step = {}
                step['pos x?'] = read('L')
                step['pos y?'] = read('L')
                step['pos z?'] = read('L')
                step['unknown rot?'] = read('L')
                steps.append(step)
            path['steps'] = steps
            print(pformat (path))
        elif quad.type == b'GGFR':
            dump_section = False
            magic = read('L')
            count = read('L')
            offset = read('L')
            data_file.seek(header_length + offset)

            # read index
            data_file.seek(offset + header_length)
            index = []
            for i in range(count):
                o = read('L')
                l = read('L')
                index.append((o, l))

            # seek to data and read
            for o,l in index:
                data_file.seek(o + header_length)
                frame = read('L')
                id = read('L')
                if id == 1:
                    sound = {}
                    sound['frame'] = frame
                    sound['section id'] = id
                    sound['volume'] = read('L')
                    sound['unknown d'] = read('L')
                    sound['looping'] = read('L')
                    sound['unknown f'] = read('L')
                    sound['unknown g'] = read('L')
                    sound['unknown h'] = read('L')
                    sound['unknown i'] = read('L')
                    sound['unknown j'] = read('4s')[::-1]
                    sound['sound id'] = read('L')
                    quad_dumps.append('sound')
                    print(pformat(sound))
                elif id == 3:
                    camera_angle = {}
                    camera_angle['frame'] = frame
                    camera_angle['section id'] = id
                    camera_angle['camera angle id'] = read('L')
                    quad_dumps.append('camera angle')
                    print(pformat(camera_angle))
                else:
                    quad_dumps.append('unknown GGFR section')



                data_file.seek(o + header_length)
                d = data_file.read(l)
                quad_dumps.append(lib3dmm.hex_dump(d,
                    quad.section_offset + o + header_length))
        elif quad.type == b'GGST':
            dump_section = False
            magic = read('L')
            count = read('L')
            offset = read('L')
            data_file.seek(header_length + offset)

            # read index
            data_file.seek(offset + header_length)
            index = []
            for i in range(count):
                o = read('L')
                l = read('L')
                index.append((o, l))

            # seek to data and read
            for o,l in index:
                data_file.seek(o + header_length)
                d = data_file.read(l)
                quad_dumps.append(lib3dmm.hex_dump(d,
                    quad.section_offset + o + header_length))

                data_file.seek(o + header_length)
                unknown = {}
                unknown['unknown a'] = read('L')
                unknown['unknown b'] = read('L')
                unknown['unknown c'] = read('L')
                unknown['unknown d'] = read('L')
                unknown['unknown e'] = read('4s')[::-1]
                unknown['unknown f'] = read('L')
                print(pformat(unknown))

        elif quad.type == b'SCEN':
            print_header = False
            magic = read('L')
            scene = {}
            scene['frame count'] = read('L')
            scene['unknown b'] = read('L')
            scene['dissolve'] = read('L')
            print(pformat(scene))
        elif quad.type == b'MVIE':
            print_header = False
            magic = read('L')
            unknown = read('L')
        elif quad.type == b'TDT ':
            print_header = False
            tdt = {}
            magic = read('L')
            tdt['text shape'] = read('L')
            tdt['font set??'] = read('L')
            tdt['unknown d'] = read('L')
            tdt['unknown e'] = read('4s')[::-1]
            tdt['font'] = read('L')
            print(pformat(tdt))
        elif quad.type == b'TMPL':
            print_header = False
            tmpl = {}
            magic = read('L')
            tmpl['unknown b'] = read('L')
            tmpl['unknown c'] = read('L')
            tmpl['unknown d'] = read('L')
            print(pformat(tmpl))
        else:
            print('unknown quad: %s' % quad.type)

        section_dumps.append(quad.type)

        if print_header == True:
            data_file.seek(0)
            d = data_file.read(header_length)
            section_dumps.append('header')
            section_dumps.append(lib3dmm.hex_dump(d,
                quad.section_offset))

        if dump_section:
            data_file.seek(0)
            d = data_file.read(quad.section_length)
            section_dumps.append(lib3dmm.hex_dump(d,
                quad.section_offset))

        section_dumps.extend(quad_dumps)

    return section_dumps

def update_dump(new_dump):
    global current_data
    if new_dump == None:
        clear()
        return
    clear()
    enable()
    new_data = {}
    current_quad = None
    for section in new_dump:
        if type(section) == bytes:
            current_quad = section.decode('ascii')
            t.insert('end-1c', current_quad + '\n\n')
            continue
        elif type(section) == str:
            t.insert('end-1c', ' ' * 11 + section + '\n')
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
            t.insert('end-1c', '| ')
            t.insert('end-1c', characters)
            t.insert('end-1c', '\n')
        t.insert('end-1c', '\n')
    disable()
    current_data = new_data

def update_display():
    print('\n' + "*" * 60 + '\n')
    current_dump = dump_quad()
    update_dump(current_dump)

def check_if_modified():
    global last_time_modified
    try:
        time_modified = os.stat(movie_file_name).st_mtime
        if time_modified != last_time_modified:
            update_display()
            last_time_modified = time_modified
    except FileNotFoundError:
        # 3DMM uses a temp file while saving
        pass

    root.after(1000, check_if_modified)

def update_file(e):
    if selection_offset == None:
        return
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
    cmd = execute_post_update_commands()
    time.sleep(0.2)
    if cmd != 'play':
        t.focus_force()

def execute_post_update_commands():
    cmd = None
    aliases = {
            'nf': 'next-frame',
            'ns': 'next-scene',
            's': 'sleep',
            'f': 'frame',
            }
    lines = text_post_update_commands.get('1.0', 'end')
    for line in lines.split('\n'):
        line = line.strip()
        if line == '':
            continue
        try:
            cmd, args = line.split(maxsplit=1)
        except ValueError:
            cmd, args = line, ''
        finally:
            if cmd in aliases.keys():
                cmd = aliases[cmd]

            if cmd == 'sleep':
                try:
                    duration = float(args)
                except ValueError:
                    duration = 1
                time.sleep(duration)
            elif cmd == 'frame':
                try:
                    frame_number = int(args)
                    frame_number -= 1
                    if frame_number > 1:
                        system('start 3dmm_remote.ahk %s %d' %
                                ('next-frame', frame_number))
                except ValueError:
                    print('failed to parse command frame arg: %s' %
                            args)
            else:
                system('start 3dmm_remote.ahk %s %s' % (cmd, args))
    return cmd

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


def change_step(direction):
    global step_power
    if direction == 'up':
        step_power += 4
        if step_power > 28: step_power = 28
    else:
        step_power -= 4
        if step_power < 0: step_power = 0

    step.set(2 ** step_power)


top_section = Frame()
bottom_section = Frame()
debug_section = Frame(bottom_section)

unsigned_short = IntVar()
signed_long = IntVar()
unsigned_long = IntVar()
step = IntVar(value=1)
step_power = 0
hexed_long = IntVar()
double = DoubleVar()
ignore_list_string = StringVar(value='MVIE SCEN PATH GGFR GST ACTR ' +
        'GGST THUM TDT TMPL init action action-marker cut ' +
        'unknown-10')

entry_ignore_list = Entry(top_section, textvariable=ignore_list_string)
button_update = Button(top_section, text='Update', command=update_display)

entry_unsigned_short = Entry(debug_section, textvariable=unsigned_short)
entry_signed_long = Entry(debug_section, textvariable=signed_long)
entry_unsigned_long = Entry(debug_section, textvariable=unsigned_long)
entry_hexed_long = Entry(debug_section, textvariable=hexed_long)
entry_double = Entry(debug_section, textvariable=double)
entry_step = Entry(debug_section, textvariable=step)

text_post_update_commands = ScrolledText(bottom_section, font='TkFixedFont',
        width=20, height=10,
        wrap='none',
        padx=5, pady=5)

entry_ignore_list.pack(fill=X, expand=TRUE, side='left')
button_update.pack(side='right')
top_section.pack(side=TOP, fill=X)

t.pack(fill=BOTH, expand = YES)

bottom_section.pack(side=BOTTOM, fill=BOTH, expand=YES)
debug_section.pack(side=LEFT, fill=Y)

Label(debug_section, text="unsigned short").grid(row=0)
entry_unsigned_short.grid(row=0, column=1)

Label(debug_section, text="signed long").grid(row=1)
entry_signed_long.grid(row=1, column=1)

Label(debug_section, text="unsigned long").grid(row=2)
entry_unsigned_long.grid(row=2, column=1)

Label(debug_section, text="hex").grid(row=3)
entry_hexed_long.grid(row=3, column=1)

Label(debug_section, text="double").grid(row=4)
entry_double.grid(row=4, column=1)

Label(debug_section, text="step").grid(row=5)
entry_step.grid(row=5, column=1)

text_post_update_commands.pack(side=RIGHT, fill=BOTH)

entry_ignore_list.bind('<Return>', lambda e: update_display())

t.bind('<Button-1>', button_1)

root.bind('<Escape>', lambda e: t.focus())
t.bind('<Return>', update_file)
t.bind('j', lambda e: change_value('down'))
t.bind('k', lambda e: change_value('up'))
t.bind('d', lambda e: change_step('up'))
t.bind('f', lambda e: change_step('down'))
t.bind('x', lambda e: change_value_to_zero())
t.bind('u', lambda e: change_value_reset())

#root.bind('<KeyPres-a>', lambda e: print('key'))
#root.bind('<KeyRelease-a>', lambda e: print('key'))

check_if_modified()

root.mainloop()

