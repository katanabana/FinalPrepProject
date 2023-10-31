from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QLayout, QVBoxLayout, QHBoxLayout, QPushButton



def snake_to_spaced(text):
    return text.repace


def connect(signal: pyqtSignal, func, *args, **kwargs):
    signal.connect(lambda: func(*args, **kwargs))


def camel_to_normal(camel: str):
    normal = camel[0:1].lower()
    for character in camel[1:]:
        if character.isupper():
            normal += ' '
            character = character.lower()
        normal += character
    return normal.capitalize()


def get_primary_and_foreign_key_columns(relationship):
    foreign = list(relationship._user_defined_foreign_keys)[0]
    primary = list(foreign.foreign_keys)[0].column
    return primary, foreign
