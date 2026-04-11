import tkinter as tk
from tkinter import ttk
from logic.models import Filter
from windows.template_window import TemplateWindow
class FilterWindow(TemplateWindow):
    def __init__(self, master, subject_filter, onClose, onFilterSet):
        super().__init__(master, "Filtrowanie", "filter", onClose)
        self.input_frame = ttk.Frame(self.window)
        self.filter_var = tk.StringVar()
        self.onFilterSet = onFilterSet
        self.subject_filter: Filter = subject_filter
        self.window.grab_set()
        self.build()
        self.setDefault()
        self.placeWidgets()

    def build(self):
        self.info_label = ttk.Label(self.window,
                                    text="Wpisz co ma zawierać temat wiadomości, słowa kluczowe lub tekst oddziel przecinkiem.")

        self.filter_input = ttk.Entry(self.input_frame,
                                      width=70,
                                      textvariable=self.filter_var)

        self.clear_button = ttk.Button(self.input_frame,
                                      text="Wyczyść",
                                      command=self.clear
                                      )

        self.save_button = ttk.Button(self.window,
                                      text="Zapisz",
                                      command=self.save
                                      )

    def placeWidgets(self):
        self.window.geometry("550x120")
        self.input_frame.grid(row=1,column=0, columnspan=3, sticky="w")
        self.info_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        self.filter_input.grid(row=0, column=0, columnspan=2, padx=10, sticky="w")
        self.clear_button.grid(row=0, column=3, padx=(5,0), pady=5, sticky="w")
        self.save_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    def setDefault(self):
        if self.subject_filter.filter_text != "":
            self.filter_input.delete(0, tk.END)
            self.filter_input.insert(0, self.subject_filter.filter_text)

    def clear(self):
        self.filter_input.delete(0, tk.END)

    def save(self):
        self.subject_filter.readFilter(self.filter_input.get())
        self.window_close()
        self.onFilterSet()
