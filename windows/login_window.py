import imaplib
import poplib
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror, showwarning, showinfo
from connection import Connection, MailDetails
from models import UserCredentials
from windows.template_window import TemplateWindow
import socket

class LoginWindow(TemplateWindow):
    def __init__(self, master,
                 connection,
                 mail_details,
                 app_state,
                 onClose,
                 onLoginSuccess):
        super().__init__(master, "Logowanie", "login", onClose)
        self.onLoginSuccess = onLoginSuccess
        self.connection: Connection = connection
        self.mail_details: MailDetails = mail_details
        self.app_state = app_state
        self.protocol = self.connection.protocol
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.login_status = tk.StringVar(value="")
        self.build()
        self.placeWidgets()

    def build(self):
        self.entry_username = ttk.Entry(self.window, textvariable=self.username, width=25)
        self.entry_password = ttk.Entry(self.window, textvariable=self.password, show="*",width=25)
        self.login_button = ttk.Button(self.window, text="Zaloguj", command=self.submit)
        self.status_label = ttk.Label(self.window, textvariable=self.login_status)

    def placeWidgets(self):
        self.window.geometry("230x130")

        ttk.Label(self.window, text="Login").grid(row=0, column=0, padx=(5,10), pady=5)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5, sticky="nswe")

        ttk.Label(self.window, text="Hasło").grid(row=1, column=0, padx=(5,10), pady=5)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5, sticky="nswe")

        self.login_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(5,10))

    def submit(self):
        user_credentials = UserCredentials(username=self.username.get().strip(),
                                           password=self.password.get())

        if not user_credentials.checkCredentials(): return

        try:
            if not self.connection.check_connection():
                if self.connection.reconnect(self.mail_details, self.app_state):
                    pass
                else:
                    raise ConnectionAbortedError
            self.login_status.set("Logowanie...")
            self.window.update_idletasks()
            if self.connection.auth(user_credentials):
                self.window_close()
                showinfo("Logowanie", f"Zalogowano:\nUżytkownik: {user_credentials.username}")
                self.onLoginSuccess(self.connection.connect_host, user_credentials)
                return True
            else:
                showwarning("Logowanie", "Problem z logowaniem, spróbuj ponownie")

        except (ConnectionResetError,
                ConnectionAbortedError,
                imaplib.IMAP4.abort,
                OSError,
                AttributeError,
                imaplib.IMAP4.error,
                poplib.error_proto,
                TimeoutError,
                socket.timeout,
                ) as e:

            if "Authentication failed" in str(e):
                showerror("Błąd logowania", "Sprawdź dane logowania \nlub \nspróbuj ponownie później", parent=self.window)
                self.login_status.set("")
                self.window.update_idletasks()

            elif "auth failure" in str(e) or "access disabled" in str(e):
                showerror("Błąd połączenia","Błędne dane logowania\nlub\ndostęp przez wybrany protokół nie jest włączony")
                self.login_status.set("")
                self.window.update_idletasks()

            elif self.connection.check_connection_info(self.window, self.app_state):
                self.submit()
                return True

            elif all([word in str(e) for word in ("NoneType", "login")]):
                self.login_status.set("")

            else:
                pass
                # showerror("Błąd", f"{type(e)}______{e}_______{e.__class__.__name__}")
            self.window.focus_force()
            return

        except Exception as e:
            showerror("Błąd", f"{type(e)}______{e}_______{e.__class__.__name__}")
        self.login_status.set("")
        self.window.update_idletasks()
