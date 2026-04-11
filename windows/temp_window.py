import tkinter as tk
from tkinter import ttk
class TempWindow:
    def __init__(self, master, title, text):
        self.temp_window = tk.Toplevel(master)
        self.temp_window.title(title)
        self.temp_window.geometry("250x100")
        self.temp_window.transient(master)
        self.temp_window.grab_set()
        self.text_label = ttk.Label(self.temp_window,
                                    text=text)
        self.text_label.grid(row=0,column=0,columnspan=2)
        self.temp_window.update()

    def addCombobox(self, columns=None):
        self.text_label.grid(padx=10,pady=5)
        self.selected_value = tk.StringVar()
        self.temp_cb = ttk.Combobox(self.temp_window, values=columns, width=25, textvariable=self.selected_value)
        self.temp_cb.grid(row=1,column=0,columnspan=2,padx=10,pady=(5,10))
        self.btn = ttk.Button(self.temp_window, text="Zatwierdź", command=self.closeWindow)
        self.btn.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        self.temp_window.geometry("")

    def closeWindow(self):
        self.temp_window.destroy()

    def changeContent(self, text):
        self.text_label.config(text=text)
        self.temp_window.update()
