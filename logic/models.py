import datetime
import re
import pandas as pd
from tkinter.messagebox import showwarning, showerror

class FileSavePath:
    def __init__(self):
        self.save_location = ""
        self.save_method = ""
        self.save_method_for_user = ""
        self.full_save_path = ""

        self.types = ["data_zapisu",
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

        self.example_user = None

    def setFromConfig(self, save_method):
        self.save_method = save_method
        if self.save_method != "" and self.example_user is not None:
            self.example_save_text = self.replaceText(save_method,
                                                      self.example_user.user_info,
                                                      self.example_receive_datetime)

    def replaceText(self, raw_text, message_user_info, message_datetime):
        replaced_text = raw_text
        message_datetime = message_datetime.copy()

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
    def __init__(self,user_dict, email_column):
        self.username = ""
        self.user_info = {}
        self.fillUserAttribs(user_dict, email_column)

    def fillUserAttribs(self,user_dict, email_column):
        self.username = user_dict.pop(email_column)
        self.user_info = user_dict
        return
class UserFile:
    def __init__(self):
        self.user_file_location = ""
        self.data = None
        self.users_list = []
        self.users_class_list: list[User] = []
        self.column_names = []
        self.email_column = ""

    def setUserFile(self, user_file_location):
        if user_file_location == "":
            raise ValueError("Nie wybrano pliku z użytkownikami")
        else:
            self.user_file_location = user_file_location
            return True

    def getDataFromFile(self):
        # axis 0 = rows
        # axis 1 = columns
        data = pd.read_excel(self.user_file_location)
        data = data.dropna(axis=0, how="all")
        data = data.dropna(axis=1, how="all")
        data = data.reset_index(drop=True)
        data = data.fillna("NONE")
        if len(data)<=0:
            raise ValueError("Plik z użytkownikami jest pusty")
        self.data = data
        self.normalizeColumns()
        return True

    def normalizeColumns(self):
        if "@" not in str(self.data.iloc[0]).lower() and not any(c.isdigit() for c in str(self.data.iloc[0]).lower()):
            self.data.columns = self.data.iloc[0]
            self.data = self.data[1:].reset_index(drop=True)
        self.column_names = self.removeSpecialCharacters(self.data.columns)
        self.column_names = [x.capitalize() for x in self.column_names]
        self.data.columns = self.column_names
        return True

    def getUsers(self):
        duplicated_users = self.findDuplicates(self.data, self.email_column)
        duplicated_users_list = ""
        for key, value in duplicated_users.items():
            duplicated_users_list += f"Wiersz: {str(key)}, Adres: {str(value)}\n"
        if len(duplicated_users_list) != 0:
            showwarning("Ostrzeżenie", f"W pliku znajdują się zduplikowane adresy email:\n{duplicated_users_list}")
        self.users_list = list(self.data.to_dict("index").values())

    def convertFileToUsers(self, user_file_location):
        self.setUserFile(user_file_location)
        self.getDataFromFile()
        if not self.email_column and not self.findEmailColumn():
            return False
        self.getUsers()
        self.convertUsers()
        return True

    def removeSpecialCharacters(self, column_names):
        characters = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
        temp_string = " ".join(column_names)
        temp_string = temp_string.translate(characters)
        fixed_columns = temp_string.split(" ")
        return fixed_columns

    def findDuplicates(self, users, column_name):
        users_list = users[column_name].tolist()
        duplicates_list = users.duplicated(subset=column_name)
        duplicated_users = {}
        for i, status in enumerate(duplicates_list):
            if status:
                duplicated_users[i + 2] = users_list[i]
        return duplicated_users

    def convertUsers(self):
        for user_from_file in self.users_list:
            if not self.fixValues(user_from_file):
                continue
            user_class = User(user_from_file, self.email_column)
            self.users_class_list.append(user_class)

    def fixValues(self, user):
        for key, value in user.items():
            user[key] = str(value).strip()
            try:
                if value != value: user[key] = ""
                if user[self.email_column] == "": return False
                user[key] = int(float(value))
            except Exception:
                continue
        return True

    def findEmailColumn(self):
        if self.column_names:
            for column_name in self.column_names:
                for item in self.data[column_name].head(5):
                    try:
                        if "@" in str(item) or column_name.lower() in ['email','e-mail']:
                            self.email_column = column_name
                            return True
                    except Exception:
                        continue
            return False
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