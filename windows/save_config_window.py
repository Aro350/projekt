import tkinter as tk
from tkinter import ttk
from windows.template_window import TemplateWindow
class SaveConfigWindow(TemplateWindow):
    def __init__(self, master, save_config_choice, onClose, onConfigSave):
        super().__init__(master, "Konfiguracja", "save_config", onClose)
        self.button_frame = ttk.Frame(self.window)
        self.onConfigSave = onConfigSave
        self.fields = [
            "mail",
            "credentials",
            "mailbox",
            "user_file",
            "save_location",
            "date",
            "save_method",
            "filter"
        ]
        self.texts = [
            "adres, port, protokół",
            "nazwa użytkownika, hasło",
            "skrzynka",
            "plik z użytkownikami",
            "lokalizacja zapisu",
            "zakres czasu",
            "sposób zapisu",
            "filtr tematu"
        ]
        self.checkbuttons = []
        self.checkbutton_vars = save_config_choice
        self.window.grab_set()
        self.build()
        self.placeWidgets()

    def build(self):
        self.info_label = ttk.Label(self.window, text="Wybierz informacje do zapisania w pliku konfiguracyjnym.")

        for field, text in zip(self.fields, self.texts):
            var = tk.BooleanVar(value=self.checkbutton_vars[field].get() if field in self.checkbutton_vars else False)
            # try:
            #     if self.checkbutton_vars[field].get():
            #         var.set(True)
            # except:
            #     pass
            check_button = ttk.Checkbutton(self.window, text=text, variable=var)
            self.checkbuttons.append(check_button)
            self.checkbutton_vars[field] = var


        self.check_button = ttk.Button(self.button_frame,
                                              text="Zaznacz wszystko",
                                              command=self.checkAll
                                              )

        self.uncheck_button = ttk.Button(self.button_frame,
                                              text="Odznacz wszystko",
                                              command=self.uncheckAll
                                              )

        self.save_button = ttk.Button(self.window,
                                      text="Zapisz",
                                      command=self.save
                                      )
    def placeWidgets(self):
        self.info_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        self.button_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="w")
        self.check_button.grid(row=0, column=0, padx=(0,15), sticky="w")
        self.uncheck_button.grid(row=0, column=1, sticky="w")
        for i, checkbox in enumerate(self.checkbuttons):
            checkbox.grid(row = i+2, column = 0, padx=10,pady=5, sticky="w")

        self.save_button.grid(row=len(self.fields)+3, column=0, padx=10, pady=(15,10), sticky="w")
        self.window.geometry("")

    def checkAll(self):
        for var in self.checkbutton_vars.values():
            var.set(True)

    def uncheckAll(self):
        for var in self.checkbutton_vars.values():
            var.set(False)

    def save(self):
        self.window_close()
        self.onConfigSave(self.checkbutton_vars)
        return True
