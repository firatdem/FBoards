# main.py
import tkinter as tk
from tkinter import ttk


class ModeSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Select Mode")
        self.selected_mode = None

        frame = ttk.Frame(root, padding="10 10 10 10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Select Mode").pack(pady=10)

        offline_button = ttk.Button(frame, text="Offline", command=lambda: self.select_mode('offline'))
        offline_button.pack(side=tk.LEFT, padx=20, pady=20)

        online_button = ttk.Button(frame, text="Online", command=lambda: self.select_mode('online'))
        online_button.pack(side=tk.RIGHT, padx=20, pady=20)

    def select_mode(self, mode):
        self.selected_mode = mode
        self.root.destroy()

    def get_mode(self):
        return self.selected_mode


if __name__ == "__main__":
    root = tk.Tk()
    app = ModeSelectorApp(root)
    root.mainloop()

    selected_mode = app.get_mode()
    if selected_mode == 'online':
        from whiteboard_online import WhiteboardApp
    else:
        from whiteboard_offline import WhiteboardApp

    root = tk.Tk()
    app = WhiteboardApp(root)
    root.mainloop()
