import json
import platform
import base64
import hashlib
import tkinter as tk
from cryptography.fernet import Fernet
from tkinter.messagebox import showinfo
from logic.models import Filter, UserCredentials

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
        self.save_config_choice = {}

    def clearConfig(self):
        for key in list(self.__dict__.keys()):
            if key == "port":
                self.__dict__[key] = 0
            elif key == "date_list":
                self.__dict__[key] = []
            elif key == "save_config_choice":
                self.__dict__[key] = {}
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
                raise ValueError(f"Nieznany klucz konfiguracji: '{key}'")

    def loadConfig(self, app):
        if self.user_file_location:
            success = app.user_file.convertFileToUsers(self.user_file_location)

            if not success and not app.user_file.email_column and app.selectEmailColumnWindow():
                success = app.user_file.convertFileToUsers(self.user_file_location)

            if success:
                app.user_file_text.config(text=self.user_file_location)
                app.app_state.state["user_file_set"] = True
                app.onUserFileLoaded()
            else:
                raise ValueError("Plik z użytkownikami zawiera błąd.")

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

        if self.save_location:
            app.file_save_path.save_location = self.save_location
            app.file_save_text.config(text=f"{self.save_location}/")
            app.app_state.state["save_loc_set"] = True

        if self.save_method and app.app_state.state["user_file_set"]:
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

        if self.save_config_choice:
            for key,status in self.save_config_choice.items():
                var = tk.BooleanVar(value=status)
                self.save_config_choice[key] = var
            app.save_config_choice = self.save_config_choice

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
            config_params["filter_text"] = app.subject_filter.filter_text if app.subject_filter else ""

        temp = app.save_config_choice.copy()
        for key, value in app.save_config_choice.items():
            temp[key] = value.get()

        config_params["save_config_choice"] = temp
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