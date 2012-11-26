from tkinter import *
from tkinter import ttk
import lib3dmm

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

        self.tree_scroll = Scrollbar(self)
        self.tree.config(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.config(command=self.tree.yview)
        self.tree_scroll.grid(row=0, column=1, sticky='news')
        self.rowconfigure(0, weight=1) 

        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=0) 

    def load_movie(self, name):
        self.movie = lib3dmm.Movie(name)

        root_quad = self.movie.get_root_quad()
        self.walk_quad_tree(root_quad, '')

    def walk_quad_tree(self, quad, parent_id):
        id = self.tree.insert(parent_id,
                'end',
                text=quad.type,
                open=True,
                values=(quad.id,
                    quad.string,
                    quad.section_offset,
                    quad.section_length))
        for ref in quad.references:
            child = self.movie.get_quad(ref)
            self.walk_quad_tree(child, id)

    def delete_tree(self):
        for node in self.tree.get_children(''):
            self.tree.delete(node)


app = Application()
app.master.title('Movie File Layout')
app.load_movie('test_movie.3mm')
app.mainloop()

