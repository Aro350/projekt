import imaplib
import poplib
from tkinter import ttk
from tkinter.messagebox import showerror, showinfo, askretrycancel
from connection import Connection
from windows.template_window import TemplateWindow
import socket

class MailboxSelectionWindow(TemplateWindow):
    def __init__(self, master, connection, mailbox_details, app_state, onClose, onMailboxSelectionSuccess):
        super().__init__(master, "Wybór skrzynki", "mailbox", onClose)
        self.onMailboxSelectionSuccess = onMailboxSelectionSuccess
        self.mailbox_details = mailbox_details
        self.connection: Connection = connection
        self.app_state = app_state
        self.build()
        self.placeWidgets()

    def build(self):
        self.mailbox_choice = ttk.Combobox(self.window, width=30)
        self.save_choice = ttk.Button(self.window, text="Zapisz", command=self.saveMailbox)

    def placeWidgets(self):
        self.window.geometry("250x100")

        for i in range(3):
            self.window.columnconfigure(i, weight=1)

        self.mailbox_choice.grid(row=0, column=0, columnspan=3, pady=10)
        self.save_choice.grid(row=1, column=0, columnspan=3, pady=5)
        self.fillMailboxes()

    def fillMailboxes(self):
        try:
            mailboxes = ["", *self.mailbox_details.getAllMailboxes(self.connection)]
            self.mailbox_choice.config(values=mailboxes)

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

            err_msg = str(e).lower()
            connected = self.connection.manageConnectionLoss(err_msg,
                                                             self.window,
                                                             self.app_state)

            if connected:
                showinfo("Wznowienie", "Sesja odświeżona.")
                self.window.focus_force()
                self.fillMailboxes()
                return True
            return False
        except Exception as e:
            showerror("Błąd",str(e))
            pass


    def saveMailbox(self):
        chosen_mailbox = self.mailbox_choice.get()
        try:

            self.onMailboxSelectionSuccess(chosen_mailbox)
            self.window_close()

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

            err_msg = str(e).lower()
            connected = self.connection.manageConnectionLoss(err_msg,
                                                             self.window,
                                                             self.app_state)

            self.window.focus_force()
            if connected:
                retry = askretrycancel("Wznowienie", "Sesja odświeżona. Czy spróbować ponownie?")
                if retry:
                    self.saveMailbox()
                    return True
                return True
            return False
        except Exception as e:
            showerror("Błąd", f"{type(e)}______{e}_______{e.__class__.__name__}")
