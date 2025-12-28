import datetime
import imaplib
import os
import socket
import time
from doctest import master

from email.message import EmailMessage
from email import policy
from email.parser import BytesParser

import poplib
from email.utils import parsedate_to_datetime
from poplib import error_proto
from tkinter.constants import DISABLED
from tkinter.messagebox import askyesno, askyesnocancel, showwarning, showerror, showinfo

import pandas as pd
import json
import datetime as dt
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from tkcalendar import Calendar
# =========================
# APLIKACJA
# =========================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Aplikacja pocztowa")
        self.app_state = AppState()
        self.connection = Connection()
        self.mail_details = MailDetails()
        self.config = Config()
        self.user_file = UserFile()
        self.time = Time()

        self.main_window = MainWindow(
            self.root,
            self.app_state,
            self.mail_details,
            self.connection,
            self.config,
            self.user_file,
            self.time
        )

    def run(self):
        self.root.mainloop()

# =========================
# STAN APLIKACJI
# =========================
class AppState:
    def __init__(self):
        self.mail_connected = False
        self.logged_in = False

# =========================
# LOGIKA
# =========================
class Config:
    def __init__(self):
        self.address = ""
        self.port = 0
        self.mailbox = ""
        self.user_file_location = ""
        self.protocol = ""
        self.save_template = ""

    def saveParameters(self,
                       mail_info: 'MailDetails',
                       user_file:'UserFile',
                       mailbox:'MailboxDetails'):

        self.address = mail_info.address
        self.port = mail_info.port
        self.protocol = mail_info.protocol
        if self.protocol == "IMAP":
            self.mailbox = mailbox.mailbox_name
        self.user_file_location = user_file.user_file_location

    def readConfigFile(self, config_file_location):
        with open(config_file_location) as file:
            conf = json.load(file)
        for key, value in conf.items():
            if hasattr(self,key): setattr(self,key,value)

    def setConfig(self, config_file_loc):
        self.readConfigFile(config_file_loc)

    def loadConfig(self, mail_details, connection, user_file):
        mail_details.setFromConfig(self)
        user_file.setFromConfig(self)
        if connection.connect(mail_details):
            return True
        return False

class Connection:
    def __init__(self):
        self.connect_host = None
        self.protocol = ""
        self.username = ""
    def connect(self, mail_details):
            try:
                if mail_details.protocol == "IMAP":
                    self.connect_host = imaplib.IMAP4_SSL(
                        mail_details.address,
                        mail_details.port)
                    self.protocol = "IMAP"
                    return True
                elif mail_details.protocol == "POP3":
                    self.connect_host = poplib.POP3_SSL(
                        mail_details.address,
                        mail_details.port)
                    self.protocol = "POP3"
                    return True
                return False
            except socket.gaierror:
                showerror("Błąd","Błąd połączenia")
                return False
            except TimeoutError:
                showerror("Błąd","Przekroczono limit czasu połączenia. Otrzymano błędny port lub usługa jest chwilowo niedostępna")
                return False
            except OSError:
                showerror("Błąd","Błąd połączenia")
                return False
            except Exception as e:
                showerror("Błąd", f"\n{e}")
                exit()

    def auth(self, user_credentials):
        protocol = self.protocol
        try:
            if protocol == "IMAP":
                self.connect_host.login(user_credentials.username, user_credentials.password)
                self.username = user_credentials.username
                return True
            elif protocol == "POP3":
                self.connect_host.user(user_credentials.username)
                self.connect_host.pass_(user_credentials.password)
                self.username = user_credentials.username
                return True
            return False
        # except imaplib.IMAP4.error:
        #     return False
        # except error_proto:
        #     return False
        except Exception as e:
            showerror("Błąd",f"\n{e.__class__.__name__}")

class MailDetails:
    def __init__(self, address="", port=None, protocol=""):
        self.address = address
        self.port = port
        self.protocol = protocol

    def checkDetails(self):
        if self.checkAddress(self.address) and self.checkPort(self.port):
            print(self.address, self.port, self.protocol)
            return True
        return False

    def checkAddress(self,address):
        if len(str(address).strip()) == 0:
            showerror("Błąd","Adres nie może być pusty")
            return False
        return True

    def checkPort(self,port):
        if not port:
            showerror("Błąd","Pole Port nie może być puste")
            return False
        # elif port == 995 and self.protocol == "IMAP":
        #     self.port = 993
        # elif port == 993 and self.protocol == "POP3":
        #     self.port = 995
        elif not port.isdigit():
            showerror("Błąd","Port musi mieć wartość numeryczną")
            return False
        elif not (1 <= int(port) <= 65535):
            showerror("Błąd","Port musi być w zakresie 1–65535")
            return False
        else:
            self.port = int(port)
        return True

    def setFromConfig(self, config:Config):
        self.address = config.address
        self.port = config.port
        self.protocol = config.protocol


class MailboxDetails:
    def __init__(self):
        self.mailbox_name = ""
        self.mailbox_list = []

class MailData:
    def __init__(self):
        self.data = ""

class User:
    username: str
    year: str
    group: int

    def __init__(self,
                 username = None,
                 year = None,
                 group = None):

        self.username = username
        self.year = year
        self.group = group

    def getImapAttachments(self, connect_host, message_id_list, save_path):
        for message in message_id_list:
            status, message_data = connect_host.fetch(message,"(RFC822)")
            message_content: EmailMessage = BytesParser(policy=policy.default).parsebytes(message_data[0][1])
            self.getAttachment(message_content,save_path)
            # for attachment in message_content.iter_attachments():
            #     filename = attachment.get_filename()
            #     payload = attachment.get_payload(decode=True)
            #     print(f"Znaleziono: {filename}")
            #     self.saveAttachments(payload, filename, save_path)

    def getAttachment(self, message,save_path):
        for attachment in message.iter_attachments():
            filename = attachment.get_filename()
            payload = attachment.get_payload(decode=True)
            print(f"Znaleziono: {filename}")
            self.saveAttachments(payload, filename, save_path)

    def saveAttachments(self, payload,filename,save_path):
        full_save_path = f"{save_path}/{self.username}"
        os.makedirs(full_save_path, exist_ok=True)
        try:
            if os.path.exists(os.path.join(full_save_path, filename)):
                print(f"Plik {filename} użytkownika {self.username} już istnieje.")
            else:
                with open(f"{full_save_path}/{filename}","wb") as f:
                    f.write(payload)
            print(f"{full_save_path}")

        except Exception as e:
            print(f"Błąd zapisu pliku. {e}")

class UserFile:
    def __init__(self):
        self.user_file_location = ""
        self.users_list = []
        self.users_class_list = []

    def setFromConfig(self, config:Config):
        self.user_file_location = config.user_file_location

    def getUsers(self,user_file_location):
        if self.setUserFile(user_file_location):
            if self.convertData():
                return True
            showerror("Błąd", "W pliku nie znaleziono adresów email")
            return False
        else:
            return False

    def setUserFile(self, user_file_location):
        temp_file_location = user_file_location
        if temp_file_location == "":
            showwarning("Ostrzeżenie", "Nie wybrano pliku z użytkownikami")
            return False
        else:
            self.user_file_location = user_file_location
            return True

    def convertData(self):
        try:
            users = pd.read_excel(self.user_file_location)

            #axis 0 = rows
            #axis 1 = columns

            users = users.dropna(axis=0,how="all")

            users = users.dropna(axis=1,how="all")

            users = users.reset_index(drop=True)

            if "@" not in str(users.iloc[0]).lower():
                users.columns = users.iloc[0]
                users = users[1:].reset_index(drop=True)

            column_name = self.findEmailColumn(users)
            if column_name[0]:
                column_name = column_name[1]
            else:
                return False

            self.users_list = users[column_name].unique().tolist()
            self.convertUsers()
            return True

        except Exception as e:
            print(e)

    def convertUsers(self):
        i = 0
        for user in self.users_list:
            user = str(user).strip()
            if not self.validateUsername(user):
                continue
            self.users_class_list.append(User(user))
            print(self.users_class_list[i].username)
            i += 1

    def validateUsername(self, username):
        if username == "":
            return False
        return True

    def findEmailColumn(self, data: pd.DataFrame):
        for column_name in data.columns:
            for item in data[column_name].head(1):
                if "@stud.prz.edu.pl" in item:
                    return [True, column_name]
        return [False]

class Time:
    def __init__(self):
        self.time_range =""
        self.date_list = []

    def setDate(self, time_range, date_list):
        self.time_range = time_range
        if self.checkDateList(date_list):
            return True
        else:
            showerror("Błąd", "Podane daty są nieprawidłowe")
            return False

    def checkDateList(self, date_list):
        return True

class UserCredentials:
    def __init__(self, username = "", password = ""):
        self.username = username
        self.password = password

    def checkCredentials(self):
        if self.validateUsername(self.username) and self.validatePassword(self.password):
            print(self.username, self.password)
            return True
        return False

    def validateUsername(self, username):
        if not username:
            showerror("Błąd", "Nazwa użytkownika nie może być pusta")
            return False
        else:
            return True

    def validatePassword(self, password):
        if not password:
            showerror("Błąd", "Hasło nie może być puste")
            return False
        else:
            return True

# =========================
# OKNA
# =========================

class MainWindow:
    def __init__(self,
                 master,
                 app_state,
                 mail_details,
                 connection,
                 config,
                 user_file,
                 time
                 ):

        self.master = master
        self.connection:Connection = connection
        self.mail_details:MailDetails = mail_details
        self.app_state:AppState = app_state
        self.config:Config = config
        self.user_file:UserFile = user_file
        self.time:Time = time
        self.file_save_location = ""
        self.build()
        self.placeWidgets()

    def build(self):
       
        self.load_config_button = ttk.Button(self.master, text="Wczytaj konfigurację", command=self.openLoadConfig)
        self.mail_connection_button = ttk.Button(self.master, text="Połącz z pocztą", command=self.openMailConnection)
        self.login_button = ttk.Button(self.master, text="Zaloguj do poczty", command=self.openLogin, state=tk.DISABLED)
        self.user_file_button = ttk.Button(self.master, text="Wczytaj plik z użytkownikami", command=self.getUserFileLocation)
        self.file_save_location_button = ttk.Button(self.master, text="Wybierz lokalizację zapisu", command=self.getFileSaveLocation)
        self.set_date_button = ttk.Button(self.master, text="Wybierz zakres czasu", command=self.openTimeSettings)
        self.set_directory_path = ttk.Button(self.master, text="Wybierz sposób zapisu", command=self.openDirectoryPath)

        self.config_label = ttk.Label(self.master, text="Konfiguracja: ")
        self.connection_label = ttk.Label(self.master, text="Poczta: ")
        self.login_label = ttk.Label(self.master, text="Użytkownik: ")
        self.user_file_label = ttk.Label(self.master, text="Plik z użytkownikami: ")
        self.file_save_label = ttk.Label(self.master, text="Lokalizacja zapisu: ")
        self.date_label = ttk.Label(self.master, text="Zakres czasu: ")
        self.directory_label = ttk.Label(self.master, text="Sposób zapisu: ")

        self.config_text = ttk.Label(self.master)
        self.connection_text = ttk.Label(self.master)
        self.login_text = ttk.Label(self.master)
        self.user_file_text = ttk.Label(self.master)
        self.file_save_text = ttk.Label(self.master)
        self.date_text = ttk.Label(self.master)
        self.directory_text = ttk.Label(self.master)

    def placeWidgets(self):
        self.master.geometry("380x300")

        buttons = [
            self.load_config_button,
            self.mail_connection_button,
            self.login_button,
            self.user_file_button,
            self.file_save_location_button,
            self.set_date_button,
            self.set_directory_path
        ]

        labels = [
            self.config_label,
            self.connection_label,
            self.login_label,
            self.user_file_label,
            self.file_save_label,
            self.date_label,
            self.directory_label
        ]

        texts = [
            self.config_text,
            self.connection_text,
            self.login_text,
            self.user_file_text,
            self.file_save_text,
            self.date_text,
            self.directory_text
        ]

        for i, button in enumerate(buttons):
            button.grid(row=i, column=0, padx=5, pady=7, sticky=tk.W)
            button.config(width=30)
        self.load_config_button.grid(pady = (15,7))
        for i, label in enumerate(labels):
            label.grid(row=i, column=1, padx=5, pady=7, sticky=tk.W)
        self.config_label.grid(pady = (15,7))

        for i, text in enumerate(texts):
            text.grid(row=i, column=2, padx=5, pady=7, sticky=tk.W)
        self.config_text.grid(pady = (15,7))

    def openLoadConfig(self):
        config_file_loc = askopenfilename(title="Wybierz plik z zapisaną konfiguracją",
                                          filetypes=(("Json File", "*.json"),))
        try:
            if config_file_loc != "":
                self.config.setConfig(config_file_loc)
                if self.config.loadConfig(self.mail_details, self.connection, self.user_file):
                    showinfo("Połączenie",f"Połączono:\nAdres: {self.mail_details.address}\nPort: {self.mail_details.port}\nProtokół: {self.mail_details.protocol}")
                    self.config_text.config(text=config_file_loc)
                    self.app_state.mail_connected = True
                    self.refreshUi()
                    return True
                else:
                    showerror("Błąd",f"Plik konfiguracyjny zawiera błąd")
            showwarning("Ostrzeżenie",f"Nie wybrano pliku konfiguracyjnego")
            return False
        except Exception as e:
            print(e)

    def openMailConnection(self):
        try:
            MailConnectionWindow(self.master, self.connection, on_connection_success=self.onConnectionSuccess)
        except ValueError:
            return

    def onConnectionSuccess(self, mail_details):
        self.app_state.mail_connected = True
        self.mail_details = mail_details
        self.refreshUi()

    def openLogin(self):
        LoginWindow(self.master, self.connection, on_login_success= self.onLoginSuccess)

    def onLoginSuccess(self, connect_host):
        self.app_state.logged_in = True
        self.connection.connect_host = connect_host
        self.refreshUi()

    def refreshUi(self):
        if self.app_state.mail_connected:
            self.login_button.config(state=tk.NORMAL)
            self.mail_connection_button.config(state=tk.DISABLED)
            self.connection_text.config(text=f"{self.mail_details.address} | {self.mail_details.port} | {self.mail_details.protocol}")
            self.user_file_text.config(text = f"{self.user_file.user_file_location}")
        else:
            self.login_button.config(state=tk.DISABLED)

        if self.app_state.logged_in:
            self.login_button.config(state=DISABLED)
            self.login_text.config(text=self.connection.username)

    def getUserFileLocation(self):
        user_file_loc = askopenfilename(title="Wybierz plik Excel z użytkownikami",
                                        filetypes=[("Excel files", "*.xlsx *.xls")])
        self.user_file.getUsers(user_file_loc)

    def getFileSaveLocation(self):
        save_loc = askdirectory(title="Wybierz folder do zapisu załączników")
        if save_loc == "":
            showwarning("Ostrzeżenie", "Nie wybrano lokalizacji do zapisu plików")
        else:
            self.file_save_location = save_loc
            self.file_save_text.config(text=f"{save_loc}/")

    def openTimeSettings(self):
        TimeWindow(self.master, self.time)
        return

    def openDirectoryPath(self):
        DirectoryPath(self.master)
        return
    
# =========================
# OKNO LOGOWANIA
# =========================
class MailConnectionWindow:
    def __init__(self, master, connection, on_connection_success):
        self.window = tk.Toplevel(master)
        self.window.title("Logowanie")
        self.window.grab_set()
        self.connection = connection
        self.on_connection_success = on_connection_success
        self.address = tk.StringVar(value="")
        self.port = tk.StringVar()
        self.protocol = tk.StringVar(value="IMAP")
        self.setDefaultPort()
        self.connection_status = tk.StringVar(value="")
        self.build()
        self.placeWidgets()

    def build(self):
        self.imap_radio = ttk.Radiobutton(self.window, text = "IMAP", variable=self.protocol, value="IMAP", command=self.setDefaultPort)
        self.pop_radio = ttk.Radiobutton(self.window, text = "POP3", variable=self.protocol, value="POP3", command=self.setDefaultPort)

        self.address_label = ttk.Label(self.window, text="Adres poczty: ")
        self.address_input = ttk.Entry(self.window, textvariable=self.address)

        self.port_label = ttk.Label(self.window, text="Port: ")
        self.port_input = ttk.Entry(self.window, textvariable=self.port)
        self.connect_button = ttk.Button(self.window, text="Połącz", command=self.submit)
        self.status_label = ttk.Label(self.window,textvariable=self.connection_status)

    def placeWidgets(self):
        self.window.geometry("250x200")

        self.imap_radio.grid(row=0, column=0, padx=5, pady=5)
        self.pop_radio.grid(row=0, column=1, padx=5, pady=5)

        self.address_label.grid(row=1, column=0, padx=5, pady=5)
        self.address_input.grid(row=1, column=1, padx=5, pady=5)

        self.port_label.grid(row=2, column=0, padx=5, pady=5)
        self.port_input.grid(row=2, column=1, padx=5, pady=5)

        self.connect_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

    def setDefaultPort(self):
        protocol = self.protocol.get()
        if protocol == "IMAP":
            self.port.set("993")
        elif protocol == "POP3":
            self.port.set("995")

    def submit(self):
        self.connection_status.set("Łączenie...")
        self.window.update_idletasks()
        mail_details = MailDetails(
            address=self.address.get(),
            port=self.port.get(),
            protocol=self.protocol.get()
        )
        if mail_details.checkDetails():
            if self.connection.connect(mail_details):
                self.window.destroy()
                showinfo("Połączenie", f"Połączono:\nAdres: {self.address.get()}\nPort: {self.port.get()}\nProtokół: {self.protocol.get()}")
                self.on_connection_success(mail_details)
        self.connection_status.set("")
        self.window.update_idletasks()


class LoginWindow:
    def __init__(self, master, connection, on_login_success):
        self.window = tk.Toplevel(master)
        self.window.title("Logowanie")
        self.window.grab_set()
        self.on_login_success = on_login_success
        self.connection:Connection = connection
        self.protocol = self.connection.protocol
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.login_status = tk.StringVar(value="")
        self.build()
        self.placeWidgets()

    def build(self):
        self.entry_username = ttk.Entry(self.window, textvariable=self.username)
        self.entry_password = ttk.Entry(self.window, textvariable=self.password ,show="*")
        self.btn_login = ttk.Button(self.window, text="Zaloguj", command=self.submit)
        self.status_label = ttk.Label(self.window,textvariable=self.login_status)

    def placeWidgets(self):
        self.window.geometry("200x180")

        ttk.Label(self.window, text="Login").grid(row=0, column=0, padx=5, pady=5)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.window, text="Hasło").grid(row=1, column=0, padx=5, pady=5)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        self.btn_login.grid(row=3, column=0, columnspan=2, pady=5)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

    def submit(self):
        user_credentials = UserCredentials(username = self.username.get(),
                                           password = self.password.get())
        self.login_status.set("Logowanie...")
        self.window.update_idletasks()
        if user_credentials.checkCredentials():
            if self.connection.auth(user_credentials):
                self.window.destroy()
                showinfo("Logowanie", f"Zalogowano:\nUżytkownik: {user_credentials.username}")
                self.on_login_success(self.connection.connect_host)
            else:
                showerror("Błąd", "Nieprawidłowe dane logowania")
        self.login_status.set("")
        self.window.update_idletasks()

class TimeWindow:
    def __init__(self, master, time):
        self.window = tk.Toplevel(master)
        self.window.title("Zakres czasu")
        self.window.grab_set()
        self.time:Time = time
        self.timestamp = tk.StringVar(value="one_day")
        self.build()
        self.placeWidgets()
        self.calendar_one_date.bind("<<CalendarSelected>>", self.updateDate)
        self.calendar_from.bind("<<CalendarSelected>>", self.updateDateFrom)
        self.calendar_to.bind("<<CalendarSelected>>", self.updateDateTo)
        self.updateWindow()

    def build(self):
        self.radio_frame = ttk.Frame(self.window)
        self.one_day = ttk.Radiobutton(self.radio_frame, text = "Jeden dzień", variable=self.timestamp, value="one_day", command=self.updateWindow)
        self.from_to = ttk.Radiobutton(self.radio_frame, text = "Od...Do", variable=self.timestamp, value="from_to", command=self.updateWindow)
        self.only_from = ttk.Radiobutton(self.radio_frame, text = "Tylko od...", variable=self.timestamp, value="from", command=self.updateWindow)
        self.only_to = ttk.Radiobutton(self.radio_frame, text = "Tylko do...", variable=self.timestamp, value="to", command=self.updateWindow)

        self.content_frame = ttk.Frame(self.window)
        self.calendar_one_date = Calendar(self.content_frame,
                                 selectmode = "day",
                                 locale="pl",
                                 year = datetime.datetime.now().year,
                                 month = datetime.datetime.now().month,
                                 day = datetime.datetime.now().day,
                                 date_pattern="dd-mm-yyyy")

        self.calendar_from = Calendar(self.content_frame,
                                 selectmode = "day",
                                 locale="pl",
                                 year = datetime.datetime.now().year,
                                 month = datetime.datetime.now().month,
                                 day = datetime.datetime.now().day,
                                 date_pattern="dd-mm-yyyy")

        self.calendar_to = Calendar(self.content_frame,
                                 selectmode = 'day',
                                 locale="pl",
                                 year = datetime.datetime.now().year,
                                 month = datetime.datetime.now().month,
                                 day = datetime.datetime.now().day,
                                 date_pattern="dd-mm-yyyy")

        self.one_date_label = ttk.Label(self.content_frame,text=self.calendar_from.get_date())
        self.date_from_label = ttk.Label(self.content_frame,text=self.calendar_from.get_date())
        self.date_to_label = ttk.Label(self.content_frame,text=self.calendar_to.get_date())

        self.save_time_button = ttk.Button(self.content_frame, text="Zapisz", command=self.save)

    def placeWidgets(self):
        self.window.minsize(560,300)

        self.window.columnconfigure(0, weight=1)

        self.radio_frame.grid(row=0, column=0, sticky='nswe')
        self.content_frame.grid(row=1, column=0, sticky='nswe')

        self.radio_frame.columnconfigure(0, weight=1)
        self.radio_frame.columnconfigure(1, weight=1)
        self.radio_frame.columnconfigure(2, weight=1)
        self.radio_frame.columnconfigure(3, weight=1)
        self.radio_frame.rowconfigure(0, weight=1)

        self.one_day.grid(row=0, column=0, padx=5, pady=5)
        self.from_to.grid(row=0, column=1, padx=5, pady=5)
        self.only_from.grid(row=0, column=2, padx=5, pady=5)
        self.only_to.grid(row=0, column=3, padx=5, pady=5)

        self.calendar_one_date.grid(row=1,column=0,padx=(15,5),pady=(15,5))

        self.calendar_from.grid(row=1,column=0,padx=(15,5),pady=(15,5))
        self.calendar_to.grid(row=1,column=1,padx=(20,15),pady=(15,5))

        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)

        self.one_date_label.grid(row=2, column=0)
        self.date_from_label.grid(row=2, column=0)
        self.date_to_label.grid(row=2, column=1)

        self.save_time_button.grid(row=4,column=0, columnspan=2, pady=(10,0))

    def updateDateFrom(self, event = None):
        self.date_from_label.config(text=self.calendar_from.get_date())

    def updateDateTo(self, event = None):
        self.date_to_label.config(text=self.calendar_to.get_date())

    def updateDate(self, event = None):
        self.one_date_label.config(text=self.calendar_one_date.get_date())


    def updateWindow(self):
        timestamp = self.timestamp.get()
        if timestamp != "from_to":
            self.content_frame.columnconfigure(1, weight=0)

            self.calendar_from.grid_remove()
            self.date_from_label.grid_remove()

            self.calendar_to.grid_remove()
            self.date_to_label.grid_remove()

            self.calendar_one_date.grid()
            self.one_date_label.grid()

        else:
            self.content_frame.columnconfigure(1, weight=1)

            self.calendar_from.grid()
            self.date_from_label.grid()

            self.calendar_to.grid()
            self.date_to_label.grid()

            self.calendar_one_date.grid_remove()
            self.one_date_label.grid_remove()

    def save(self):
        time_range = self.timestamp.get()
        date_list = []
        if time_range != "from_to":
            date_list.append(self.calendar_one_date.get_date())
            self.time.setDate(time_range, date_list)
        else:
            date_list.append(self.calendar_from.get_date())
            date_list.append(self.calendar_to.get_date())
            self.time.setDate(time_range, date_list)

class DirectoryPath:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Ścieżka zapisu")
        self.window.grab_set()
        self.build()
        self.placeWidgets()

    def build(self):
        self.save_time = ttk.Button(self.window, text="Zapisz", command=self.save)

    def placeWidgets(self):
        self.window.geometry("200x180")

    def save(self):
        return

# =========================
# START
# =========================
if __name__ == "__main__":
    app = App()
    app.run()
