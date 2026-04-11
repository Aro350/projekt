import imaplib
import poplib
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from tkinter.messagebox import showwarning, showerror, showinfo, askyesno, askretrycancel
from logic.models import UserFile, FileSavePath, Filter, Date, UserCredentials
from logic.connection import Connection, MailDetails, MailboxDetails
from logic.config import Config
from logic.mail import MailData, Download
from windows.temp_window import TempWindow
from windows.connection_window import MailConnectionWindow
from windows.login_window import LoginWindow
from windows.mailbox_window import MailboxSelectionWindow
from windows.date_window import DateWindow
from windows.save_path_window import SavePathWindow
from windows.filter_window import FilterWindow
from windows.save_config_window import SaveConfigWindow
import socket

class MainWindow:
    def __init__(self,
                 master,
                 app_state,
                 mail_details,
                mailbox_details,
                 connection,
                 config,
                 user_file,
                 date,
                 file_save_path
                 ):

        self.master = master
        self.app_state = app_state
        self.config: Config = config

        self.connection: Connection = connection

        self.mail_details: MailDetails = mail_details
        self.mailbox_details: MailboxDetails = mailbox_details
        self.user_file: UserFile = user_file
        self.date: Date = date
        self.file_save_path: FileSavePath = file_save_path

        self.user_credentials = UserCredentials()
        self.subject_filter = None

        self.save_config_choice = {}

        self.login_opened = False
        self.mail_connection_opened = False
        self.mailbox_selection_opened = False
        self.date_selection_opened = False
        self.save_path_opened = False
        self.filter_opened = False
        self.save_config_opened = False

        self.download_flag = 0

        self.build()
        self.placeWidgets()

    def build(self):
        self.info_label = ttk.Label(self.master,
                                    text="Uwaga! Zbyt długi czas nieaktywności spowoduje rozłączenie z serwerem. Należy wtedy połączyć się z nim ponownie.")

        self.load_config_button = ttk.Button(self.master, text="Wczytaj konfigurację", command=self.openLoadConfig)
        self.mail_connection_button = ttk.Button(self.master, text="Połącz z pocztą", command=self.manageConnection)
        self.login_button = ttk.Button(self.master, text="Zaloguj do poczty", command=self.manageLogin,state=tk.DISABLED)
        self.mailbox_button = ttk.Button(self.master, text="Wybierz skrzynkę", command=self.openMailboxSelection,state=tk.DISABLED)
        self.user_file_button = ttk.Button(self.master, text="Wczytaj plik z użytkownikami",command=self.getUserFileLocation)
        self.file_save_location_button = ttk.Button(self.master, text="Wybierz lokalizację zapisu",command=self.getFileSaveLocation)
        self.set_date_button = ttk.Button(self.master, text="Wybierz zakres czasu", command=self.openDateSettings)
        self.set_save_path_button = ttk.Button(self.master, text="Wybierz sposób zapisu", command=self.openSavePath, state=tk.DISABLED)
        self.filter_button = ttk.Button(self.master, text="Dodaj filtr tematu", command=self.openFilter)
        self.download_button = ttk.Button(self.master, text="Pobierz załączniki", command=self.downloadAttachments,state=tk.DISABLED)
        self.save_config_button = ttk.Button(self.master, text="Zapisz konfigurację", command=self.saveConfig)

        self.config_label = ttk.Label(self.master, text="Konfiguracja: ")
        self.connection_label = ttk.Label(self.master, text="Poczta: ")
        self.login_label = ttk.Label(self.master, text="Użytkownik: ")
        self.mailbox_label = ttk.Label(self.master, text="Skrzynka: ")
        self.user_file_label = ttk.Label(self.master, text="Plik z użytkownikami: ")
        self.file_save_label = ttk.Label(self.master, text="Lokalizacja zapisu: ")
        self.date_label = ttk.Label(self.master, text="Zakres czasu: ")
        self.save_path_label = ttk.Label(self.master, text="Sposób zapisu: ")
        self.filter_label = ttk.Label(self.master, text="Filtr tematu: ")
        self.save_config_label = ttk.Label(self.master, text="Zapisany plik: ")

        self.config_text = ttk.Label(self.master)
        self.connection_text = ttk.Label(self.master)
        self.login_text = ttk.Label(self.master)
        self.mailbox_text = ttk.Label(self.master)
        self.user_file_text = ttk.Label(self.master)
        self.file_save_text = ttk.Label(self.master)
        self.date_text = ttk.Label(self.master)
        self.save_path_text = ttk.Label(self.master)
        self.filter_text = ttk.Label(self.master)
        self.save_config_text = ttk.Label(self.master)

    def placeWidgets(self):
        #700x460
        self.master.geometry("")
        self.master.grid_columnconfigure(0, weight=0)
        self.master.grid_columnconfigure(1, weight=0)
        self.master.grid_columnconfigure(2, weight=1)
        self.info_label.grid(row=0, column=0, columnspan=3, padx=5, pady=(5, 0), sticky="w")

        buttons = [
            self.load_config_button,
            self.mail_connection_button,
            self.login_button,
            self.mailbox_button,
            self.user_file_button,
            self.file_save_location_button,
            self.set_date_button,
            self.set_save_path_button,
            self.filter_button,
            self.save_config_button,
        ]

        labels = [
            self.config_label,
            self.connection_label,
            self.login_label,
            self.mailbox_label,
            self.user_file_label,
            self.file_save_label,
            self.date_label,
            self.save_path_label,
            self.filter_label,
            self.save_config_label,
        ]

        self.texts = [
            self.config_text,
            self.connection_text,
            self.login_text,
            self.mailbox_text,
            self.user_file_text,
            self.file_save_text,
            self.date_text,
            self.save_path_text,
            self.filter_text,
            self.save_config_text,
        ]

        for i, button in enumerate(buttons):
            button.grid(row=i + 1, column=0, padx=5, pady=7, sticky="w")
            button.config(width=30)

        for i, label in enumerate(labels):
            label.grid(row=i + 1, column=1, padx=5, pady=7, sticky="w")

        for i, text in enumerate(self.texts):
            text.grid(row=i + 1, column=2, padx=5, pady=7, sticky="w")
            text.config(text="")
        self.download_button.grid(row=len(buttons) + 3, column=0, columnspan=3, padx=5, pady=(10, 15), sticky="wesn")
        self.download_button.config(width=30)

    def changeWindowStatus(self, window):
        match window:
            case "login":
                self.login_opened = False
            case "connection":
                self.mail_connection_opened = False
            case "mailbox":
                self.mailbox_selection_opened = False
            case "save_path":
                self.save_path_opened = False
            case "date":
                self.date_selection_opened = False
            case "filter":
                self.filter_opened = False
            case "save_config":
                self.save_config_opened = False

    def openLoadConfig(self):
        config_file_loc = askopenfilename(title="Wybierz plik z zapisaną konfiguracją",
                                          filetypes=(("Json File", "*.json"),))
        if not config_file_loc:
            return False

        try:
            self.resetData()

            self.config.readConfigFile(config_file_loc)
            self.config.loadConfig(self)

            self.config_text.config(text=config_file_loc)
            self.refreshUi()
            showinfo("Sukces", "Pomyślnie wczytano plik konfiguracyjny.")
            return True

        except ValueError as e:
            showerror("Błąd", str(e))
            self.config.clearConfig()
            return False

        except Exception as e:
            showerror("Błąd", f"Plik konfiguracyjny zawiera błąd:\n{type(e)}\n{e}\n{e.__class__.__name__}")
            self.config.clearConfig()
            return False

    def clearUI(self):
        for text in self.texts:
            text.config(text="")

    def resetData(self):
        self.clearUI()
        if self.connection.connect_host:
            self.disconnectMail()
        self.config.clearConfig()
        self.app_state.clearAppState()

        self.user_file = UserFile()
        self.file_save_path = FileSavePath()
        self.date = Date()
        self.subject_filter = None

        self.config_text.config(text="")
        self.refreshUi()

    def manageConnection(self):
        if self.app_state.state["mail_connected"]:
            self.disconnectMail()
        else:
            self.openMailConnection()

    def manageLogin(self):
        if self.app_state.state["logged_in"]:
            self.logoutMail()
        else:
            self.openLogin()

    def openMailConnection(self):
        try:
            if not self.mail_connection_opened:
                self.mail_connection_opened = True
                MailConnectionWindow(self.master,
                                     self.connection,
                                     onClose=self.changeWindowStatus,
                                     onConnectionSuccess=self.onConnectionSuccess)
            else:
                showerror("Błąd", "Okno jest już otwarte")
        except ValueError:
            return

    def openLogin(self):
        if not self.login_opened:
            self.login_opened = True
            LoginWindow(self.master, self.connection, self.mail_details, self.app_state,
                        onClose=self.changeWindowStatus, onLoginSuccess=self.onLoginSuccess)
        else:
            showerror("Błąd", "Okno jest już otwarte")

    def disconnectMail(self, flag=0):
        self.connection.disconnect()
        self.user_credentials = UserCredentials()
        self.mailbox_details = MailboxDetails()
        self.app_state.state["mail_connected"] = False
        self.app_state.state["logged_in"] = False
        self.app_state.state["mailbox_set"] = False
        self.login_text.config(text="")
        self.mailbox_text.config(text="")
        if flag == 0:
            self.mail_details = MailDetails()
            self.connection_text.config(text="")
            showinfo("Połączenie", "Rozłączono z pocztą")
        self.refreshUi()

    def logoutMail(self):
        self.disconnectMail(flag=1)
        self.connection.clearUserInfo()
        if self.connection.connect(self.mail_details):
            self.onConnectionSuccess(self.mail_details)
            self.connection.protocol = self.mail_details.protocol
            showinfo("Połączenie", "Wylogowano z poczty")
        else:
            self.connection_text.config(text="")
        self.refreshUi()

    def openMailboxSelection(self):
        if not self.mailbox_selection_opened:
            self.mailbox_selection_opened = True
            MailboxSelectionWindow(self.master,
                                   self.connection,
                                   self.mailbox_details,
                                   self.app_state,
                                   onClose=self.changeWindowStatus,
                                   onMailboxSelectionSuccess=self.onMailboxSelectionSuccess)
        else:
            showerror("Błąd", "Okno jest już otwarte")

    def openDateSettings(self):
        if not self.date_selection_opened:
            self.date_selection_opened = True
            DateWindow(self.master, self.date, onClose=self.changeWindowStatus, onDateSetSuccess=self.onDateSetSuccess)
        else:
            showerror("Błąd", "Okno jest już otwarte")

    def getUserFileLocation(self):
        try:
            user_file_loc = askopenfilename(title="Wybierz plik Excel z użytkownikami",
                                            filetypes=[("Excel files", "*.xlsx *.xls")])
            if not user_file_loc:
                return False
            self.user_file = UserFile()
            if self.user_file.convertFileToUsers(user_file_loc):
                self.onUserFileLoaded()
            elif self.selectEmailColumnWindow() and self.user_file.convertFileToUsers(user_file_loc):
                self.onUserFileLoaded()
            else:
                return False
        except ValueError as e:
            showerror("Błąd", f"{e}")
        except Exception as e:
            showerror("Błąd", f"{type(e)}______{e}_______{e.__class__.__name__}")

    def selectEmailColumnWindow(self):
        self.master.bell()
        if askyesno("Błąd","Nie znaleziono kolumny zawierajacej adres email. \nWybrać kolumnę ręcznie?"):
            temp_colum_selection = TempWindow(self.master, "Wybór kolumny",
                                              "Wybierz kolumnę zawierającą adresy/nazwy użytkowników:")
            temp_colum_selection.addCombobox(self.user_file.column_names)
            self.master.wait_window(temp_colum_selection.temp_window)
            chosen_column = temp_colum_selection.selected_value.get()
            if chosen_column:
                self.user_file.email_column = chosen_column
                return True
        return False

    def onUserFileLoaded(self):
        self.user_file_text.config(text=self.user_file.user_file_location)
        self.app_state.state["user_file_set"] = True
        self.file_save_path.types = self.user_file.column_names + list(self.file_save_path.download_datetime.keys()) + list(self.file_save_path.example_receive_datetime.keys())
        self.file_save_path.types.remove(self.user_file.email_column)
        self.app_state.state["save_method_set"] = False
        self.file_save_path.save_method = ""
        self.file_save_path.save_method_for_user = ""
        self.file_save_path.example_save_text = ""
        self.setExampleUser()
        self.set_save_path_button.config(state=tk.NORMAL)
        self.refreshUi()

    def setExampleUser(self):
        self.file_save_path.example_user = None
        for user in self.user_file.users_class_list:
            if "NONE" not in user.user_info.values():
                self.file_save_path.example_user = user
                break
        if not self.file_save_path.example_user:
            self.file_save_path.example_user = self.user_file.users_class_list[0]

    def getFileSaveLocation(self):
        save_loc = askdirectory(title="Wybierz folder do zapisu załączników")
        if save_loc == "":
            showwarning("Ostrzeżenie", "Nie wybrano lokalizacji do zapisu plików")
        else:
            self.file_save_path.save_location = save_loc
            self.file_save_text.config(text=f"{save_loc}/")
            self.app_state.state["save_loc_set"] = True
            self.refreshUi()

    def openSavePath(self):
        if not self.save_path_opened:
            self.save_path_opened = True
            SavePathWindow(self.master, self.file_save_path, onClose=self.changeWindowStatus,
                           onPathSetSuccess=self.onPathSetSuccess)
        else:
            showerror("Błąd", "Okno jest już otwarte")

    def openFilter(self):
        if not self.filter_opened:
            self.filter_opened = True
            if not self.subject_filter:
                self.subject_filter = Filter()
            FilterWindow(self.master, self.subject_filter, onClose=self.changeWindowStatus,
                         onFilterSet=self.onFilterSet)
        else:
            showerror("Błąd", "Okno jest już otwarte")

    def saveConfig(self):
        if not self.save_config_opened:
            self.save_config_opened = True
            SaveConfigWindow(self.master,self.save_config_choice, onClose=self.changeWindowStatus, onConfigSave = self.onConfigSave)
        else:
            showerror("Błąd", "Okno jest już otwarte")

    def downloadAttachments(self):
        if not self.connection.check_connection():
            self.download_flag = 1
            if self.connection.reconnect(self.mail_details, self.app_state):
                self.connection.auth(self.user_credentials)
                if self.connection.protocol == "IMAP":
                    self.connection.connect_host.select(self.mailbox_details.chosen_mailbox)
            pass

        ask_log_file = False
        log_save_loc = ""

        if not self.download_flag:
            self.master.bell()
            ask_log_file = askyesno("Plik dziennika", "Czy stworzyć plik dziennika?")

        if ask_log_file:
            self.master.bell()
            log_save_loc = asksaveasfilename(defaultextension=".txt",
                                             filetypes=(("Text files", "*.txt"),),
                                             title="Zapisz plik dziennika")

        temp_window = TempWindow(self.master, "Pobieranie", "Pobieranie wiadomości...\nProszę czekać.")

        try:
            if self.connection.protocol == "IMAP":
                self.connection.connect_host.select(self.mailbox_details.chosen_mailbox)
            if (self.connection.connect_host
                    and self.connection.protocol == "IMAP"
                    and str(self.connection.connect_host.state).lower() != "selected"):
                showerror("Pobieranie", "Wybrano nieprawidłową skrzynkę pocztową")
                return False
            mail_data = MailData(self.connection, self.user_file, self.date, self.file_save_path)
            download = Download(self.connection, mail_data, self.user_file.users_class_list, self.subject_filter,
                                ask_log_file)
            download.getMailData()
            temp_window.closeWindow()
            del temp_window

            if ask_log_file:
                download.save_log(log_save_loc)
            showinfo("Gotowe", "Pobieranie zakończone")
            self.download_flag = 0
            del mail_data
            del download

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

            temp_window.closeWindow()
            del temp_window

            err_msg = str(e).lower()

            connected = self.connection.manageConnectionLoss(err_msg,
                                                             self.master,
                                                             self.app_state)
            if connected:
                retry = askretrycancel("Wznowienie", "Sesja odświeżona. Czy spróbować pobrać ponownie?")
                if retry:
                    self.download_flag = 0
                    self.downloadAttachments()
                return True
            return False

        except Exception as e:
            showerror("Błąd", f"{type(e)}______{e}_______{e.__class__.__name__}")

    def refreshUi(self):
        if self.app_state.state["mail_connected"]:
            self.login_button.config(state=tk.NORMAL)
            self.mail_connection_button.config(text="Rozłącz z pocztą")
            self.connection_text.config(
                text=f"{self.mail_details.address} | {self.mail_details.port} | {self.mail_details.protocol}")
            self.user_file_text.config(text=f"{self.user_file.user_file_location}")
        else:
            self.login_button.config(state=tk.DISABLED)
            self.mail_connection_button.config(text="Połącz z pocztą")

        if self.app_state.state["logged_in"]:
            self.login_button.config(text="Wyloguj z poczty")
            self.login_text.config(text=self.user_credentials.username)
            if self.connection.protocol == "IMAP":
                self.mailbox_button.config(state=tk.NORMAL)
            elif self.connection.protocol == "POP3":
                self.mailbox_button.config(state=tk.DISABLED)
                self.mailbox_text.config(text="INBOX")
        else:
            self.login_button.config(text="Zaloguj do poczty")
            self.mailbox_button.config(state=tk.DISABLED)

        if self.app_state.state["mailbox_set"]:
            if self.mail_details.protocol == "POP3":
                self.mailbox_text.config(text="INBOX")
            else:
                self.mailbox_text.config(text=f"{self.mailbox_details.chosen_mailbox}")

        if self.app_state.state["date_set"]:
            date_text = ""
            if len(self.date.date_list) == 1:
                match self.date.date_range:
                    case "from":
                        date_text += "Od: "
                    case "to":
                        date_text += "Do: "
                    case "one_day":
                        date_text += "Z dnia: "
                date_text += self.date.date_list[0]
            else:
                date_text = f"Od: {self.date.date_list[0]} \nDo: {self.date.date_list[1]}"
            self.date_text.config(text=date_text)

        if self.app_state.state["save_method_set"]:
            self.save_path_text.config(
                text=str(f"{self.file_save_path.save_method}\n{self.file_save_path.example_save_text}"))
        else:
            self.save_path_text.config(text="")

        if self.app_state.checkAppStatus():
            self.download_button.config(state=tk.NORMAL)
        else:
            self.download_button.config(state=tk.DISABLED)

        self.master.geometry("")

    def onConnectionSuccess(self, mail_details):
        self.app_state.state["mail_connected"] = True
        self.mail_details = mail_details
        if self.mail_details.protocol == "POP3":
            self.mailbox_details.chosen_mailbox = "INBOX"
            self.app_state.state["mailbox_set"] = True
        if self.user_credentials.username and self.user_credentials.password:
            if self.connection.auth(self.user_credentials):
                self.onLoginSuccess(self.connection.connect_host,self.user_credentials)
        self.refreshUi()

    def onLoginSuccess(self, connect_host, user_credentials):
        self.app_state.state["logged_in"] = True
        self.connection.connect_host = connect_host
        self.user_credentials = user_credentials

        self.refreshUi()

    def onMailboxSelectionSuccess(self, mailbox):
        if mailbox.strip() != "":
            # self.connection.connect_host.select(mailbox)
            self.app_state.state["mailbox_set"] = True
        else:
            self.app_state.state["mailbox_set"] = False
        self.mailbox_details.chosen_mailbox = mailbox
        self.connection.mailbox_details = self.mailbox_details
        self.refreshUi()

    def onDateSetSuccess(self):
        self.app_state.state["date_set"] = True
        self.refreshUi()

    def onPathSetSuccess(self):
        self.app_state.state["save_method_set"] = True if self.file_save_path.save_method.strip() != "" else False
        self.refreshUi()

    def onFilterSet(self):
        self.filter_text.config(text=self.subject_filter.filter_text if self.subject_filter else "")

    def onConfigSave(self, checkbutton_vars):
        self.save_config_choice = checkbutton_vars
        active_keys = [key for key, var in checkbutton_vars.items() if var.get()]

        if not active_keys:
            showwarning("Ostrzeżenie", "Nie wybrano żadnych opcji do zapisu.")
            return

        config_save_location = asksaveasfilename(defaultextension=".json", filetypes=(("Json File", "*.json"),))
        if config_save_location:
            self.config.save_selected_config(active_keys, self, config_save_location)
            self.save_config_text.config(text=config_save_location)
