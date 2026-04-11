import os
import datetime
import datetime as dt
import patoolib
from email.message import EmailMessage
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import poplib
from tkinter.messagebox import showwarning, showerror
from logic.models import FileSavePath, Filter, User
from logic.connection import Connection

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

        match self.date_choice:
            case "one_day":
                self.query = [quotes[0], self.date_list[0].strftime("%d-%b-%Y")]

            case "from_to":
                query_date_end = self.date_list[1] + dt.timedelta(days=1)
                self.query = [quotes[1], self.date_list[0].strftime("%d-%b-%Y"),
                              quotes[2], query_date_end.strftime("%d-%b-%Y")]
            case "from":
                self.query = [quotes[1], self.date_list[0].strftime("%d-%b-%Y")]

            case "to":
                query_date = self.date_list[0] + dt.timedelta(days=1)
                self.query = [quotes[2], query_date.strftime("%d-%b-%Y")]

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
                showwarning("Ostrzeżenie",f"Błąd przy wiadomości {i}: {e}")
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
        self.connection = connection.connect_host
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
            # print(f"Znaleziono: {filename}")

            if payload is None or filename is None:
                payload, filename = self.extractPayload(attachment)

            if payload is None:
                display_name = filename or "nieznana nazwa"
                showwarning("Ostrzeżenie", f"Pominięto załącznik '{display_name}': nie można odczytać zawartości.")
                continue
            if not filename:
                showwarning("Ostrzeżenie", "Pominięto załącznik bez nazwy pliku.")
                continue

            self.saveAttachments(payload, filename, full_save_path, user)
            if self.ask_log_file:
                self.add_log(message, user, filename, full_save_path)

    def saveAttachments(self, payload, filename, full_save_path, user):
        file_path = os.path.join(full_save_path, filename)
        try:
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
            showerror("Błąd",f"Błąd zapisu pliku. {str(e)}")

    def extractPayload(self, attachment):
        if attachment.is_multipart():
            for part in attachment.iter_parts():
                payload, filename = self.extractPayload(part)
                if payload is not None:
                    return payload, filename
            return None, None
        return attachment.get_payload(decode=True), attachment.get_filename()

    def add_log(self, message, user, filename, full_save_path):

        date = str(parsedate_to_datetime(message.get("Date")).date())
        user_name = f"{user.username}"
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
            log_save_loc = f"dziennik_{today.strftime('%d-%m-%Y_%H-%M-%S')}.txt"

        with open(log_save_loc, "w", encoding="utf-8") as f:
            f.write(f"***** Data utworzenia dziennika: {str(today.strftime('%d-%m-%Y  %H:%M:%S'))} *****\n")
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