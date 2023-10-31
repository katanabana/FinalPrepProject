import os
import random

from PIL.ImageDraw import ImageDraw
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import func
from PIL import Image

import database
from db_pyqt import widgets
from db_pyqt.forms import Add, Form, Dialog
from db_pyqt.inputs import Input, UniqueInput
from db_pyqt.table import Table


class Bar:
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.color = color


class CodeDialog(widgets.Dialog):
    def __init__(self, parent):
        self.label = QtWidgets.QLabel('Введите код заказа:')
        self.code = UniqueInput(Table('Order').declarative_meta.Id)
        super().__init__(parent, 'Код заказа', self.label, self.code.widget, self.code.error)

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key_Return:
            self.form_bar_code()
            Dialog(Form(Add('Order', Id=self.code)), self.parent()).show()
            self.close()

    def form_bar_code(self):
        path = QFileDialog.getSaveFileName(self, filter='(*.pdf)')[0]
        if path:
            w, h = 200, 100
            img_file = 'test\\temp.png'

            im = Image.new('RGB', (w, h), "white")
            painter = ImageDraw(im)
            for x in range(w):
                color = random.choice(['black', 'white'])
                painter.line([(x, 0), (x, h - 10)], color)
            n = 13
            per_digit = w / n
            x = 0
            name = ''
            for _ in range(n):
                digit = random.randint(0, 9)
                name += str(digit)
                painter.text((x, h - 10), str(digit), 'black')
                x += per_digit
            im.save(img_file)
            canvas = Canvas(path)
            canvas.drawImage(img_file, 0, canvas._pagesize[1] - h)
            canvas.save()
            os.remove(img_file)
