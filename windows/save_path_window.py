import re
import tkinter as tk
from tkinter import ttk
from logic.models import FileSavePath, User
from windows.template_window import TemplateWindow
class SavePathWindow(TemplateWindow):
    def __init__(self, master, file_save_path, onClose, onPathSetSuccess):
        super().__init__(master, "Ścieżka zapisu", "save_path", onClose)

        self.insert_frame = ttk.Frame(self.window)
        self.insert_field_frame = ttk.Frame(self.insert_frame)
        self.insert_symbol_frame = ttk.Frame(self.insert_frame)
        self.input_frame = ttk.Frame(self.window)

        self.onPathSetSuccess = onPathSetSuccess
        self.file_save_path: FileSavePath = file_save_path
        self.example_user: User = file_save_path.example_user
        self.download_datetime = file_save_path.download_datetime
        self.example_receive_datetime = file_save_path.example_receive_datetime

        self.types = file_save_path.types

        self.symbols = file_save_path.symbols

        self.symbol_buttons = []

        self.path_var = tk.StringVar()
        self.insert_var = tk.StringVar()
        self.window.grab_set()
        self.build()
        self.setDefault()
        self.placeWidgets()

    def build(self):
        self.info_label = ttk.Label(self.window,
                                    text="Wpisz ścieżkę ręcznie lub skorzystaj z listy pól (zostaną one wpisane w miejscu kursora)."
                                         "\nSłowa kluczowe zostaną automatycznie oznaczone w {}."
                                    )

        self.insert_combo = ttk.Combobox(self.insert_field_frame,
                                         textvariable=self.insert_var,
                                         values=[word.capitalize() for word in self.types],
                                         state="readonly",
                                         width=15
                                         )

        self.insert_button = ttk.Button(self.insert_field_frame,
                                        text="Wstaw pole",
                                        command=self.insert_field,
                                        width=15
                                        )
        for symbol in self.symbols:
            button = ttk.Button(
                self.insert_symbol_frame,
                text=symbol.capitalize(),
                width=7
            )
            button.bind("<Button-1>", self.insert_symbol)
            self.symbol_buttons.append(button)

        self.path_entry = ttk.Entry(self.input_frame,
                                    width=86,
                                    textvariable=self.path_var)

        self.clear_button = ttk.Button(self.input_frame,
                                       text="Wyczyść",
                                       command=self.clear
                                       )
        self.path_entry.bind("<KeyRelease>", self.on_text_change)

        self.preview_label = ttk.Label(self.window, text="Podgląd:")
        self.preview_value = ttk.Label(self.window, text="", foreground="blue")

        self.example_label = ttk.Label(self.window, text="Przykładowy wygląd:")
        self.example_preview = ttk.Label(self.window, text="", foreground="blue")

        self.save_button = ttk.Button(self.window,
                                      text="Zapisz",
                                      command=self.save
                                      )

    def placeWidgets(self):
        self.window.geometry("640x270")

        self.info_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        self.insert_frame.grid(row=1, column=0, columnspan=2, padx=5, sticky="w")
        self.insert_field_frame.grid(row=0, column=0, columnspan=2, sticky="w")
        self.insert_symbol_frame.grid(row=0, column=2, columnspan=4, padx=(15, 0), sticky="w")

        self.insert_combo.grid(row=0, column=0, padx=5, pady=5, )
        self.insert_button.grid(row=0, column=1, padx=5, pady=5, )

        for i, symbol_button in enumerate(self.symbol_buttons):
            symbol_button.grid(row=0, column=i, padx=10, pady=5, sticky="w")

        self.input_frame.grid(row=2,column=0, columnspan=3, sticky="w")
        self.path_entry.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.clear_button.grid(row=0, column=1, padx=(5,0), pady=5, sticky="w")

        self.preview_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")
        self.preview_value.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        self.example_label.grid(row=5, column=0, padx=10, sticky="w")
        self.example_preview.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        self.save_button.grid(row=7, column=0, padx=10, pady=5, sticky="w")

    def setDefault(self):
        if self.file_save_path.save_method != "":
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.file_save_path.save_method)
            self.on_text_change()

    def insert_field(self):
        field = self.insert_var.get()

        if not field:
            return

        cursor_position = self.path_entry.index(tk.INSERT)
        self.path_entry.insert(cursor_position, f"{{{field}}}")
        self.insert_combo.set("")
        self.on_text_change()

    def insert_symbol(self, event):
        symbol = event.widget["text"]
        if symbol == "Spacja":
            symbol = " "
        cursor_position = self.path_entry.index(tk.INSERT)
        self.path_entry.insert(cursor_position, f"{symbol}")
        self.on_text_change()

    def clear(self):
        self.path_entry.delete(0, tk.END)
        self.on_text_change()

    def on_text_change(self, event=None):
        try:
            if len(event.keysym) > 1 and event.char not in ["/", "\\", "{", "}"]:
                self.preview_value.config(text=self.path_entry.get())
                self.example_preview.config(text=self.file_save_path.replaceText(self.path_entry.get(),
                                                                                 self.file_save_path.example_user.user_info,
                                                                                 self.file_save_path.example_receive_datetime))
                return
            if event.state & 0x4:  # ← 0x4 is the Ctrl modifier flag
                return
        except AttributeError:
            pass

        text = self.path_entry.get()
        characters = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
        text = text.translate(characters)
        cursor_pos = self.path_entry.index(tk.INSERT)
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, text)
        self.path_entry.icursor(cursor_pos)

        new_text = text
        for word in self.types:
            if word.lower() in new_text.lower() and f"{{{word.lower()}}}" not in new_text.lower():
                new_text = re.sub(word, f"{{{word.capitalize()}}}", new_text, flags=re.IGNORECASE)

        for brackets in ["{{", "}}"]:
            if brackets in new_text:
                new_text = new_text.replace(brackets, brackets[0])
        for slash in ["//", r"\\"]:
            if slash in new_text:
                new_text = new_text.replace(slash, slash[0])

        if new_text != text:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, new_text)

        self.preview_value.config(text=new_text)
        self.example_preview.config(text=self.file_save_path.replaceText(new_text,
                                                                         self.file_save_path.example_user.user_info,
                                                                         self.file_save_path.example_receive_datetime))

    def save(self):
        self.file_save_path.save_method = self.path_var.get()
        self.file_save_path.example_save_text = self.example_preview.cget("text")
        self.window_close()
        self.onPathSetSuccess()
