from tkinter import *
from tkinter import ttk
import tkinter.font
import lib3dmm

verbose_type_names = {
    b'MVIE': 'Movie : MVIE',
    b'GST ': 'String Table : GST',
    b'MSND': 'Movie Sound : MSND',
    b'WAVE': 'Waveform Audio : WAVE',
    b'SCEN': 'Scene : SCEN',
    b'ACTR': 'Actor : ACTR',
    b'GGAE': 'Actor Event : GGAE',
    b'PATH': 'Path : PATH',
    b'GGFR': 'Frame Events : GGFR',
    b'THUM': 'Thumbnail : THUM',
    b'GGST': 'Dynamic String Table : GGST',
    b'TDT': '3D Text : TDT',
    b'BMDL': 'Body Model : BMDL',
    b'TDFF': '3D Font on File : TDFF',
    b'CMTL': 'Custom Material : CMTL',
    b'MTRL': 'Material : MTRL',
    b'TDF': '3D Font : TDF'
}


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack(fill='both', expand=True)
        self.createWidgets()

    def createWidgets(self):
        self.tree = ttk.Treeview(self)
        self.tree['columns'] = ('id', 'string', 'offset', 'length')
        self.tree.heading('id', text='ID')
        self.tree.heading('string', text='String')
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
        for ref in chunk.references:
            child = self.movie.get_chunk(ref)
            self.walk_chunk_tree(child, node_id)

    def delete_tree(self):
        for node in self.tree.get_children(''):
            self.tree.delete(node)


app = Application()
app.master.title('Movie File Layout')
app.load_movie('walk.3mm')
app.mainloop()

