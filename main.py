import tkinter as tk
from logic.models import UserFile, FileSavePath, Date
from logic.connection import Connection, MailDetails, MailboxDetails
from logic.config import Config
from windows.main_window import MainWindow
# =========================
# APLIKACJA
# =========================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.minsize(640,460)
        self.root.title("Aplikacja pocztowa")
        self.app_state = AppState()
        self.connection = Connection()
        self.mail_details = MailDetails()
        self.mailbox_details = MailboxDetails()
        self.config = Config()
        self.user_file = UserFile()
        self.date = Date()
        self.file_save_path = FileSavePath()

        self.main_window = MainWindow(
            self.root,
            self.app_state,
            self.mail_details,
            self.mailbox_details,
            self.connection,
            self.config,
            self.user_file,
            self.date,
            self.file_save_path
        )

    def run(self):
        self.root.mainloop()

# =========================
# STAN APLIKACJI
# =========================
class AppState:
    def __init__(self):
        self.state = {
            "mail_connected": False,
            "logged_in": False,
            "mailbox_set": False,
            "user_file_set": False,
            "save_loc_set": False,
            "date_set": False,
            "save_method_set": False
        }

    def clearAppState(self):
        for key, value in self.state.items():
            self.state[key] = False

    def checkAppStatus(self):
        return all(self.state.values())

# =========================
# START
# =========================
if __name__ == "__main__":
    app = App()
    app.run()