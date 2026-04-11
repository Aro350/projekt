import socket
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror, showinfo
from connection import MailDetails
from windows.template_window import TemplateWindow

class MailConnectionWindow(TemplateWindow):
    def __init__(self, master, connection, onClose, onConnectionSuccess):
        super().__init__(master, "Połączenie", "connection", onClose)
        self.connection = connection
        self.onConnectionSuccess = onConnectionSuccess
        self.address = tk.StringVar(value="np. stud.prz.edu.pl")
        self.port = tk.StringVar()
        self.protocol = tk.StringVar(value="IMAP")
        self.setDefaultPort()
        self.connection_status = tk.StringVar(value="")
        self.build()
        self.placeWidgets()

    def build(self):
        self.imap_radio = ttk.Radiobutton(self.window, text="IMAP", variable=self.protocol, value="IMAP",
                                          command=self.setDefaultPort)
        self.pop_radio = ttk.Radiobutton(self.window, text="POP3", variable=self.protocol, value="POP3",
                                         command=self.setDefaultPort)

        self.address_label = ttk.Label(self.window, text="Adres poczty: ")
        self.address_input = ttk.Entry(self.window, textvariable=self.address)

        self.port_label = ttk.Label(self.window, text="Port: ")
        self.port_input = ttk.Entry(self.window, textvariable=self.port)

        self.connect_button = ttk.Button(self.window, text="Połącz", command=self.submit)
        self.status_label = ttk.Label(self.window, textvariable=self.connection_status)

        self.address_input.bind("<FocusIn>", self.focus_in)
        self.address_input.bind("<FocusOut>", self.focus_out)

    def placeWidgets(self):
        self.window.geometry("250x170")

        self.imap_radio.grid(row=0, column=0, padx=5, pady=5)
        self.pop_radio.grid(row=0, column=1, padx=5, pady=5)

        self.address_label.grid(row=1, column=0, padx=5, pady=5)
        self.address_input.grid(row=1, column=1, padx=5, pady=5)

        self.port_label.grid(row=2, column=0, padx=5, pady=5)
        self.port_input.grid(row=2, column=1, padx=5, pady=5)

        self.connect_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

    def focus_in(self, event=None):
        if self.address_input.get().strip() == "np. stud.prz.edu.pl":
            self.address_input.delete(0, tk.END)

    def focus_out(self, event=None):
        if self.address_input.get().strip() == "":
            self.address_input.insert(0, "np. stud.prz.edu.pl")

    def setDefaultPort(self):
        protocol = self.protocol.get()
        if protocol == "IMAP":
            self.port.set("993")
        elif protocol == "POP3":
            self.port.set("995")

    def submit(self):
        self.connection_status.set("Łączenie...")
        self.window.update_idletasks()
        try:
            mail_details = MailDetails()
            if mail_details.setDetails(address=self.address.get(),
                                         port=self.port.get(),
                                         protocol=self.protocol.get()):
                if self.connection.connect(mail_details):
                    self.window_close()
                    showinfo("Połączenie",
                             f"Połączono:\nAdres: {self.address.get()}\nPort: {self.port.get()}\nProtokół: {self.protocol.get()}")
                    self.onConnectionSuccess(mail_details)
            else:
                self.window.focus_force()
            self.connection_status.set("")
            self.window.update_idletasks()

        except (socket.gaierror, OSError):
            showerror("Błąd", "Błąd połączenia.\nSprawdź połączenie internetowe i dostępność serwera.", parent = self.window)
            self.connection_status.set("")
            self.window.focus_force()

            return False
        except (TimeoutError,socket.timeout):
            showerror("Błąd",
                      "Przekroczono limit czasu połączenia. Otrzymano błędny port lub usługa jest chwilowo niedostępna", parent = self.window)
            self.connection_status.set("")
            self.window.focus_force()
            return False

        except ValueError as e:
            showerror("Błąd", str(e))
            self.connection_status.set("")
            self.window.focus_force()
            return False

        except Exception as e:
            self.connection_status.set("")
            showerror("Błąd", f"\n{e}", parent = self.window)
            exit()
