import datetime

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout

import check
import database

import order
from db_pyqt import widgets
from db_pyqt.forms import View, ViewToEdit, Dialog, Form, Choose
from db_pyqt.table import Table
from db_pyqt.widgets import Captcha
from report import Report


class Login(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.errors = 0
        self.password = QtWidgets.QLineEdit()
        self.show_password = QtWidgets.QCheckBox('Показать')
        self.login = QtWidgets.QLineEdit()
        self.enter = QtWidgets.QPushButton('Войти')
        self.error = QtWidgets.QLabel('Неверные данные')
        self.captcha = Captcha()

        self.password.setPlaceholderText('Пароль')
        self.login.setPlaceholderText('Логин')
        self.error.hide()

        self.show_password.stateChanged.connect(self.update_password_visibility)
        self.update_password_visibility()

        self.password_lt = QtWidgets.QHBoxLayout()
        self.password_lt.addWidget(self.password)
        self.password_lt.addWidget(self.show_password)
        self.layout().addLayout(self.password_lt)
        self.layout().addWidget(self.login)
        self.layout().addWidget(self.error)
        self.layout().addWidget(self.enter)

        #technician
        # password = '4tzqHdkqzo4'
        # login = 'chacking0'

        # bookkeeper
        # password = 'Cbmj3Yi'
        # login = 'srobken8'

        # self.password.setText(password)
        # self.login.setText(login)

    def update_password_visibility(self):
        mode = QtWidgets.QLineEdit().echoMode() if self.show_password.isChecked() else QtWidgets.QLineEdit.Password
        self.password.setEchoMode(mode)

    def try_to_enter(self):
        password = self.password.text()
        login = self.login.text()
        user = Table('User').get(Login=login, Password=password).first()
        if user is None:
            self.error.show()
            self.errors += 1
            if self.errors >= 2:
                for widget in self.login_widgets:
                    widget.hide()
                self.layout().addWidget(self.captcha)
                pass
        else:
            self.error.hide()
        return user

    @property
    def login_widgets(self):
        return [self.password, self.enter, self.login, self.show_password, self.error]


class Menu(widgets.Widget):
    def __init__(self, user):
        super().__init__()
        self.user_info = QtWidgets.QHBoxLayout()
        self.user_pfp = QtWidgets.QLabel()
        self.user_name = QtWidgets.QLabel(user.Name)
        self.exit = QtWidgets.QPushButton('Выйти')
        self.timer = widgets.Timer(self.show_warning)
        self.start_time = datetime.datetime.now()
        self.user_pfp.setPixmap(QPixmap(f'data\\pfp\\{user.TypeId}.png').scaled(70, 70))
        self.user_pfp.setMaximumSize(70, 70)
        for widget in [self.exit, self.timer, self.user_name, self.user_pfp]:
            self.user_info.addWidget(widget, alignment=Qt.AlignTop)
        for index in [1, 3]:
            self.user_info.insertWidget(index, QWidget(), 1)
        self.layout().addLayout(self.user_info)

    def show_warning(self):
        dialog = widgets.Dialog(self, 'Предупреждение')
        dialog.layout().addWidget(QtWidgets.QLabel(f'Осталось {self.timer.seconds} секунд'))


class User(Menu):
    def __init__(self, user):
        super().__init__(user)
        self.services = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.services)
        for service_to_user in Table('ServiceToUser').get(UserId=user.Id):
            service = Table('Service').get(Id=service_to_user.ServiceId).first()
            self.add_service(service.Name)
        self.add_service_dialog('Формировать отчет', Report)

    def add_service(self, name, connect_to=None):
        button = QtWidgets.QPushButton(name)
        if connect_to is not None:
            button.clicked.connect(connect_to)
        self.services.addWidget(button)
        return button

    def add_service_dialog(self, name, get_widget):
        self.add_service(name, lambda: widgets.ScrollableDialog(self, name, get_widget()).show())

    @staticmethod
    def get_by_type(user):
        user_type = Table('UserType').get(Id=user.TypeId).first()
        return globals()[user_type.Name](user)


class EditClientMode(ViewToEdit):
    def edit(self):
        edit_mode = super().edit()
        if edit_mode is not None:
            for column_name in ['Email', 'Phone']:
                edit_mode.inputs[column_name].widget.setDisabled(True)


class Technician(User):
    def __init__(self, user):
        super().__init__(user)
        self.add_service('Формировать заказ', lambda: order.CodeDialog(self).show())
        self.add_service_dialog('Редактировать информацию о клиенте', lambda: EditClientMode('Client'))


class Administrator(User):
    def __init__(self, user):
        super().__init__(user)
        self.add_service_dialog('История входа', lambda: View('LastEnter'))


class Bookkeeper(User):
    def __init__(self, user):
        super().__init__(user)
        self.add_service('Формировать счет на услуги предприятию', lambda: check.LegalEntityCheck(self))
        self.add_service('Формировать счет на услуги частному лицу', lambda: check.PhysicalEntityCheck(self))
