import imaplib
import poplib
import re
import time
from tkinter.messagebox import askretrycancel
from windows.temp_window import TempWindow

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
            self.connect_host.sock.settimeout(10)
            return True

        elif mail_details.protocol == "POP3":
            self.protocol = "POP3"
            self.mail_details = mail_details
            self.connect_host = poplib.POP3_SSL(
                mail_details.address,
                mail_details.port)
            self.connect_host.sock.settimeout(10)

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
            self.reconnect(self.mail_details, app_state)
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
            raise ValueError("Adres nie może być pusty")
        return True

    def checkPort(self, port):
        if not port:
            raise ValueError("Pole Port nie może być puste")
        elif not str(port).isdigit():
            raise ValueError("Port musi mieć wartość numeryczną")
        elif not (1 <= int(port) <= 65535):
            raise ValueError("Port musi być w zakresie 1–65535")
        else:
            self.port = int(port)
        return True

    def checkProtocol(self, protocol):
        if protocol not in ["IMAP", "POP3"]:
            raise ValueError("Błędny protokół")
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
                match = re.search(r'\)\s+"?(.)"?\s+"?([^"]+)"?$', i.decode('utf-8'))
                if match:
                    self.mailbox_list.append(match.group(2))
        return self.mailbox_list
