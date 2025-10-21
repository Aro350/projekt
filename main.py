import getpass
import imaplib
import os
import socket
import time

from email.message import EmailMessage
from email import policy
from email.parser import BytesParser

import pandas as pd
import json
import datetime as dt
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory


class App:
    def __init__(self):
        self.config = Config()
        self.user_credentials = UserCredentials()
        self.mail_info = MailInfo()
        self.user_file = UserFile()
        self.connection = None
        self.mailbox = None
        self.timestamp = None

    def run(self):
        try:
            if self.askLoadConfig():
                self.loadFromConfig()
            else:
                self.newConfig()

            self.timestamp = Time()
            self.timestamp.setTimestamp()
            self.timestamp.printDatetime()

            mail_data = MailData(self.connection, self.user_file, self.timestamp)
            mail_data.getSaveLocation()
            mail_data.getMessage()

            print("\nProgram zakończony pomyślnie.\n")

        except KeyboardInterrupt:
            print("\nPrzerwano przez użytkownika.")

        except Exception as e:
            print(f"\nBłąd krytyczny: {e}\n")


    def askLoadConfig(self):
        while True:
            choice = input("Czy wczytać konfigurację? (T/N): ").strip().upper()
            if choice in ["T", "N"]:
                return choice == "T"
            print("Nieprawidłowa odpowiedź. Spróbuj ponownie.")

    def loadFromConfig(self):
        print("\n** Wczytywanie konfiguracji **")
        self.config.loadConfig()
        print("** Konfiguracja załadowana **")
        print(self.config)

        # Dane serwera
        self.mail_info.getFromConfig(self.config)

        # Połączenie
        self.connection = Connection(self.mail_info)
        self.connection.connect()

        # Dane logowania
        self.user_credentials.getCredentials()
        self.connection.login(self.user_credentials)

        # Skrzynka pocztowa
        self.mailbox = Mailbox(self.connection)
        self.mailbox.getFromConfig(self.config)

        # Plik z użytkownikami
        self.user_file.getFromConfig(self.config)
        self.user_file.convertData()

        print(f"Używana skrzynka: {self.mailbox.mailbox_name}")

        print(self.connection.connect_host.state)

    def newConfig(self):
        # Dane serwera
        self.mail_info.getInput()

        # Połączenie
        self.connection = Connection(self.mail_info)
        self.connection.connect()

        # Dane logowania
        self.user_credentials.getInput()
        self.connection.login(self.user_credentials)

        # Skrzynka pocztowa
        self.mailbox = Mailbox(self.connection)
        self.mailbox.mailboxSelect()

        # Plik z użytkownikami
        self.user_file.getUserFileLocation()
        self.user_file.convertData()

        # Zapis konfiguracji
        self.config.saveParameters(self.mail_info, self.user_file, self.mailbox)
        self.config.askForSave()

class User:
    username: str
    year: str

    def __init__(self,username = None, year = None):
        self.username = username
        self.year = year


class Time:
    current_date = None
    timestamp_list = None

    def __init__(self
                 # day = current_date.day,
                 # month = current_date.month,
                 # year=current_date.year
                 # # hours= 0,
                 # # minutes = 0,
                 # # seconds = 0
                 ):
        self.current_date = dt.datetime.today().date()
        self.day = self.current_date.day
        self.month = self.current_date.month
        self.year = self.current_date.year
        self.timestamp_list = []
        # self.hours = hours
        # self.minutes = minutes
        # self.seconds = seconds

    def __str__(self):
        # return f"{self.day}-{self.month}-{self.year} {self.hours}:{self.minutes}:{self.seconds}"
        return f"{self.day}-{self.month}-{self.year}"

    def printDatetime(self):
        output = "Wybrany zakres czasu: "
        if len(self.timestamp_list) == 2:
            output += f"{str(self.timestamp_list[0])} -> {str(self.timestamp_list[1] - dt.timedelta(days = 1))}"
        else:
            output += str(self.timestamp_list[0])
        print(output)

    def getTimestamp(self):
        print("**************************\n"
              "*  Wybierz zakres czasu  *\n"
              "**************************")

        timestamp_dict = {"1": "Dzisiaj",
                          "2": "Cały dany dzień",
                          "3": "Od - do",
                          "4": "Od - dzisiaj"}

        for key, value in timestamp_dict.items():
            print(key + ". " + value)

        while True:
            try:
                timestamp_choice = int(input("Wybór: "))
                print(f"Twój wybór: {timestamp_choice}. {timestamp_dict[str(timestamp_choice)]}. Kontynuować? (T/N)")
                ask_continue = input("Odpowiedź: ").strip().upper()

                match ask_continue:
                    case "N":
                        print("Wybierz ponownie")
                        continue
                    case "T":
                        if 1 <= timestamp_choice <= 4:
                            return timestamp_choice
                    case _:
                        raise ValueError

            except ValueError:
                print("Błędna wartość.\n")
                continue

    def setTimestamp(self):
        match self.getTimestamp():
            case 1:  # dzisiaj
                timestamp = self.current_date
                self.timestamp_list.append(timestamp)

            case 2:  # konkretny dzień
                timestamp = self.setDate()
                self.timestamp_list.append(timestamp)

            case 3:  # od - do
                print("Podaj datę OD:")
                timestamp_from = self.setDate()
                self.timestamp_list.append(timestamp_from)

                print("Podaj datę DO:")
                timestamp_to = self.setDate()
                timestamp_to = timestamp_to + dt.timedelta(days = 1)
                self.timestamp_list.append(timestamp_to)

            case 4:  # od - dzisiaj
                print("Podaj datę OD:")
                timestamp_from = self.setDate()
                self.timestamp_list.append(timestamp_from)

                timestamp_to = self.current_date + dt.timedelta(days = 1)
                self.timestamp_list.append(timestamp_to)

    # def convertToDatetime(self):
    #     return dt.datetime(self.year, self.month, self.day)
    #                                  # self.hours,
    #                                  # self.minutes,
    #                                  # self.seconds)

    def setDay(self):
        while True:
            try:
                day = int(input("Podaj dzień: "))
                if self.checkDay(day):
                    self.day = day
                    break
            except ValueError:
                print("Dzień powinien być liczbą")

    def checkDay(self, day):
        try:
            dt.datetime(self.year, self.month, day)
            return True
        except ValueError:
            print(f"Nieprawidłowy dzień {day} dla miesiąca {self.month} i roku {self.year}")
            return False

    def setMonth(self):
        while True:
            try:
                month = int(input("Podaj miesiąc: "))
                if 1 <= month <= 12:
                    self.month = month
                    if not self.checkDay(self.day):
                        self.setDay()
                    break
                else:
                    print("Miesiąc powinien być między 1 a 12")
            except ValueError:
                print("Miesiąc powinien być liczbą")

    def setYear(self):
        current_year = dt.datetime.today().date().year
        while True:
            try:
                year = int(input("Podaj rok: "))
                if 2000 <= year <= current_year:
                    self.year = year
                    if not self.checkDay(self.day):
                        self.setDay()
                    break
                else:
                    print("Podaj prawidłowy rok")

            except ValueError:
                print("Rok powinien być liczbą")

    # def setSeconds(self):
    #     while True:
    #         try:
    #             seconds = int(input("Podaj sekundy: "))
    #             if 0 <= seconds <= 59:
    #                 self.seconds = seconds
    #                 break
    #         except ValueError:
    #             print("Sekundy powinny być liczbami w zakresie 0-59")
    #
    # def setMinutes(self):
    #     while True:
    #         try:
    #             minutes = int(input("Podaj minuty: "))
    #             if 0 <= minutes <= 59:
    #                 self.minutes = minutes
    #                 break
    #         except ValueError:
    #             print("Minuty powinny być liczbami w zakresie 0-59")
    #
    # def setHour(self):
    #     while True:
    #         try:
    #             hours = int(input("Podaj godzinę: "))
    #             if 0 <= hours <= 23:
    #                 self.hours = hours
    #                 break
    #         except ValueError:
    #             print("Godziny powinny być liczbami w zakresie 0-23")

    def setDate(self):
        self.setDay()
        self.setMonth()
        self.setYear()
        self.askValidDatetime()
        return dt.datetime(self.year, self.month, self.day).date()

    def askValidDatetime(self):
        print(f"Czy data {self} jest poprawna? (T/N)")
        validChoice = input("Odpowiedź: ").strip().upper()
        if validChoice == "N":
            self.changeDateTime()

    def changeDateTime(self):
        while True:
            try:
                choice = int(input("Co chcesz zmienić:\n"
                               "1. Dzień\n"
                               "2. Miesiąc\n"
                               "3. Rok\n"
                               # "4. Godzinę\n"
                               # "5. Minutę\n"
                               # "6. Sekundę\n"
                               "0. Wyjdź\n"
                               "Wybór: "))
                match choice:
                    case 1:
                        self.setDay()
                    case 2:
                        self.setMonth()
                    case 3:
                        self.setYear()
                    case 0:
                        break
                    case _:
                        print("Błędny numer\n")
                print(f"** {self} **\n")
            except ValueError:
                print("Wybierz 0-3\n")

class Config:
    address: str
    port: int
    mailbox: str
    user_file_location: str

    def __init__(self):
        self.address = ""
        self.port = 0
        self.mailbox = ""
        self.user_file_location = ""

    def __str__(self):
        return (f"Adres: {self.address},\n"
                f"Port: {self.port},\n"
                f"Skrzynka: {self.mailbox},\n"
                f"Lokalizacja pliku z użytkownikami: {self.user_file_location}\n")

    def saveParameters(self, mail_info: 'MailInfo', user_file:'UserFile', mailbox:'Mailbox'):
        self.address = mail_info.address
        self.port = mail_info.port
        self.mailbox = mailbox.mailbox_name
        self.user_file_location = user_file.file_location

    def askForSave(self):
        while True:
            choice = input("Czy zapisać:\n"
                           "     - Adres i port\n"
                           "     - Wybrany plik z użytkownikami\n"
                           "     - Wybraną skrzynkę\n"
                           "T/N: ").upper()
            match choice:
                case "T":
                    self.saveConfig()
                    break
                case "N":
                    break
                case _:
                    print("Błędny wybór. Spróbuj ponownie.")

    def saveConfig(self, ):
        Tk().withdraw()
        print("**  Wybierz lokalizację zapisu  **")
        config_save = asksaveasfilename(defaultextension=".json",
                                        filetypes=(("Json File", "*.json"),))
        config_data = {
            'address': self.address,
            'port': self.port,
            'mailbox': self.mailbox,
            'user_file_location': self.user_file_location
        }

        with open(config_save, 'w') as file:
            json.dump(config_data, file)
        print(f"**  Konfiguracja zapisana  **\n"
              f"{config_save}")

    def loadConfigFromFile(self,config_path):
        with open(config_path) as file:
            conf = json.load(file)
        for key, value in conf.items():
            if hasattr(self,key): setattr(self,key,value)

    def loadConfig(self):
        Tk().withdraw()
        config_path = askopenfilename(title="Wybierz plik z zapisaną konfiguracją",
                                      filetypes=(("Json File", "*.json"),))
        self.loadConfigFromFile(config_path)

    # def askForChange(self):
    #     choice = input("**  Czy chcesz coś zmienić?(T/N)  **").strip().upper()
    #     match choice:
    #         case "T":
    #             self.changeParams()
    #         case "N":
    #             return
    #         case _:
    #             print("Błędny odpowiedź.")
    #
    # def changeParams(self):
    #     print("Co chcesz zmienić:\n"
    #           "1. Dane pocztowe\n"
    #           "2. Skrzynkę\n"
    #           "3. Plik z użytkownikami\n")

class UserCredentials:
    username: str
    password: str
    def __init__(self):
        self.username = ""
        self.password = ""

    def getCredentials(self):
        self.loginText()
        while True:
            try:
                self.getUsername()
                self.getPassword()
                break
            except Exception as e:
                print(f"\n{e}")

    def loginText(self):
        print("*********************\n"
              "*    Zaloguj się    *\n"
              "*********************")

    def getUsername(self):
        username = input("Nazwa użytkownika: ").strip()
        self.validateUsername(username)
        self.username = username

    def validateUsername(self, username):
        if not username:
            raise ValueError("Nazwa użytkownika nie może być pusta")
        else:
            return 1

    def getPassword(self):
        password = getpass.getpass().strip()
        self.validatePassword(password)
        self.password = password

    def validatePassword(self, password):
        if not password:
            raise ValueError("Hasło nie może być puste")
        else:
            return 1

    def getInput(self):
        self.loginText()
        while True:
            try:
                self.getUsername()
                self.getPassword()
                break
            except Exception as e:
                print(e)

class MailInfo:
    address: str
    port: int

    def __init__(self):
        self.address = ""
        self.port = 0

    def mailText(self):
        print("******************************\n"
              "*    Podaj dane pocztowe:    *\n"
              "******************************")

    def getFromConfig(self, config:Config):
        self.address = config.address
        self.port = config.port

    def getAddress(self):
        while True:
            try:
                address = input("Adres: ").strip()
                self.validateAddress(address)
                self.address = address
                break
            except Exception as e:
                print(f"{e}\n")

    def validateAddress(self, address):
        if address == "":
            raise ValueError("Adres nie może być pusty")
        return 1

    def getPort(self):
        while True:
            try:
                port = input("Port dla IMAP-SSL (domyślnie 993): ").strip()
                self.validatePort(port)
                break
            except Exception as e:
                print(f"\n{e}")
                continue

    def validatePort(self, port):
        if not port:
            self.port = 993
        elif not port.isdigit():
            raise ValueError("Port musi mieć wartość numeryczną")
        elif not (1 <= int(port) <= 65535):
            raise ValueError("Port musi być w zakresie 1–65535")
        else:
            self.port = int(port)
        return 1

    def getInput(self):
        self.mailText()
        self.getAddress()
        self.getPort()

class Connection:
    connect_host = None

    def __init__(self, mail_info: MailInfo):
        self.mail_info = mail_info

    def printConnecting(self):
        print("*****************\n"
              "*  Łączenie...  *\n"
              "*****************")

    def printConnected(self):
        print("******************\n"
              "*  Połączono...  *\n"
              "******************")

    def connect(self):
        exit_flag = 0
        while True:
            try:
                if exit_flag == 3:
                    print("** Zamykanie programu  **")
                    exit()
                self.printConnecting()
                time.sleep(2)
                print(self.mail_info.address, self.mail_info.port)
                self.connect_host = imaplib.IMAP4_SSL(self.mail_info.address, self.mail_info.port)
                self.printConnected()
                time.sleep(1)
                break

            except socket.gaierror:
                print("\nBłędny adres!\n")
                self.mail_info.getInput()
                exit_flag += 1
                continue

            except TimeoutError as te:
                print(f"Przekroczono limit czasu połączenia. Otrzymano błędny port lub usługa jest chwilowo niedostępna")
                exit()

            except OSError:
                print("\nBłędny adres!\n")
                self.mail_info.getInput()
                exit_flag += 1
                continue

            except Exception as e:
                print(f"\n{e}")
                exit()

    def login(self, user_credentials:UserCredentials):
        # username = ""
        # password = ""
        while True:
            try:
                self.connect_host.login(user_credentials.username, user_credentials.password)
                # self.connect_host.login(username, password)
                break

            except imaplib.IMAP4.error:
                print("\nBłąd logowania!\n")
                user_credentials.getCredentials()
                continue

            except Exception as e:
                print(f"\n{e}")


class Mailbox:
    mailbox_name: str
    all_mailboxes: list

    def __init__(self, connection: Connection):
        self.connection = connection
        self.mailbox_name = ""
        self.all_mailboxes = []
        self.mailboxChoice = ""

    def getFromConfig(self,config:Config):
        self.mailbox_name = config.mailbox
        self.connection.connect_host.select(self.mailbox_name)

    def getAllMailboxes(self):
        for i in (self.connection.connect_host.list()[1]):
            if not b"doveco" in i:
                self.all_mailboxes.append(str(i).split(".")[1][2:-1])
        # self.allMailboxes.remove('doveco')

    def printAllMailboxes(self):
        # mailboxes = {}
        for num, item in enumerate(self.all_mailboxes, start=1):
            # mailboxes[str(num)] = item
            print(f"{num}. {item}")

    def getMailboxChoice(self):
        while True:
            try:
                chosen_mailbox_number = int(input("Podaj numer: "))
                if 1 <= chosen_mailbox_number <= len(self.all_mailboxes):
                    if not self.askValidMailbox(self.all_mailboxes[chosen_mailbox_number-1]):
                        continue
                    break
                else:
                    print("Błędna odpowiedź. Spróbuj ponownie.")
                    continue
            except ValueError:
                print("Błędna odpowiedź. Spróbuj ponownie.")
                continue
            except Exception as e:
                print(e)

    def askValidMailbox(self,mailbox):
        while True:
            print(f"Wybrana skrzynka: {mailbox}")
            choice = input("Kontynuować? (T/N): ").strip().upper()
            match choice:
                case "T":
                    self.mailbox_name = mailbox
                    return 1
                case "N":
                    return 0
                case _:
                    print("Błędna odpowiedź")
                    continue

    def mailboxText(self):
        print("*************************\n"
              "*    Wybierz katalog    *\n"
              "*************************")

    def mailboxSelect(self):
        self.mailboxText()
        self.getAllMailboxes()
        self.printAllMailboxes()
        self.getMailboxChoice()

        self.connection.connect_host.select(self.mailbox_name)

class UserFile:
    file_location: str
    users_list: list
    users_class_list: list

    def __init__(self):
        self.file_location = ""
        self.users_list = []
        self.users_class_list = []

    def user_fileText(self):
        print("**************************************\n"
              "*    Wybierz plik z użytkownikami    *\n"
              "**************************************")

    def getFromConfig(self, config:Config):
        self.file_location = config.user_file_location

    def getUserFileLocation(self):
        self.user_fileText()
        Tk().withdraw()
        failed_file_attempts = 0
        while True:
            try:
                temp_file_location = askopenfilename(title="Wybierz plik Excel z użytkownikami",
                                                     filetypes=[("Excel files", "*.xlsx *.xls")])

                if temp_file_location == "" and failed_file_attempts < 2:
                    print("Nie wybrano pliku. Spróbuj ponownie.")
                    failed_file_attempts += 1
                    continue

                elif failed_file_attempts == 2:
                    raise FileNotFoundError

                if not self.askValidFile(temp_file_location):
                    continue

                self.file_location = temp_file_location

                break

            except FileNotFoundError:
                while True:
                    choice = input("Nie wybrano pliku. Przerwać program? (T/N):").strip().upper()
                    match choice:
                        case "T":
                            quit()
                        case "N":
                            failed_file_attempts = 0
                            self.user_fileText()
                            break
                        case _:
                            print("Błędna odpowiedź")
                continue

    def askValidFile(self,temp_file_location):
        print(f"Czy wybrany plik: {temp_file_location} jest poprawny?")
        valid_choice = input("(T/N): ").strip().upper()
        if valid_choice == "N":
            print("Wybierz ponownie.")
            return 0
        return 1

    # def checkExtension(self, user_file_path):
    #     if user_file_path.endswith('.xlsx'):
    #         print("JEST TO PLIK XLSX")
    #         return 1
    #     raise ValueError("Błędny plik. Spróbuj ponownie.")

    def convertData(self):
        while True:
            try:
                users = pd.read_excel(self.file_location)

                #axis 0 = rows
                #axis 1 = columns

                users = users.dropna(axis=0,how="all")

                users = users.dropna(axis=1,how="all")

                users = users.reset_index(drop=True)

                if "@" not in str(users.iloc[0]).lower():
                    users.columns = users.iloc[0]
                    users = users[1:].reset_index(drop=True)

                column_name = self.findEmailColumn(users)

                self.users_list = users[column_name].unique().tolist()
                self.convertUsers()
                break

            except InvalidUserFile:
                print("**  Błąd. W pliku nie znaleziono adresów email  **")
                self.getUserFileLocation()

    def validateUsername(self, username):
        if username == '':
            return False
        return True

    def convertUsers(self):
        i = 0
        for user in self.users_list:
            user = str(user).strip()
            if not self.validateUsername(user):
                continue
            self.users_class_list.append(User(user))
            print(self.users_class_list[i].username)
            i += 1

    def findEmailColumn(self, data: pd.DataFrame):
        for column_name in data.columns:
            for item in data[column_name].head(1):
                if "@stud.prz.edu.pl" in item:
                    return column_name

        raise InvalidUserFile()


class InvalidUserFile(Exception):
    pass

class MailData:
    connection = None
    users_list = None
    timestamp_list = None
    query = None
    save_path = None

    def __init__(self,connection: Connection, user_file: UserFile, timestamp: Time):
        self.connection = connection.connect_host
        self.users_list = user_file.users_class_list
        self.timestamp_list = timestamp.timestamp_list
        self.query = []
        self.save_path = ""

    def makeQuery(self):
        quotes = ["ON","SINCE","BEFORE"]
        index = 0
        for timestamp in self.timestamp_list:
            if len(self.timestamp_list) == 1:
                self.query = [quotes[index], timestamp.strftime("%d-%b-%Y")]
                break
            self.query += [quotes[index+1], timestamp.strftime("%d-%b-%Y")]
            index += 1
        print(self.query)

    def getMessage(self):
        self.makeQuery()
        for user in self.users_list:
            status, data = self.connection.search(None,'From',f'"{user.username}"', *self.query)
            print(data)
            message_id_list = data[0].split()
            self.getAttachments(message_id_list, user.username)
            time.sleep(2)

    def getAttachments(self, message_id_list, username):
        for message in message_id_list:
            status, message_data = self.connection.fetch(message,"(RFC822)")
            message_content: EmailMessage = BytesParser(policy=policy.default).parsebytes(message_data[0][1])

            for attachment in message_content.iter_attachments():
                filename = attachment.get_filename()
                payload = attachment.get_payload(decode=True)
                print(f"Znaleziono: {filename}")
                self.saveAttachments(payload,username,filename)

    def saveAttachments(self, payload, username,filename):
        full_save_path = f"{self.save_path}/{username}"
        os.makedirs(full_save_path, exist_ok=True)
        try:
            if os.path.exists(os.path.join(full_save_path, filename)):
                print(f"Plik {filename} użytkownika {username} już istnieje.")
            else:
                with open(f"{full_save_path}/{filename}","wb") as f:
                    f.write(payload)
            print(f"{full_save_path}")

        except Exception as e:
            print(f"Błąd zapisu pliku. {e}")

    def saveMessage(self):
        print("******************************************\n"
              "*    Wybierz lokalizację do zapisania    *\n"
              "******************************************\n"
              "**  Pliki zostaną zapisane w odpowiednich folderach w podanej lokalizacji  **")

    def getSaveLocation(self):
        Tk().withdraw()
        self.saveMessage()
        failed_file_attempts = 0
        while True:
            try:
                temp_save_path = askdirectory(title="Wybierz folder do zapisu załączników")

                if temp_save_path == "" and failed_file_attempts < 2:
                    print("Nie wybrano pliku. Spróbuj ponownie.")
                    failed_file_attempts += 1
                    continue

                elif failed_file_attempts == 2:
                    raise NotADirectoryError

                if not self.askValidDir(temp_save_path):
                    continue

                self.save_path = temp_save_path
                break

            except NotADirectoryError:
                while True:
                    choice = input("Nie wybrano lokalizacji. Przerwać program? (T/N):").strip().upper()
                    match choice:
                        case "T":
                            quit()
                        case "N":
                            failed_file_attempts = 0
                            self.saveMessage()
                            break
                        case _:
                            print("Błędna odpowiedź")
                continue

    def askValidDir(self,temp_dir_path):
        print(f"Czy wybrana lokalizacja: {temp_dir_path} jest poprawna? (T/N)")
        valid_choice = input("Odpowiedź: ").strip().upper()
        if valid_choice == "N":
            print("Wybierz ponownie.")
            return 0
        return 1

if __name__ == "__main__":
    app = App()
    app.run()
