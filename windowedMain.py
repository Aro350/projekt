import datetime
import imaplib
import os
import socket

import re
import time

import platform
import base64
from cryptography.fernet import Fernet
import hashlib

from email.message import EmailMessage
from email import policy
from email.parser import BytesParser

import poplib
from email.utils import parsedate_to_datetime

import patoolib

from tkinter.messagebox import showwarning, showerror, showinfo, askyesno, askretrycancel

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
# LOGIKA
# =========================
class Config:
    def __init__(self):
        self.address = ""
        self.port = 0
        self.protocol = ""
        self.chosen_mailbox = ""
        self.username = ""
        self.password = ""
        self.user_file_location = ""
        self.date_range = ""
        self.date_list = []
        self.save_location = ""
        self.save_method = ""
        self.filter_text = ""

    def clearConfig(self):
        for key in list(self.__dict__.keys()):
            if key == "port":
                self.__dict__[key] = 0
            elif key == "date_list" or key == "filter":
                self.__dict__[key] = []
            else:
                self.__dict__[key] = ""

    def saveParameters(self, config_params, config_save_location):
        with open(config_save_location, 'w') as file:
            json.dump(config_params, file, indent=4)
            showinfo("Informacja", f"Konfiguracja zapisana w:\n"
                                   f"{config_save_location}")

    def readConfigFile(self, config_file_location):
        with open(config_file_location) as file:
            conf = json.load(file)
        for key, value in conf.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError

    def loadConfig(self, app):
        if self.address and self.port and self.protocol:
            app.mail_details.setFromConfig(self.address, self.port, self.protocol)
            if app.connection.connect(app.mail_details):
                app.app_state.state["mail_connected"] = True

        if self.username and self.password:
            self.decryptCredentials()
            app.user_credentials = UserCredentials(self.username, self.password)
            app.login_text.config(text=self.username)
            if app.app_state.state["mail_connected"]:
                if app.connection.auth(app.user_credentials):
                    app.app_state.state["logged_in"] = True

        if self.chosen_mailbox:
            app.mailbox_details.setFromConfig(self.chosen_mailbox)
            app.mailbox_text.config(text=self.chosen_mailbox)
            app.app_state.state["mailbox_set"] = True

        if self.user_file_location:
            if app.user_file.getUsers(self.user_file_location):
                app.user_file_text.config(text=self.user_file_location)
                app.app_state.state["user_file_set"] = True

        if self.save_location:
            app.file_save_path.save_location = self.save_location
            app.file_save_text.config(text=f"{self.save_location}/")
            app.app_state.state["save_loc_set"] = True

        if self.save_method:
            app.file_save_path.setFromConfig(self.save_method)
            app.app_state.state["save_method_set"] = True

        if self.date_range:
            if app.date.setDate(self.date_range, self.date_list):
                app.app_state.state["date_set"] = True

        if self.filter_text:
            if not app.subject_filter:
                app.subject_filter = Filter()
            app.subject_filter.readFilter(self.filter_text)
            app.onFilterSet()

    def save_selected_config(self, active_keys, app, save_location):
        config_params = {}

        if "mail" in active_keys:
            config_params.update({"address": app.mail_details.address,
                                  "port": app.mail_details.port,
                                  "protocol": app.mail_details.protocol})
        if "credentials" in active_keys:
            username, password = ["",""]
            if app.user_credentials.username and app.user_credentials.password:
                username,password = self.encryptCredentials(app.user_credentials.username, app.user_credentials.password)

            config_params.update({"username": username,
                                  "password": password})
        if "mailbox" in active_keys:
            config_params["chosen_mailbox"] = app.mailbox_details.chosen_mailbox
        if "user_file" in active_keys:
            config_params["user_file_location"] = app.user_file.user_file_location
        if "save_location" in active_keys:
            config_params["save_location"] = app.file_save_path.save_location
        if "date" in active_keys:
            config_params.update({"date_range": app.date.date_range, "date_list": app.date.date_list})
        if "save_method" in active_keys:
            config_params["save_method"] = app.file_save_path.save_method
        if "filter" in active_keys:
            config_params["filter_text"] = app.subject_filter.filter_text

        if config_params:
            self.saveParameters(config_params, save_location)

    def createEncryptionKey(self):
        unique_machine_info = f"{str(platform.machine())} {str(platform.node())} {str(platform.processor())} {str(platform.system())}".encode('utf-8')
        key = base64.urlsafe_b64encode(hashlib.sha256(unique_machine_info).digest())
        return Fernet(key)

    def encryptCredentials(self, username, password):
        encryption_key = self.createEncryptionKey()
        encrypted_username = encryption_key.encrypt(username.encode('utf-8'))
        encrypted_password = encryption_key.encrypt(password.encode('utf-8'))
        return [encrypted_username.decode('utf-8'),encrypted_password.decode('utf-8')]

    def decryptCredentials(self):
        encryption_key = self.createEncryptionKey()
        self.username = encryption_key.decrypt(self.username).decode('utf-8')
        self.password = encryption_key.decrypt(self.password).decode('utf-8')

class Connection:
    def __init__(self):
        self.connect_host = None
        self.protocol = ""
        self.username = ""
        self.mail_details = None
        self.mailbox_details = None
        self.user_credentials = None

    def connect(self, mail_details):
        if mail_details.protocol == "IMAP":
            self.protocol = "IMAP"
            self.mail_details = mail_details
            self.connect_host = imaplib.IMAP4_SSL(
                mail_details.address,
                mail_details.port)
            return True

        elif mail_details.protocol == "POP3":
            self.protocol = "POP3"
            self.mail_details = mail_details
            self.connect_host = poplib.POP3_SSL(
                mail_details.address,
                mail_details.port)
            return True
        return False

    def disconnect(self):
        if not self.connect_host:
            return False

        try:

            if self.protocol == "IMAP":
                try:
                    self.connect_host.logout()
                except:
                    pass

            elif self.protocol == "POP3":
                try:
                    self.connect_host.quit()
                except:
                    pass

            try:
                self.connect_host.sock.close()
            except:
                pass

        except Exception as e:
            print(e)
            pass

        finally:
            self.connect_host = None
            self.protocol = ""
            self.mail_details = None

    def clearUserInfo(self):
        self.username = ""
        self.mailbox_details = None
        self.user_credentials = None

    def auth(self, user_credentials):
        protocol = self.protocol
        if protocol == "IMAP":
            self.connect_host.login(user_credentials.username, user_credentials.password)
            self.username = user_credentials.username
            self.user_credentials = user_credentials
            return True
        elif protocol == "POP3":
            self.connect_host.user(user_credentials.username)
            self.connect_host.pass_(user_credentials.password)
            self.username = user_credentials.username
            self.user_credentials = user_credentials
            return True
        return False

    def check_connection_info(self, window, app_state, flag = None):
        if flag == "inactivity":
            condition = askretrycancel("Połączenie", "Zostałeś wylogowany. Połączyć ponownie?", parent=window)
        else:
            condition = askretrycancel("Połaczenie", "Połączenie z serwerem zostało utracone.", parent=window)

        while condition:
            temp_window = TempWindow(window, "Połączenie", "Łączenie...")
            time.sleep(1)
            if self.reconnect(self.mail_details, app_state):
                temp_window.changeContent("Połączono")
                time.sleep(2)
                temp_window.closeWindow()
                del temp_window
                return True
            temp_window.closeWindow()
            del temp_window
            if not askretrycancel("Połączenie", "Nie udało się połączyć. Spróbować ponownie?", parent=window):
                break
        return False

    def check_connection(self):
        try:
            if self.protocol == "IMAP":
                status, _ = self.connect_host.noop()
                return status == "OK"

            elif self.protocol == "POP3":
                try:
                    self.connect_host.noop()
                    return True
                except poplib.error_proto:
                    return True
        except:
            return False

    def reconnect(self, mail_details, app_state):
        try:
            if app_state.state["mail_connected"]:
                self.disconnect()
                return self.connect(mail_details)
        except:
            return False

    def manageConnectionLoss(self,
                             err_msg,
                             window,
                             app_state):
        reauth = False

        if "nonauth" in err_msg or "inactivity" in err_msg:
            if self.check_connection_info(window, app_state, "inactivity"):
                reauth = True
        elif self.check_connection_info(window, app_state):
            reauth = True
        elif all([word in str(err_msg) for word in ("NoneType", "login")]):
            pass
        elif all([word in str(err_msg).lower() for word in ("allowed", "states", "selected")]):
            pass

        if reauth:
            temp_window = TempWindow(window, "Logowanie", "Ponowne logowanie")
            time.sleep(2)
            if self.auth(self.user_credentials):
                temp_window.changeContent("Zalogowano")
                if self.mail_details.protocol == "IMAP" and app_state.state["mailbox_set"]:
                    self.connect_host.select(self.mailbox_details.chosen_mailbox)
                time.sleep(2)
                temp_window.closeWindow()
                return True
        return False


class MailDetails:
    def __init__(self, address="", port=0, protocol=""):
        self.address = address.lower()
        self.port = port
        self.protocol = protocol

    def setDetails(self, address, port, protocol):
        if self.checkDetails(address, port, protocol):
            self.address = address
            self.port = port
            self.protocol = protocol
            return True
        return False

    def checkDetails(self, address, port, protocol):
        if self.checkAddress(address) and self.checkPort(port) and self.checkProtocol(protocol):
            return True
        return False

    def checkAddress(self, address):
        if len(str(address).strip()) == 0 or "np. stud.prz.edu.pl" in str(address):
            showerror("Błąd", "Adres nie może być pusty")
            return False
        return True

    def checkPort(self, port):
        if not port:
            showerror("Błąd", "Pole Port nie może być puste")
            return False
        elif not str(port).isdigit():
            showerror("Błąd", "Port musi mieć wartość numeryczną")
            return False
        elif not (1 <= int(port) <= 65535):
            showerror("Błąd", "Port musi być w zakresie 1–65535")
            return False
        else:
            self.port = int(port)
        return True

    def checkProtocol(self, protocol):
        if protocol not in ["IMAP", "POP3"]:
            showerror("Błąd", "Błędny protokół")
            return False
        return True

    def setFromConfig(self, address, port, protocol):
        self.setDetails(address, port, protocol)


class MailboxDetails:
    def __init__(self):
        self.mailbox_list = []
        self.chosen_mailbox = ""

    def setFromConfig(self, chosen_mailbox):
        self.chosen_mailbox = chosen_mailbox

    def getAllMailboxes(self, connection):
        if len(self.mailbox_list) != 0:
            self.mailbox_list = []
        for i in (connection.connect_host.list()[1]):
            if not b"doveco" in i:
                self.mailbox_list.append(str(i).split(".")[1][2:-1])
        return self.mailbox_list


class MailData:
    def __init__(self, connection, user_file, date, file_save_path):
        self.connection: Connection = connection
        self.users_list = user_file.users_class_list
        self.date_choice = date.date_range
        self.date_list = date.parseDate(date.date_list)
        self.query = []
        self.file_save_path: FileSavePath = file_save_path

    # ---------------------------------------------------------
    # Tworzenie zapytania dla wybranej daty
    # ---------------------------------------------------------
    def makeQuery(self):
        quotes = ["ON", "SINCE", "BEFORE"]
        index = 0

        match self.date_choice:
            case "one_day":
                self.query = [quotes[index], self.date_list[0].strftime("%d-%b-%Y")]

            case "from_to":
                self.date_list[1] = self.date_list[1] + dt.timedelta(days=1)
                for date in self.date_list:
                    self.query += [quotes[index + 1], date.strftime("%d-%b-%Y")]
                    index += 1
            case "from":
                self.query += [quotes[1], self.date_list[0].strftime("%d-%b-%Y")]

            case "to":
                self.date_list[0] = self.date_list[0] + dt.timedelta(days=1)
                self.query += [quotes[2], self.date_list[0].strftime("%d-%b-%Y")]

    def getMessage(self, download):
        if self.connection.protocol == "IMAP":
            self.makeQuery()
            self.getImapMessage(download)
        else:
            username_dict = download.makeUsernameDict()
            self.getPopMessage(download, username_dict)

    def getImapMessage(self, download):
        for user in self.users_list:
            status, data = self.connection.connect_host.search(None, 'FROM', f'"{user.username}"', *self.query)
            message_id_list = data[0].split()
            download.getImapAttachments(self.connection.connect_host,
                                        message_id_list,
                                        user,
                                        self.file_save_path)

    def getPopMessage(self, download, username_dict):
        conn = self.connection.connect_host
        count, _ = conn.stat()
        date_filter = self.dateFilter()

        try:
            caps = conn.capa()
            supports_top = b"TOP" in caps
        except Exception:
            supports_top = False

        for i in range(count, 0, -1):

            try:
                if supports_top:
                    try:
                        resp = conn.top(i, 0)
                    except poplib.error_proto:
                        supports_top = False
                        resp = conn.retr(i)
                else:
                    resp = conn.retr(i)

                joined = b"\r\n".join(resp[1])
                message = BytesParser(policy=policy.default).parsebytes(joined)

                date_header = message.get("Date")
                if not date_header:
                    continue

                message_date = parsedate_to_datetime(date_header).date()

                if message_date < self.date_list[0] and self.date_choice != "to":
                    break

                if not date_filter(message_date):
                    continue

                user = self.checkUser(message.get("From", ""), username_dict)
                if not user:
                    continue

                if supports_top:
                    full_resp = conn.retr(i)
                    full_joined = b"\r\n".join(full_resp[1])
                    full_message = BytesParser(policy=policy.default).parsebytes(full_joined)
                else:
                    full_message = message

                parsed_date = parsedate_to_datetime(date_header)
                message_datetime = {"data_odbioru": parsed_date.date(),
                                    "czas_odbioru": parsed_date.time()}

                download.getAttachment(full_message, self.file_save_path, user, message_datetime)

            except Exception as e:
                print(f"Błąd przy wiadomości {i}: {e}")
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

    def checkUser(self, mail_user, username_dict):
        for username in username_dict.keys():
            if username in mail_user:
                user = username_dict[username]
                return user
        return None


class Download:
    def __init__(self, connection, mail_data, users_class_list, subject_filter, ask_log_file):
        self.connection: Connection = connection.connect_host
        self.mail_data: MailData = mail_data
        self.users_class_list: list[User] = users_class_list
        self.subject_filter: Filter = subject_filter
        self.ask_log_file = ask_log_file
        self.log_data = None
        self.user_count = []
        self.message_count = []
        self.attachment_count = 0

    def getMailData(self):
        if self.ask_log_file:
            self.log_data = {}
        self.mail_data.getMessage(self)

    def makeUsernameDict(self):
        return {user.username: user for user in self.users_class_list}

    def getImapAttachments(self,
                           connection,
                           message_id_list,
                           user: "User",
                           file_save_path):

        for message in message_id_list:
            status, message_data = connection.fetch(message, "(RFC822)")
            message_content: EmailMessage = BytesParser(policy=policy.default).parsebytes(message_data[0][1])
            self.getAttachment(message_content, file_save_path, user)

    def getAttachment(self, message, file_save_path: "FileSavePath", user, message_datetime=None):
        if (self.subject_filter and len(self.subject_filter.filter_list) != 0 and
                not any([keyword.lower() in message.get("Subject", "").lower() for keyword in
                         self.subject_filter.filter_list])):
            return None

        attachments = list(message.iter_attachments())
        if not attachments:
            return None

        if not message_datetime:
            parsed_date = parsedate_to_datetime(message.get("Date"))
            message_datetime = {"data_odbioru": parsed_date.date(), "czas_odbioru": parsed_date.time()}

        file_save_path.addUserInfo(user.user_info, message_datetime)
        full_save_path = file_save_path.full_save_path
        os.makedirs(full_save_path, exist_ok=True)
        for attachment in message.iter_attachments():
            filename = attachment.get_filename()
            payload = attachment.get_payload(decode=True)
            print(f"Znaleziono: {filename}")
            self.saveAttachments(payload, filename, full_save_path, user)
            if self.ask_log_file:
                self.add_log(message, user, filename, full_save_path)

    def saveAttachments(self, payload, filename, full_save_path, user):
        file_path = os.path.join(full_save_path, filename)
        try:
            # if os.path.exists(file_path):
            #     print(f"Plik {filename} użytkownika {user.username} już istnieje.")
            # else:
            with open(f"{file_path}", "wb") as f:
                f.write(payload)
                self.attachment_count += 1
            if patoolib.is_archive(str(file_path)):
                extract_dir = (full_save_path +
                               filename.split(".")[0] +
                               "_EXTRACTED_" +
                               str(datetime.datetime.today().strftime('%d-%m-%Y')))
                os.makedirs(extract_dir,
                            exist_ok=True)
                patoolib.extract_archive(archive=str(file_path), outdir=extract_dir)
        except Exception as e:
            print(f"Błąd zapisu pliku. {e}")

    def add_log(self, message, user, filename, full_save_path):

        date = str(parsedate_to_datetime(message.get("Date")).date())
        user_name = f"{user.user_info['imie']} {user.user_info['nazwisko']}"
        subject = str(message.get("Subject", "Brak tematu"))
        self.user_count.append(user.username)
        self.message_count.append(f"{message.get('From')}: {message.get('Message-ID')}")

        if date not in self.log_data:
            self.log_data[date] = {}

        if user_name not in self.log_data[date]:
            self.log_data[date][user_name] = {}

        if subject not in self.log_data[date][user_name]:
            self.log_data[date][user_name][subject] = {}

        if full_save_path not in self.log_data[date][user_name][subject]:
            self.log_data[date][user_name][subject][full_save_path] = []

        self.log_data[date][user_name][subject][full_save_path].append(filename)

    def save_log(self, log_save_loc):
        today = datetime.datetime.today()
        if log_save_loc == "":
            log_save_loc = f"dziennik_{today.strftime("%d-%m-%Y_%H-%M-%S")}.txt"

        with open(log_save_loc, "w", encoding="utf-8") as f:
            f.write(f"***** Data utworzenia dziennika: {str(today.strftime("%d-%m-%Y  %H:%M:%S"))} *****\n")
            self.message_count = len(set(self.message_count))
            self.user_count = len(set(self.user_count))
            f.write(f"Pobrano: {self.attachment_count} załączników\n"
                    f"      z: {self.message_count} wiadomości\n"
                    f"     od: {self.user_count} użytkowników\n")

            for date in sorted(self.log_data):
                f.write(f"{date}\n")
                for user_name in self.log_data[date]:
                    f.write(f"  {user_name}\n")
                    for subject in self.log_data[date][user_name]:
                        f.write(f"      {subject}\n")
                        for file_save_path in self.log_data[date][user_name][subject]:
                            f.write(f"          {file_save_path}\n")
                            for attachment in self.log_data[date][user_name][subject][file_save_path]:
                                f.write(f"              {attachment}\n")

                f.write("\n")

class FileSavePath:
    def __init__(self):
        self.save_location = ""
        self.save_method = ""
        self.save_method_for_user = ""
        self.full_save_path = ""

        self.types = ["imie",
                      "nazwisko",
                      "indeks",
                      "rok",
                      "grupa",
                      "specjalizacja",
                      "data_zapisu",
                      "czas_zapisu",
                      "data_odbioru",
                      "czas_odbioru"
                      ]

        self.symbols = ["/",
                        "_",
                        "spacja",
                        "-"]

        self.example_save_text = ""

        self.download_datetime = {"data_zapisu": datetime.datetime.today().strftime('%Y-%m-%d'),
                                  "czas_zapisu": datetime.datetime.now().time().strftime('%H-%M-%S')}

        self.example_receive_datetime = {"data_odbioru": datetime.datetime.today(),
                                         "czas_odbioru": datetime.datetime.now().time()}

        self.example_user = User("jankowalski@email.pl",
                                 "Jan",
                                 "Kowalski",
                                 "2",
                                 "EF-ZI",
                                 "1",
                                 "123456")

    def setFromConfig(self, save_method):
        self.save_method = save_method
        if self.save_method != "":
            self.example_save_text = self.replaceText(save_method,
                                                      self.example_user.user_info,
                                                      self.example_receive_datetime)

    def replaceText(self, raw_text, message_user_info, message_datetime):
        replaced_text = raw_text
        if any(time_word.lower() in raw_text.lower() for time_word in message_datetime.keys()):
            message_datetime["data_odbioru"] = message_datetime["data_odbioru"].strftime('%Y-%m-%d') if type(
                message_datetime["data_odbioru"]) != str else message_datetime["data_odbioru"]
            message_datetime["czas_odbioru"] = message_datetime["czas_odbioru"].strftime('%H-%M-%S') if type(
                message_datetime["czas_odbioru"]) != str else message_datetime["czas_odbioru"]

        for word in self.types:
            if word.lower() in raw_text.lower():
                if word in message_user_info:
                    value = message_user_info[word]
                elif word in message_datetime:
                    value = message_datetime[word]
                else:
                    value = self.download_datetime[word]
                if str(value).strip() == "":
                    value = "None"
                replaced_text = re.sub(
                    f"{{{word.capitalize()}}}",
                    str(value),
                    replaced_text,
                    flags=re.IGNORECASE
                )
        return replaced_text

    def makeSavePath(self):
        self.full_save_path = self.save_location + "/" + self.save_method_for_user + "/"

    def addUserInfo(self, user_info, message_datetime):
        self.save_method_for_user = self.replaceText(self.save_method,user_info,message_datetime)
        self.makeSavePath()

class Filter:
    def __init__(self):
        self.filter_text = ""
        self.filter_list = []

    def readFilter(self, filter_text):
        self.filter_text = filter_text.strip()
        self.filter_list = self.filter_text.split(",")

    def checkFilter(self, subject):
        for text in self.filter_list:
            if text in subject:
                return True
        return False

class User:
    username: str
    first_name: str
    surname: str
    year: str
    specialization: str
    group: str
    index: str

    def __init__(self,
                 username=None,
                 first_name=None,
                 surname=None,
                 year=None,
                 specialization=None,
                 group=None,
                 index=None):
        self.username = username
        self.user_info = {
            "imie": first_name,
            "nazwisko": surname,
            "rok": year,
            "grupa": group,
            "specjalizacja": specialization,
            "indeks": index
        }

class UserFile:
    def __init__(self):
        self.user_file_location = ""
        self.users_list = []
        self.users_class_list: list[User] = []

    def getUsers(self, user_file_location):
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

            # axis 0 = rows
            # axis 1 = columns

            users = users.dropna(axis=0, how="all")

            users = users.dropna(axis=1, how="all")

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
            for key, value in duplicated_users.items():
                duplicated_users_list += f"Wiersz: {str(key)}, Adres: {str(value)}\n"
            if len(duplicated_users_list) != 0:
                showwarning("Ostrzeżenie", f"W pliku znajdują się zduplikowane adresy email:\n{duplicated_users_list}")

            users.columns = users.columns.str.lower()
            self.users_list = list(users.to_dict("index").values())
            self.convertUsers()
            return True

        except Exception as e:
            print(e)

    def findDuplicates(self, users, column_name):
        users_list = users[column_name].tolist()
        duplicates_list = users.duplicated(subset=column_name)
        duplicated_users = {}
        for i, status in enumerate(duplicates_list):
            if status:
                duplicated_users[i + 1] = users_list[i]
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

    def fixValues(self, user):
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
    # one_day
    # from_to
    # from
    # to
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
                    showerror("Błąd", "Początkowa data jest większa niż końcowa")
                    return False

                if parsed_date_list[0] == parsed_date_list[1]:
                    showwarning("Ostrzeżenie", "Daty są takie same")

                return True

            case "one_day":
                return True

            case "from":
                if parsed_date_list[0] > present_date:
                    showerror("Błąd", "Początkowa data jest większa niż końcowa")
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
    def __init__(self, username="", password=""):
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
        self.app_state: AppState = app_state
        self.config: Config = config

        self.connection: Connection = connection

        self.mail_details: MailDetails = mail_details
        self.mailbox_details: MailboxDetails = mailbox_details
        self.user_file: UserFile = user_file
        self.date: Date = date
        self.file_save_path: FileSavePath = file_save_path

        self.user_credentials = UserCredentials()
        self.subject_filter = Filter()

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
        self.set_save_path_button = ttk.Button(self.master, text="Wybierz sposób zapisu", command=self.openSavePath)
        self.filter_button = ttk.Button(self.master, text="Dodaj filtr", command=self.openFilter)
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
        self.filter_label = ttk.Label(self.master, text="Filtr: ")
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
        self.master.geometry("700x460")
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
        self.download_button.grid(row=len(buttons) + 3, column=0, columnspan=3, padx=5, pady=(10, 10), sticky="wesn")
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

        except Exception as e:
            print(e)
            showerror("Błąd", f"Plik konfiguracyjny zawiera błąd:\n{e}")
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
        self.subject_filter = Filter()

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
        user_file_loc = askopenfilename(title="Wybierz plik Excel z użytkownikami",
                                        filetypes=[("Excel files", "*.xlsx *.xls")])
        if self.user_file.getUsers(user_file_loc):
            self.user_file_text.config(text=user_file_loc)
            self.app_state.state["user_file_set"] = True
            self.refreshUi()

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
            SaveConfigWindow(self.master, onClose=self.changeWindowStatus, onConfigSave = self.onConfigSave)
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
            del mail_data
            del download

        except (ConnectionResetError,
                ConnectionAbortedError,
                imaplib.IMAP4.abort,
                OSError,
                AttributeError,
                imaplib.IMAP4.error,
                poplib.error_proto,
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
            print(e)

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
        print(self.app_state.state)

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
        self.filter_text.config(text=self.subject_filter.filter_text)

    def onConfigSave(self, checkbutton_vars):
        active_keys = [key for key, var in checkbutton_vars.items() if var.get()]

        if not active_keys:
            showwarning("Ostrzeżenie", "Nie wybrano żadnych opcji do zapisu.")
            return

        config_save_location = asksaveasfilename(defaultextension=".json", filetypes=(("Json File", "*.json"),))
        if config_save_location:
            self.config.save_selected_config(active_keys, self, config_save_location)
            self.save_config_text.config(text=config_save_location)


# =========================
# OKNO LOGOWANIA
# =========================
class TemplateWindow:
    def __init__(self, master, title, window_name, onClose):
        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.grab_set()
        self.window_name = window_name
        self.onClose = onClose
        self.window.protocol("WM_DELETE_WINDOW", self.window_close)

    def window_close(self):
        self.window.destroy()
        self.onClose(self.window_name)


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
        self.window.geometry("250x200")

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
            self.connection_status.set("")
            self.window.update_idletasks()

        except (socket.gaierror, OSError):
            showerror("Błąd", "Błąd połączenia.\nSprawdź połączenie internetowe i dostępność serwera.", parent = self.window)
            self.connection_status.set("")
            return False
        except TimeoutError:
            showerror("Błąd",
                      "Przekroczono limit czasu połączenia. Otrzymano błędny port lub usługa jest chwilowo niedostępna", parent = self.window)
            self.connection_status.set("")
            return False
        except Exception as e:
            self.connection_status.set("")
            showerror("Błąd", f"\n{e}", parent = self.window)
            exit()

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
        self.app_state: AppState = app_state
        self.protocol = self.connection.protocol
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.login_status = tk.StringVar(value="")
        self.build()
        self.placeWidgets()

    def build(self):
        self.entry_username = ttk.Entry(self.window, textvariable=self.username)
        self.entry_password = ttk.Entry(self.window, textvariable=self.password, show="*")
        self.login_button = ttk.Button(self.window, text="Zaloguj", command=self.submit)
        self.status_label = ttk.Label(self.window, textvariable=self.login_status)

    def placeWidgets(self):
        self.window.geometry("240x160")

        ttk.Label(self.window, text="Login").grid(row=0, column=0, padx=5, pady=5)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5, sticky="nswe")

        ttk.Label(self.window, text="Hasło").grid(row=1, column=0, padx=5, pady=5)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5, sticky="nswe")

        self.login_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

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
                poplib.error_proto) as e:

            if "Authentication failed" in str(e):
                showerror("Błąd logowania", "Sprawdź dane logowania \nlub \nspróbuj ponownie później", parent=self.window)
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
        self.mailbox_choice = ttk.Combobox(self.window)
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
            print(e)
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
            print(e)


class DateWindow(TemplateWindow):
    def __init__(self, master, date, onClose, onDateSetSuccess):
        super().__init__(master, "Zakres czasu", "date", onClose)
        self.onDateSetSuccess = onDateSetSuccess
        self.date: Date = date
        self.timestamp = tk.StringVar(value="one_day")
        self.build()
        self.placeWidgets()
        self.calendar_one_date.bind("<<CalendarSelected>>", self.updateDate)
        self.calendar_from.bind("<<CalendarSelected>>", self.updateDateFrom)
        self.calendar_to.bind("<<CalendarSelected>>", self.updateDateTo)
        self.updateWindow()

    def build(self):
        self.radio_frame = ttk.Frame(self.window)
        self.one_day = ttk.Radiobutton(self.radio_frame, text="Jeden dzień", variable=self.timestamp, value="one_day",
                                       command=self.updateWindow)
        self.from_to = ttk.Radiobutton(self.radio_frame, text="Od...Do", variable=self.timestamp, value="from_to",
                                       command=self.updateWindow)
        self.only_from = ttk.Radiobutton(self.radio_frame, text="Tylko od...", variable=self.timestamp, value="from",
                                         command=self.updateWindow)
        self.only_to = ttk.Radiobutton(self.radio_frame, text="Tylko do...", variable=self.timestamp, value="to",
                                       command=self.updateWindow)

        self.content_frame = ttk.Frame(self.window)
        self.calendar_one_date = Calendar(self.content_frame,
                                          selectmode="day",
                                          locale="pl",
                                          year=datetime.datetime.now().year,
                                          month=datetime.datetime.now().month,
                                          day=datetime.datetime.now().day,
                                          date_pattern="dd-mm-yyyy")

        self.calendar_from = Calendar(self.content_frame,
                                      selectmode="day",
                                      locale="pl",
                                      year=datetime.datetime.now().year,
                                      month=datetime.datetime.now().month,
                                      day=datetime.datetime.now().day,
                                      date_pattern="dd-mm-yyyy")

        self.calendar_to = Calendar(self.content_frame,
                                    selectmode='day',
                                    locale="pl",
                                    year=datetime.datetime.now().year,
                                    month=datetime.datetime.now().month,
                                    day=datetime.datetime.now().day,
                                    date_pattern="dd-mm-yyyy")

        self.one_date_label = ttk.Label(self.content_frame, text=self.calendar_from.get_date())
        self.date_from_label = ttk.Label(self.content_frame, text=self.calendar_from.get_date())
        self.date_to_label = ttk.Label(self.content_frame, text=self.calendar_to.get_date())

        self.save_time_button = ttk.Button(self.content_frame, text="Zapisz", command=self.save)

    def placeWidgets(self):
        self.window.minsize(560, 300)

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

        self.calendar_one_date.grid(row=1, column=0, padx=(15, 5), pady=(15, 5))

        self.calendar_from.grid(row=1, column=0, padx=(15, 5), pady=(15, 5))
        self.calendar_to.grid(row=1, column=1, padx=(20, 15), pady=(15, 5))

        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)

        self.one_date_label.grid(row=2, column=0)
        self.date_from_label.grid(row=2, column=0)
        self.date_to_label.grid(row=2, column=1)

        self.save_time_button.grid(row=4, column=0, columnspan=2, pady=(10, 0))

    def updateDateFrom(self, event=None):
        self.date_from_label.config(text=self.calendar_from.get_date())

    def updateDateTo(self, event=None):
        self.date_to_label.config(text=self.calendar_to.get_date())

    def updateDate(self, event=None):
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
        else:
            date_list.append(self.calendar_from.get_date())
            date_list.append(self.calendar_to.get_date())

        if self.date.setDate(time_range, date_list):
            self.window_close()
            self.onDateSetSuccess()


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
        self.window.geometry("750x270")

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
                                                                                 self.file_save_path.example_datetime))
                return
        except AttributeError:
            pass

        text = self.path_entry.get()

        if "imię" in text.lower():
            text = re.sub("Imię", "Imie", text, flags=re.IGNORECASE)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, text)

        new_text = text
        for word in self.types:
            if word in new_text.lower() and f"{{{word}}}" not in new_text.lower():
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

class SaveConfigWindow(TemplateWindow):
    def __init__(self, master, onClose, onConfigSave):
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
            "filtr"
        ]
        self.checkbuttons = []
        self.checkbutton_vars = {}
        self.window.grab_set()
        self.build()
        self.placeWidgets()

    def build(self):
        self.info_label = ttk.Label(self.window, text="Wybierz informacje do zapisania w pliku konfiguracyjnym.")

        for field, text in zip(self.fields, self.texts):
            var = tk.BooleanVar()
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

class TempWindow:
    def __init__(self, master, title, text):
        self.temp_window = tk.Toplevel(master)
        self.temp_window.title(title)
        self.temp_window.geometry("250x100")
        self.temp_window.transient(master)
        self.temp_window.grab_set()
        self.text_label = ttk.Label(self.temp_window,
                                    text=text)
        self.text_label.pack()
        self.temp_window.update()

    def closeWindow(self):
        self.temp_window.destroy()

    def changeContent(self, text):
        self.text_label.config(text=text)
        self.temp_window.update()


# =========================
# START
# =========================
if __name__ == "__main__":
    app = App()
    app.run()