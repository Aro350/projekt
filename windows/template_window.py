import tkinter as tk

class TemplateWindow:
    def __init__(self, master, title, window_name, onClose):
        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.grab_set()
        self.window_name = window_name
        self.onClose = onClose
        self.window.protocol("WM_DELETE_WINDOW", self.window_close)

    def window_close(self):
        self.window.destroy()
        self.onClose(self.window_name)
