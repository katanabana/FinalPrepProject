import os.path
import sys

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

import menus
from db_pyqt import widgets
from db_pyqt.utilities import connect


class MainWindow(widgets.Widget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Не навреди')
        self.setWindowIcon(QIcon(os.path.join('data', 'icon.ico')))
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.lt.addWidget(self.stacked_widget)
        self.to_login_menu()

    def check_captcha(self):
        if self.login.captcha.input.text() == self.login.captcha.value:
            for widget in self.login.login_widgets:
                widget.show()
            self.login.error.hide()
            self.login.captcha.hide()
            self.login.errors = 0
        else:
            self.login.captcha.hide()
            timer = widgets.Timer(self.to_login_menu)
            self.login.lt.addWidget(QtWidgets.QLabel(f'Доступ заблокирован'))
            self.login.lt.addWidget(timer)

    def try_to_enter(self):
        user = self.login.try_to_enter()
        if user:
            menu = menus.User.get_by_type(user)
            connect(menu.exit.clicked, self.to_login_menu)
            menu.timer.callables.append(self.to_login_menu)
            self.change_stacked_widget(menu)

    def change_stacked_widget(self, widget):
        if self.stacked_widget.currentWidget():
            self.stacked_widget.currentWidget().deleteLater()
        self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)

    def to_login_menu(self):
        self.login = menus.Login()
        self.change_stacked_widget(self.login)
        connect(self.login.enter.clicked, self.try_to_enter)
        connect(self.login.captcha.check.clicked, self.check_captcha)


def except_hook(exc, val, trace): return sys.__excepthook__(exc, val, trace)


def main():
    app = QtWidgets.QApplication([])
    font = app.font()
    font.setWeight(int(font.weight() * 1.5))
    font.setPointSize(int(font.pointSize() * 1.5))
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
