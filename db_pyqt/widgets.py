import datetime
import tkinter
from typing import Any

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLayout, QVBoxLayout, QScrollArea, QWidget, QHBoxLayout, QLineEdit

import database


class Dialog(QtWidgets.QDialog):
    def __init__(self, parent, name, *widgets):
        super().__init__(parent)
        self.name = name
        self.setLayout(QVBoxLayout())
        for widget in widgets:
            self.layout().addWidget(widget)
        self.setWindowTitle(name)
        tk = tkinter.Tk()
        self.setMaximumSize(tk.winfo_screenwidth(), tk.winfo_screenheight())


class LeftAlignedLayout(QHBoxLayout):
    def __init__(self, *widgets):
        super().__init__()
        for widget in widgets:
            self.addWidget(widget)
        self.addStretch()


class ScrollableDialog(Dialog):
    def __init__(self, parent, title, *widgets):
        self.widgets = widgets
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        for sub_widget in widgets:
            widget.layout().addWidget(sub_widget)
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        super().__init__(parent, title, scroll)
        self.layout().setSizeConstraint(QLayout.SetMaximumSize)


class Timer(QtWidgets.QLabel):
    def __init__(self, *callables, seconds=60):
        super().__init__()
        self.callables = list(callables)
        self.index = 0
        self.timer = QTimer(self)
        self.start_time = datetime.datetime.now()
        self.timer.timeout.connect(self.update_time)
        self.seconds = seconds
        self.timer.start(1000)

    def update_time(self):
        total_seconds = self.seconds * len(self.callables)
        sum_time = datetime.timedelta(seconds=total_seconds)
        time_left = sum_time - (datetime.datetime.now() - self.start_time)
        self.setText(str(time_left).split('.')[0])
        if time_left.seconds % self.seconds == 0 and time_left.seconds != total_seconds:
            if self.index < len(self.callables):
                self.callables[self.index]()
                self.index += 1
            else:
                self.timer.stop()


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.lt = QtWidgets.QVBoxLayout(self)


class Captcha(Widget):
    def __init__(self):
        super().__init__()
        self.value = 'abc134'
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText('Введите капчу')
        self.img = QtWidgets.QLabel(self.value)
        self.check = QtWidgets.QPushButton('Проверить')
        self.lt.addWidget(self.img)
        self.lt.addWidget(self.input)
        self.lt.addWidget(self.check)


def resize(widget):
    size = widget.minimumSizeHint()
    widget.setMaximumSize(size)
    widget.setMinimumSize(size)


def fit_size(element):
    if not isinstance(element, QtWidgets.QLayout):
        resize(element)
    else:
        for child in element.children():
            fit_size(child)


class RadioMenuGroup(Widget):
    def __init__(self, **names_to_widgets):
        super().__init__()
        btn_lt = QtWidgets.QHBoxLayout()
        self.btn_group = QtWidgets.QButtonGroup()
        self.lt.addLayout(btn_lt)
        for label, widget in names_to_widgets.items():
            btn = QtWidgets.QRadioButton(label)
            btn_lt.addWidget(btn)
            self.btn_group.addButton(btn)
            btn.widget = widget
            btn.clicked.connect(self.update_state)
        btn_lt.addWidget(QtWidgets.QWidget(), 1)
        self.current = QtWidgets.QWidget()
        self.lt.addWidget(self.current)
        self.btn_group.buttons()[0].click()

    def update_state(self):
        for btn in self.btn_group.buttons():
            if btn.isChecked():
                self.lt.removeWidget(self.current)
                self.current.hide()
                self.current = btn.widget
                self.lt.addWidget(self.current)
                self.current.show()
                break

    @classmethod
    def get_named_by_classes(cls, *widgets):
        dct = {}
        for widget in widgets:
            dct[widget.__class__.__name__] = widget
        return cls(**dct)


class SmartScrollArea(QScrollArea):
    def __init__(self, *widgets):
        super().__init__()
        self.setWidget(QWidget())
        self.widget().setLayout(QVBoxLayout())
        for widget in widgets:
            self.widget().layout().addWidget(widget)
        self.setWidget(self.widget())
        self.setWidgetResizable(True)


class SubStringSearch(QWidget):
    def __init__(self, count, get_width=lambda column_index: Any, placeholder='All'):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.searches = []
        for i in range(count):
            search = QLineEdit()
            width = get_width(i)
            if width is not Any:
                search.setMaximumWidth(width)
                search.setMinimumWidth(width)
            self.searches.append(search)
            self.layout().addWidget(search)
            search.setPlaceholderText(placeholder)
        self.layout().addStretch()

    def connect_to(self, func=lambda: Any):
        for search in self.searches:
            search.textChanged.connect(func)

    def validate(self, values, registry_sensitive=False):
        if registry_sensitive:
            def matches(what, where):
                return what in where
        else:
            def matches(what, where):
                return what.lower() in where.lower()
        for search, value in zip(self.searches, values):
            if not matches(search.text(), str(value)):
                return False
        return True
