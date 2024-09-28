from tkinter import *
from tkinter import ttk
import tkinter.font
import lib3dmm
import struct

verbose_type_names = {
    'MVIE': 'Movie : MVIE',
    'GST ': 'String Table : GST',
    'MSND': 'Movie Sound : MSND',
    'WAVE': 'Waveform Audio : WAVE',
    'SCEN': 'Scene : SCEN',
    'ACTR': 'Actor : ACTR',
    'GGAE': 'Actor Event : GGAE',
    'PATH': 'Path : PATH',
    'GGFR': 'Frame Events : GGFR',
    'THUM': 'Thumbnail : THUM',
    'GGST': 'Dynamic String Table : GGST',
    'TDT': '3D Text : TDT',
    'BMDL': 'Body Model : BMDL',
    'TDFF': '3D Font on File : TDFF',
    'CMTL': 'Custom Material : CMTL',
    'MTRL': 'Material : MTRL',
    'TDF': '3D Font : TDF'
}


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack(fill='both', expand=True)
        self.createWidgets()

    def createWidgets(self):
        self.tree = ttk.Treeview(self)
        self.tree['columns'] = ('key', 'value', 'offset', 'length')
        self.tree.heading('key', text='Key')
        self.tree.heading('value', text='Value')
        self.tree.heading('offset', text='Offset')
        self.tree.heading('length', text='Length')
        self.tree.grid(row=0, column=0, sticky='news')

        treeview_font = tkinter.font.Font(family='Arial', size=24)
        style = ttk.Style()
        style.configure('Treeview', font=treeview_font)

        self.tree_scroll = Scrollbar(self)
        self.tree.config(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.config(command=self.tree.yview)
        self.tree_scroll.grid(row=0, column=1, sticky='news')
        self.rowconfigure(0, weight=1) 

        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=0) 

    def load_movie(self, name):
        self.movie = lib3dmm.ChunkFile(name)

        root_chunk = self.movie.get_root_chunk()
        self.walk_chunk_tree(root_chunk, '')

    def walk_chunk_tree(self, chunk, parent_id):
        type_name = verbose_type_names.get(chunk.type, chunk.type)

        node_id = self.tree.insert(parent_id,
                'end',
                text=type_name,
                open=True,
                values=(chunk.id,
                    chunk.string,
                    chunk.section_offset,
                    chunk.section_length))

        if chunk.type == 'MVIE':
            ( bo, osk, current_version, backward_version,) = struct.unpack('<hhhh', chunk.data)
            #print(f'{bo=:04x} {osk=:04x} {current_version=} {backward_version=}')
            _ = self.tree.insert(node_id,
                    'end',
                    text='attribute',
                    open=True,
                    values=('current_version', current_version, 0, 0))
            _ = self.tree.insert(node_id,
                    'end',
                    text='attribute',
                    open=True,
                    values=('backward_version', backward_version, 0, 0))
        elif chunk.type == 'SCEN':
            pass
        elif chunk.type == 'ACTR':
            pass
        elif chunk.type == 'PATH':
            pass
        elif chunk.type == 'THUM':
            pass
        elif chunk.type == 'GGAE':
            pass
        elif chunk.type == 'GGFR':
            pass
        elif chunk.type == 'GST ':
            bo, osk, cbEntry, ibstMac, bstMac, cbstFree = struct.unpack_from('<hhllll', chunk.data, 0)
            #print(f'{bo=:04x} {osk=:04x} {cbEntry=} {ibstMac=} {bstMac=} {cbstFree=} ')

            pos = 20

            for i in range(ibstMac):
                string_length = struct.unpack_from('<B', chunk.data, pos)[0]
                pos += 1
                s = chunk.data[pos:pos+string_length]
                s = s.decode('ascii')
                #print(f'{string_length=:3d}, {s=}')
                pos += string_length
                _ = self.tree.insert(node_id,
                        'end',
                        text='string',
                        open=True,
                        values=(
                            i,
                            s,
                            pos,
                            string_length))

        elif chunk.type == 'GGST':
            pass
        elif chunk.type == 'MSND':
            pass
        elif chunk.type == 'WAVE':
            pass
        else:
            print(chunk.type)
            print(chunk.data)

        for ref in chunk.references:
            child = self.movie.get_chunk(ref)
            assert child is not None
            self.walk_chunk_tree(child, node_id)

    def delete_tree(self):
        for node in self.tree.get_children(''):
            self.tree.delete(node)


app = Application()
app.master.title('Movie File Layout')
app.load_movie('walk.3mm')
app.mainloop()

