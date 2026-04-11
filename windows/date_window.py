import datetime
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from models import Date
from windows.template_window import TemplateWindow
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
