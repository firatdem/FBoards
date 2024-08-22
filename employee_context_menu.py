# NOT BEING USED

import tkinter as tk

class EmployeeContextMenu:
    def __init__(self, parent, box, delete_callback, copy_callback):
        self.parent = parent
        self.box = box
        self.delete_callback = delete_callback
        self.copy_callback = copy_callback

        self.menu = tk.Menu(parent, tearoff=0)
        self.menu.add_command(label="Delete", command=self.delete)
        self.menu.add_command(label="Copy", command=self.copy)

    def show(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def delete(self):
        if self.delete_callback:
            self.delete_callback(self.box)

    def copy(self):
        if self.copy_callback:
            self.copy_callback(self.box)
