import datetime
import imaplib
import os
import socket

import re

from email.message import EmailMessage
from email import policy
from email.parser import BytesParser

import poplib
from email.utils import parsedate_to_datetime
from multiprocessing.spawn import import_main_path

import patoolib

from tkinter.messagebox import showwarning, showerror, showinfo

import pandas as pd
import json
import datetime as dt
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory

from openpyxl.packaging.extended import VectorLpstr
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
            "mail_connected" : False,
            "logged_in" : False,
            "mailbox_set" : False,
            "user_file_set" : False,
            "save_loc_set" : False,
            "date_set" : False,
            "save_method_set" : False
        }

    def checkAppStatus(self):
        return all(self.state.values())

# =========================
# LOGIKA
# =========================
class Config:
    def __init__(self):
        self.address = ""
        self.protocol = ""
        self.port = 0
        self.chosen_mailbox = ""
        self.save_method = ""
        # self.user_file_location = ""

    def saveParameters(self,config_params,config_save_location):
        with open(config_save_location, 'w') as file:
            json.dump(config_params, file,indent=4)
            showinfo("Informacja",f"Konfiguracja zapisana w:\n"
                                  f"{config_save_location}")

    def readConfigFile(self, config_file_location):
        with open(config_file_location) as file:
            conf = json.load(file)
        for key, value in conf.items():
            if hasattr(self,key): setattr(self,key,value)

    def loadConfig(self, mail_details,mailbox_details,file_save_path, connection):
        mail_details.setFromConfig(self.address,self.protocol,self.port)
        mailbox_details.setFromConfig(self.chosen_mailbox)
        file_save_path.setFromConfig(self.save_method)

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

    def disconnect(self):
        try:
            if self.protocol == "IMAP" and self.connect_host:
                self.connect_host.logout()
            elif self.protocol == "POP3" and self.connect_host:
                self.connect_host.quit()
        except Exception:
            pass
        finally:
            self.connect_host = None
            self.protocol = ""
            self.username = ""

    def auth(self, user_credentials):
        protocol = self.protocol
        if protocol == "IMAP":
            self.connect_host.login(user_credentials.username, user_credentials.password)
            self.username = user_credentials.username
            return True
        elif protocol == "POP3":
            self.connect_host.user(user_credentials.username)
            self.connect_host.pass_(user_credentials.password)
            self.username = user_credentials.username
            return True
        raise ValueError
        # except imaplib.IMAP4.error:
        #     return False
        # except error_proto:
        #     return False


class MailDetails:
    def __init__(self, address="", port=None, protocol=""):
        self.address = address.lower()
        self.port = port
        self.protocol = protocol

    def checkDetails(self):
        if self.checkAddress(self.address) and self.checkPort(self.port):
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

    def setFromConfig(self, address,protocol,port):
        self.address = address
        self.protocol = protocol
        self.port = port

class MailboxDetails:
    def __init__(self):
        self.mailbox_list = []
        self.chosen_mailbox = ""

    def setFromConfig(self,chosen_mailbox):
        self.chosen_mailbox = chosen_mailbox

    def getAllMailboxes(self, connection):
        if len(self.mailbox_list) != 0:
            self.mailbox_list = []
        for i in (connection.connect_host.list()[1]):
            if not b"doveco" in i:
                self.mailbox_list.append(str(i).split(".")[1][2:-1])
        return self.mailbox_list

class MailData:
    def __init__(self,connection, user_file, date, file_save_path):
        self.connection:Connection = connection
        self.users_list = user_file.users_class_list
        self.date_choice = date.date_range
        self.date_list = date.parseDate(date.date_list)
        self.query = []
        self.file_save_path:FileSavePath = file_save_path

    # ---------------------------------------------------------
    # Tworzenie zapytania dla wybranej daty
    # ---------------------------------------------------------
    def makeQuery(self):
        quotes = ["ON","SINCE","BEFORE"]
        index = 0

        match self.date_choice:
            case "one_day":
                self.query = [quotes[index], self.date_list[0].strftime("%d-%b-%Y")]

            case "from_to":
                self.date_list[1] = self.date_list[1] + dt.timedelta(days=1)
                for date in self.date_list:
                    self.query += [quotes[index+1], date.strftime("%d-%b-%Y")]
                    index += 1
            case "from":
                self.query += [quotes[1], self.date_list[0].strftime("%d-%b-%Y")]

            case "to":
                self.date_list[0] = self.date_list[0] + dt.timedelta(days=1)
                self.query += [quotes[2], self.date_list[0].strftime("%d-%b-%Y")]

    def getMessage(self,download):
        if self.connection.protocol=="IMAP":
            self.makeQuery()
            self.getImapMessage(download)
        else:
            username_dict = download.makeUsernameDict()
            self.getPopMessage(download, username_dict)

    def getImapMessage(self,download):
        for user in self.users_list:
            status, data = self.connection.connect_host.search(None, 'FROM', f'"{user.username}"', *self.query)
            message_id_list = data[0].split()
            download.getImapAttachments(self.connection.connect_host,
                                        message_id_list,
                                        user,
                                        self.file_save_path)

    def getPopMessage(self,download,username_dict):
        count,_ = self.connection.connect_host.stat()
        date_filter = self.dateFilter()
        for i in range(count,0,-1):
            resp = self.connection.connect_host.retr(i)
            joined = b"\r\n".join(resp[1])
            message = BytesParser(policy=policy.default).parsebytes(joined)
            try:
                user = self.checkUser(message.get("From",""),username_dict)
                if user:
                    message_date = parsedate_to_datetime(message.get("Date")).date()
                    if message_date < self.date_list[0] and self.date_choice != "to":
                        showinfo("Pobieranie", "Zakończono pobieranie plików")
                        break
                    if date_filter(message_date):
                        download.getAttachment(message, self.file_save_path, user)
            except Exception:
                continue

    def dateFilter(self):
        match self.date_choice:
            case "one_day":
                return lambda message_date: message_date == self.date_list[0]
            case "from_to":
                return lambda message_date: self.date_list[0] <= message_date <= self.date_list[1]
            case "from":
                return lambda message_date: message_date >= self.date_list[0]
            case "to":
                return lambda message_date: message_date <= self.date_list[0]

    def checkUser(self, mail_user,username_dict):
        for username in username_dict.keys():
            if mail_user in username:
                user = username_dict[mail_user]
                return user
        return None

class Download:
    def __init__(self, connection,mail_data, users_class_list):
        self.connection:Connection = connection.connect_host
        self.mail_data:MailData = mail_data
        self.users_class_list: list[User] = users_class_list

    def getMailData(self):
        self.mail_data.getMessage(self)

    def makeUsernameDict(self):
        return {user.username: user for user in self.users_class_list}

    def getImapAttachments(self,
                           connection,
                           message_id_list,
                           user:"User",
                           save_path):
        for message in message_id_list:
            status, message_data = connection.fetch(message,"(RFC822)")
            message_content: EmailMessage = BytesParser(policy=policy.default).parsebytes(message_data[0][1])
            self.getAttachment(message_content,save_path, user)

    def getAttachment(self, message,file_save_path:"FileSavePath", user):
        file_save_path.addUserInfo(user.user_info)
        full_save_path = file_save_path.full_save_path
        os.makedirs(full_save_path, exist_ok=True)
        for attachment in message.iter_attachments():
            filename = attachment.get_filename()
            payload = attachment.get_payload(decode=True)
            print(f"Znaleziono: {filename}")
            self.saveAttachments(payload, filename, full_save_path, user)

    def saveAttachments(self, payload,filename,full_save_path, user):
        file_path = os.path.join(full_save_path,filename)
        try:
            if os.path.exists(file_path):
                print(f"Plik {filename} użytkownika {user.username} już istnieje.")
            else:
                with open(f"{file_path}","wb") as f:
                    f.write(payload)
            if patoolib.is_archive(str(file_path)):
                extract_dir = (full_save_path+
                            filename.split(".")[0]+
                            "_EXTRACTED_"+
                            str(datetime.datetime.today().strftime('%d_%m-%Y')))
                os.makedirs(extract_dir,
                            exist_ok=True)
                patoolib.extract_archive(archive=str(file_path),outdir=extract_dir)
        except Exception as e:
            print(f"Błąd zapisu pliku. {e}")

class FileSavePath:
    def __init__(self):
        self.save_location = ""
        self.save_method = ""
        self.save_method_for_user = ""
        self.full_save_path = ""
        self.example_save_text = ""
        self.example_user = User("jankowalski@email.pl",
                                 "Jan",
                                 "Kowalski",
                                 "2",
                                 "EF-ZI",
                                 "1",
                                 "123456")

    def setFromConfig(self, save_method):
        self.save_method = save_method
        self.example_save_text = save_method
        for word in self.example_user.user_info.keys():
            self.example_save_text = re.sub(
                f"{{{word.capitalize()}}}",
                self.example_user.user_info[word],
                self.example_save_text,
                flags=re.IGNORECASE
            )

    def makeSavePath(self):
        self.full_save_path = self.save_location + "/" + self.save_method_for_user + "/"

    def addUserInfo(self, user_info):
        self.save_method_for_user = self.save_method
        for key in user_info.keys():
            if key in self.save_method.lower():
                self.save_method_for_user = re.sub(
                    f"{{{key.capitalize()}}}",
                    str(user_info[key]),
                    self.save_method_for_user,
                    flags=re.IGNORECASE
                )
        self.makeSavePath()

class User:
    username: str
    first_name: str
    surname: str
    year: str
    specialization: str
    group: str
    index: str

    def __init__(self,
                 username = None,
                 first_name = None,
                 surname = None,
                 year = None,
                 specialization = None,
                 group = None,
                 index = None):

        self.username = username
        self.user_info = {
            "imie" : first_name,
            "nazwisko" : surname,
            "rok" : year,
            "grupa" : group,
            "specjalizacja" : specialization,
            "indeks" : index
        }

class UserFile:
    def __init__(self):
        self.user_file_location = ""
        self.users_list = []
        self.users_class_list: list[User] = []

    # def setFromConfig(self, config:Config):
    #     self.user_file_location = config.user_file_location

    def getUsers(self,user_file_location):
        if self.setUserFile(user_file_location):
            if self.convertData():
                return True
            showerror("Błąd", "W pliku nie znaleziono adresów email \n"
                              "lub \nadresy email nie są z domeny @stud.prz.edu.pl")
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
            duplicated_users = self.findDuplicates(users, column_name)
            duplicated_users_list = ""
            for key,value in duplicated_users.items():
                duplicated_users_list += f"Wiersz: {str(key)}, Adres: {str(value)}\n"
            if len(duplicated_users_list) != 0:
                showwarning("Ostrzeżenie",f"W pliku znajdują się zduplikowane adresy email:\n{duplicated_users_list}")

            users.columns = users.columns.str.lower()
            self.users_list = list(users.to_dict("index").values())
            self.convertUsers()
            return True

        except Exception as e:
            print(e)

    def findDuplicates(self,users,column_name):
        users_list = users[column_name].tolist()
        duplicates_list = users.duplicated(subset=column_name)
        duplicated_users = {}
        for i, status in enumerate(duplicates_list):
            if status:
                duplicated_users[i+1] = users_list[i]
        return duplicated_users

    def convertUsers(self):
        for user_from_file in self.users_list:
            if not self.fixValues(user_from_file):
                continue
            user_class = User(
                user_from_file['email'],
                user_from_file['imie'],
                user_from_file['nazwisko'],
                user_from_file['rok'],
                user_from_file['specjalizacja'],
                user_from_file['grupa'],
                user_from_file['indeks']
            )
            self.users_class_list.append(user_class)

    def fixValues(self,user):
        for key, value in user.items():
            user[key] = str(value).strip()
            try:
                if value != value: user[key] = ""
                if user["email"] == "": return False
                user[key] = int(float(value))
            except Exception:
                continue
        return True

    def findEmailColumn(self, data: pd.DataFrame):
        for column_name in data.columns:
            for item in data[column_name].head(1):
                try:
                    if "@stud.prz.edu.pl" in item:
                        return [True, column_name]
                except Exception:
                    continue
        return [False]

class Date:
    #one_day
    #from_to
    #from
    #to
    def __init__(self):
        self.date_range = ""
        self.date_list = []

    def setDate(self, date_range, date_list):
        if self.checkDateList(date_range, date_list):
            self.date_list = date_list
            self.date_range = date_range
            return True
        else:
            return False

    def checkDateList(self, date_range, date_list):
        present_date = datetime.datetime.today().date()
        parsed_date_list = self.parseDate(date_list)
        if any(date > present_date for date in parsed_date_list):
            showwarning("Ostrzeżenie", "Data jest większa niż aktualna")

        match date_range:
            case "from_to":
                if parsed_date_list[0] > parsed_date_list[1]:
                    showerror("Błąd","Początkowa data jest większa niż końcowa")
                    return False

                if parsed_date_list[0] == parsed_date_list[1]:
                    showwarning("Ostrzeżenie", "Daty są takie same")

                return True

            case "one_day":
                return True

            case "from":
                if parsed_date_list[0] > present_date:
                    showerror("Błąd","Początkowa data jest większa niż końcowa")
                    return False
                return True

            case "to":
                return True

    def parseDate(self, date_list):
        return [
            datetime.datetime.strptime(date, '%d-%m-%Y').date()
            for date in date_list
        ]

class UserCredentials:
    def __init__(self, username = "", password = ""):
        self.username = username
        self.password = password
    def checkCredentials(self):
        if self.validateUsername(self.username) and self.validatePassword(self.password):
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
                 mailbox_details,
                 connection,
                 config,
                 user_file,
                 date,
                 file_save_path
                 ):

        self.master = master
        self.connection:Connection = connection
        self.mail_details:MailDetails = mail_details
        self.mailbox_details:MailboxDetails = mailbox_details
        self.app_state:AppState = app_state
        self.config:Config = config
        self.user_file:UserFile = user_file
        self.date:Date = date
        self.file_save_path:FileSavePath = file_save_path
        self.build()
        self.placeWidgets()

    def build(self):

        self.load_config_button = ttk.Button(self.master, text="Wczytaj konfigurację", command=self.openLoadConfig)
        self.mail_connection_button = ttk.Button(self.master, text="Połącz z pocztą", command=self.manageConnection)
        self.login_button = ttk.Button(self.master, text="Zaloguj do poczty", command=self.manageLogin, state=tk.DISABLED)
        self.mailbox_button = ttk.Button(self.master, text="Wybierz skrzynkę", command=self.openMailboxSelection, state=tk.DISABLED)
        self.user_file_button = ttk.Button(self.master, text="Wczytaj plik z użytkownikami", command=self.getUserFileLocation)
        self.file_save_location_button = ttk.Button(self.master, text="Wybierz lokalizację zapisu", command=self.getFileSaveLocation)
        self.set_date_button = ttk.Button(self.master, text="Wybierz zakres czasu", command=self.openDateSettings)
        self.set_save_path_button = ttk.Button(self.master, text="Wybierz sposób zapisu", command=self.openSavePath)
        self.download_button = ttk.Button(self.master, text="Pobierz załączniki", command=self.downloadAttachments, state=tk.DISABLED)
        self.save_config_button = ttk.Button(self.master, text="Zapisz konfigurację", command=self.saveConfig, state=tk.DISABLED)


        self.config_label = ttk.Label(self.master, text="Konfiguracja: ")
        self.connection_label = ttk.Label(self.master, text="Poczta: ")
        self.login_label = ttk.Label(self.master, text="Użytkownik: ")
        self.mailbox_label = ttk.Label(self.master, text="Skrzynka: ")
        self.user_file_label = ttk.Label(self.master, text="Plik z użytkownikami: ")
        self.file_save_label = ttk.Label(self.master, text="Lokalizacja zapisu: ")
        self.date_label = ttk.Label(self.master, text="Zakres czasu: ")
        self.save_path_label = ttk.Label(self.master, text="Sposób zapisu: ")
        self.save_config_label = ttk.Label(self.master, text="Zapisany plik: ")

        self.config_text = ttk.Label(self.master)
        self.connection_text = ttk.Label(self.master)
        self.login_text = ttk.Label(self.master)
        self.mailbox_text = ttk.Label(self.master)
        self.user_file_text = ttk.Label(self.master)
        self.file_save_text = ttk.Label(self.master)
        self.date_text = ttk.Label(self.master)
        self.save_path_text = ttk.Label(self.master)
        self.save_config_text = ttk.Label(self.master)

    def placeWidgets(self):
        self.master.geometry("680x410")

        buttons = [
            self.load_config_button,
            self.mail_connection_button,
            self.login_button,
            self.mailbox_button,
            self.user_file_button,
            self.file_save_location_button,
            self.set_date_button,
            self.set_save_path_button,
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
            self.save_config_label,
        ]

        texts = [
            self.config_text,
            self.connection_text,
            self.login_text,
            self.mailbox_text,
            self.user_file_text,
            self.file_save_text,
            self.date_text,
            self.save_path_text,
            self.save_config_text,
        ]

        for i, button in enumerate(buttons):
            button.grid(row=i, column=0, padx=5, pady=7, sticky=tk.W)
            button.config(width=30)
        self.load_config_button.grid(row=0,column=0,pady = (15,7))
        for i, label in enumerate(labels):
            label.grid(row=i, column=1, padx=5, pady=7, sticky=tk.W)
        self.config_label.grid(row=0,column=1,pady = (15,7))

        for i, text in enumerate(texts):
            text.grid(row=i, column=2, padx=5, pady=7, sticky=tk.W)
        self.config_text.grid(row=0,column=2,pady = (15,7))

        self.download_button.grid(row=len(buttons)+2,column=0, columnspan=2, pady=(10,0))

    def openLoadConfig(self):
        config_file_loc = askopenfilename(title="Wybierz plik z zapisaną konfiguracją",
                                          filetypes=(("Json File", "*.json"),))
        try:
            if config_file_loc != "":
                self.config.readConfigFile(config_file_loc)
                if self.config.loadConfig(self.mail_details, self.mailbox_details,self.file_save_path, self.connection):
                    showinfo("Połączenie",f"Połączono:\nAdres: {self.mail_details.address}\nPort: {self.mail_details.port}\nProtokół: {self.mail_details.protocol}")
                    self.config_text.config(text=config_file_loc)
                    self.app_state.state["mail_connected"] = True
                    self.app_state.state["mailbox_set"] = True
                    self.app_state.state["save_method_set"] = True
                    self.refreshUi()
                    return True
                else:
                    showerror("Błąd",f"Plik konfiguracyjny zawiera błąd")
            showwarning("Ostrzeżenie",f"Nie wybrano pliku konfiguracyjnego")
            return False
        except Exception as e:
            print(e)

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
            MailConnectionWindow(self.master, self.connection, onConnectionSuccess=self.onConnectionSuccess)
        except ValueError:
            return

    def disconnectMail(self, flag=0):
        self.connection.disconnect()
        self.app_state.state["mail_connected"] = False
        self.app_state.state["logged_in"] = False
        self.app_state.state["mailbox_set"] = False
        self.login_text.config(text="")
        self.mailbox_text.config(text="")
        self.mailbox_details.mailbox_list = []
        if flag==0:
            self.connection_text.config(text="")
            showinfo("Połączenie", "Rozłączono z pocztą")
            self.refreshUi()

    def logoutMail(self):
        self.disconnectMail(flag=1)
        self.connection.connect(self.mail_details)
        self.app_state.state["mail_connected"] = True
        self.connection.protocol = self.mail_details.protocol
        showinfo("Połączenie", "Wylogowano z poczty")
        self.refreshUi()

    def openLogin(self):
        LoginWindow(self.master, self.connection, onLoginSuccess= self.onLoginSuccess)

    def openMailboxSelection(self):
        MailboxSelectionWindow(self.master, self.connection, self.mailbox_details,onMailboxSelectionSuccess = self.onMailboxSelectionSuccess)

    def openSavePath(self):
        SavePathWindow(self.master, self.file_save_path, self.onPathSetSuccess)
        self.refreshUi()
        return

    def getUserFileLocation(self):
        user_file_loc = askopenfilename(title="Wybierz plik Excel z użytkownikami",
                                        filetypes=[("Excel files", "*.xlsx *.xls")])
        if self.user_file.getUsers(user_file_loc):
            self.user_file_text.config(text=user_file_loc)
            self.app_state.state["user_file_set"] = True

    def getFileSaveLocation(self):
        save_loc = askdirectory(title="Wybierz folder do zapisu załączników")
        if save_loc == "":
            showwarning("Ostrzeżenie", "Nie wybrano lokalizacji do zapisu plików")
        else:
            self.file_save_path.save_location = save_loc
            self.file_save_text.config(text=f"{save_loc}/")
            self.app_state.state["save_loc_set"] = True

    def downloadAttachments(self):
        mail_data = MailData(self.connection,self.user_file, self.date, self.file_save_path)
        download = Download(self.connection,mail_data,self.user_file.users_class_list)
        download.getMailData()
        showinfo("Pobieranie...","Pobieranie wiadomości")

    def saveConfig(self):
        config_save_location = asksaveasfilename(defaultextension=".json",
                                                filetypes=(("Json File", "*.json"),))
        if config_save_location!="":
            mailbox = self.mailbox_details.chosen_mailbox if self.mail_details.protocol == "IMAP" else "INBOX"
            config_params = {
                "address":self.mail_details.address,
                "protocol":self.mail_details.protocol,
                "port":self.mail_details.port,
                "chosen_mailbox": mailbox,
                "save_method":self.file_save_path.save_method,
            }
            self.save_config_text.config(text=config_save_location)
            self.config.saveParameters(config_params,config_save_location)
        else:
            showwarning("Ostrzeżenie", "Nie zapisano konfiguracji")

    def refreshUi(self):
        if self.app_state.state["mail_connected"]:
            self.login_button.config(state=tk.NORMAL)
            self.mail_connection_button.config(text="Rozłącz z pocztą")
            self.connection_text.config(text=f"{self.mail_details.address} | {self.mail_details.port} | {self.mail_details.protocol}")
            self.user_file_text.config(text = f"{self.user_file.user_file_location}")
        else:
            self.login_button.config(state=tk.DISABLED)
            self.mail_connection_button.config(text="Połącz z pocztą")

        if self.app_state.state["logged_in"]:
            self.login_button.config(text="Wyloguj z poczty")
            self.login_text.config(text=self.connection.username)
            if self.connection.protocol == "IMAP":
                self.mailbox_button.config(state=tk.NORMAL)
            elif self.connection.protocol == "POP3":
                self.mailbox_button.config(state=tk.DISABLED)
                self.mailbox_text.config(text="INBOX")
        else:
            self.login_button.config(text="Zaloguj do poczty")
            self.mailbox_button.config(state=tk.DISABLED)

        if self.app_state.state["mailbox_set"]:
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
            self.save_path_text.config(text = str(f"{self.file_save_path.save_method}\n{self.file_save_path.example_save_text}"))

        if self.app_state.checkAppStatus():
            self.download_button.config(state=tk.NORMAL)
            self.save_config_button.config(state=tk.NORMAL)

    def onConnectionSuccess(self, mail_details):
        self.app_state.state["mail_connected"] = True
        self.mail_details = mail_details
        self.refreshUi()

    def onLoginSuccess(self, connect_host):
        self.app_state.state["logged_in"] = True
        self.connection.connect_host = connect_host
        if self.app_state.state["mailbox_set"]:
            self.connection.connect_host.select(self.mailbox_details.chosen_mailbox)
        self.refreshUi()

    def onMailboxSelectionSuccess(self, mailbox):
        self.mailbox_details.chosen_mailbox = mailbox
        self.connection.connect_host.select(mailbox)
        self.app_state.state["mailbox_set"] = True
        self.refreshUi()

    def openDateSettings(self):
        DateWindow(self.master, self.date, onDateSetSuccess = self.onDateSetSuccess)

    def onDateSetSuccess(self):
        self.app_state.state["date_set"] = True
        self.refreshUi()

    def onPathSetSuccess(self):
        self.app_state.state["save_method_set"] = True
        self.refreshUi()

# =========================
# OKNO LOGOWANIA
# =========================
class MailConnectionWindow:
    def __init__(self, master, connection, onConnectionSuccess):
        self.window = tk.Toplevel(master)
        self.window.title("Połączenie")
        self.window.grab_set()
        self.connection = connection
        self.onConnectionSuccess = onConnectionSuccess
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
                self.onConnectionSuccess(mail_details)
        self.connection_status.set("")
        self.window.update_idletasks()


class LoginWindow:
    def __init__(self, master, connection, onLoginSuccess):
        self.window = tk.Toplevel(master)
        self.window.title("Logowanie")
        self.window.grab_set()
        self.onLoginSuccess = onLoginSuccess
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
        self.login_button = ttk.Button(self.window, text="Zaloguj", command=self.submit)
        self.status_label = ttk.Label(self.window,textvariable=self.login_status)

    def placeWidgets(self):
        self.window.geometry("200x180")

        ttk.Label(self.window, text="Login").grid(row=0, column=0, padx=5, pady=5)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.window, text="Hasło").grid(row=1, column=0, padx=5, pady=5)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        self.login_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

    def submit(self):
        user_credentials = UserCredentials(username = self.username.get().strip(),
                                           password = self.password.get())
        self.login_status.set("Logowanie...")
        self.window.update_idletasks()
        try:
            if user_credentials.checkCredentials():
                    if self.connection.auth(user_credentials):
                        self.window.destroy()
                        showinfo("Logowanie", f"Zalogowano:\nUżytkownik: {user_credentials.username}")
                        self.onLoginSuccess(self.connection.connect_host)
        except imaplib.IMAP4.error:
            showerror("Błąd logowania", "Sprawdź dane logowania \nlub \nspróbuj ponownie później")
        except Exception as e:
            showerror("Błąd",f"{e.__class__.__name__}")
        self.login_status.set("")
        self.window.update_idletasks()

class MailboxSelectionWindow:
    def __init__(self, master, connection, mailbox_details, onMailboxSelectionSuccess):
        self.window = tk.Toplevel(master)
        self.window.title("Wybór skrzynki")
        self.window.grab_set()
        self.onMailboxSelectionSuccess = onMailboxSelectionSuccess
        self.mailboxDetails = mailbox_details
        self.mailboxes = ["",*self.mailboxDetails.getAllMailboxes(connection)]
        self.build()
        self.placeWidgets()

    def build(self):
        self.mailbox_choice = ttk.Combobox(self.window, values=self.mailboxes)
        self.save_choice = ttk.Button(self.window,text="Zapisz", command=self.saveMailbox)

    def placeWidgets(self):
        self.window.geometry("200x180")

        for i in range(3):
            self.window.columnconfigure(i, weight=1)

        self.mailbox_choice.grid(row=0, column=0, columnspan=3, pady=10)
        self.save_choice.grid(row=1, column=0, columnspan=3, pady=5)

    def saveMailbox(self):
        chosen_mailbox = self.mailbox_choice.get()
        if chosen_mailbox == "":
            showwarning("Ostrzeżenie", "Nie wybrano skrzynki")
        else:
            self.onMailboxSelectionSuccess(chosen_mailbox)
        self.window.destroy()

class DateWindow:
    def __init__(self, master, date, onDateSetSuccess):
        self.window = tk.Toplevel(master)
        self.window.title("Zakres czasu")
        self.window.grab_set()
        self.onDateSetSuccess = onDateSetSuccess
        self.date:Date = date
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
        # print(datetime.datetime.strptime(self.calendar_one_date.get_date(), '%d-%m-%Y').date() == datetime.datetime.today().date())

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
        else:
            date_list.append(self.calendar_from.get_date())
            date_list.append(self.calendar_to.get_date())

        if self.date.setDate(time_range, date_list):
            self.window.destroy()
            self.onDateSetSuccess()

class SavePathWindow:
    def __init__(self, master, file_save_path, onPathSetSuccess):
        self.window = tk.Toplevel(master)
        self.window.title("Ścieżka zapisu")

        self.insert_frame = ttk.Frame(self.window)

        self.onPathSetSuccess = onPathSetSuccess
        self.file_save_path = file_save_path
        self.example_user:User = file_save_path.example_user
        self.types = ["imie", "nazwisko", "indeks", "rok", "grupa", "specjalizacja"]
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

        self.insert_combo = ttk.Combobox(self.insert_frame,
                                         textvariable=self.insert_var,
                                         values=[word.capitalize() for word in self.types],
                                         state="readonly",
                                         width=15
                                         )

        self.insert_button = ttk.Button(self.insert_frame,
                                        text="Wstaw pole",
                                        command=self.insert_field
                                        )

        self.path_entry = ttk.Entry(self.window,
                                    width=80,
                                    textvariable=self.path_var)

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
        self.window.geometry("750x270")

        self.info_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        self.insert_frame.grid(row=1,column=0, columnspan=2, padx=5, sticky="w")

        self.insert_combo.grid(row=0, column=0, padx=5,pady=5,)
        self.insert_button.grid(row=0, column=1, padx=5,pady=5,)

        self.path_entry.grid(row=2, column=0, columnspan=10, padx=10, pady=5, sticky="ew")

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

    def on_text_change(self, event=None):
        try:
            if len(event.keysym) > 1:
                self.preview_value.config(text=self.path_entry.get())
                self.update_example_preview(self.path_entry.get())
                return
        except AttributeError:
            pass

        text = self.path_entry.get()

        if "imię" in text.lower():
            text = re.sub("Imię", "Imie", text, flags=re.IGNORECASE)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, text)

        new_text = text
        print(new_text)
        for word in self.types:
            if word in new_text.lower() and f"{{{word}}}" not in new_text.lower():
                new_text = re.sub(word, f"{{{word.capitalize()}}}", new_text, flags=re.IGNORECASE)

        for brackets in ["{{","}}"]:
            if brackets in new_text:
                new_text = new_text.replace(brackets,brackets[0])

        if new_text != text:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, new_text)

        self.preview_value.config(text=new_text)
        self.update_example_preview(new_text)

    def update_example_preview(self, preview_text):
        example_text = preview_text
        for word in self.types:
            example_text = re.sub(
                f"{{{word.capitalize()}}}",
                self.example_user.user_info[word],
                example_text,
                flags=re.IGNORECASE
            )

        self.example_preview.config(text=example_text)

    def save(self):
        self.file_save_path.save_method = self.path_var.get()
        self.file_save_path.example_save_text = self.example_preview.cget("text")
        self.window.destroy()
        self.onPathSetSuccess()

# =========================
# START
# =========================
if __name__ == "__main__":
    app = App()
    app.run()