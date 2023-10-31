import datetime
import typing

from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTimeEdit, QDateEdit, QFormLayout, \
    QWidget, QLabel
from sqlalchemy import Column

from database import DB
from db_pyqt.table import Table
from db_pyqt.utilities import connect, camel_to_normal


class Validator(QValidator):
    def __init__(self, validation_func):
        super().__init__()
        self.validation_func = validation_func

    def validate(self, a0: str, a1: int) -> typing.Tuple['QValidator.State', str, int]:
        return self.validation_func(a0, a1)


class LineEdit(QLineEdit):
    valueChanged = QLineEdit.textChanged

    def value(self):
        return self.text()

    def setValue(self, value):
        self.setText(value)

    @property
    def validate(self):
        if self.validator() is None:
            return lambda string, pos: (QValidator.State.Acceptable, string, pos)
        return self.validator().validate

    @validate.setter
    def validate(self, value):
        self.setValidator(Validator(value))

    def valueFromText(self, text):
        return text


class DateTimeEdit(QDateTimeEdit):
    valueChanged = QDateTimeEdit.dateTimeChanged

    def value(self):
        return self.dateTime().toPyDateTime()

    def setValue(self, value):
        self.setDateTime(value)

    def valueFromText(self, text):
        return self.dateTimeFromText(text)


class TimeEdit(QTimeEdit):
    valueChanged = QTimeEdit.timeChanged

    def value(self):
        return self.time().toPyTime()

    def setValue(self, value):
        self.setTime(value)

    def valueFromText(self, text):
        return self.dateTimeFromText(text).time()


class DateEdit(QDateEdit):
    valueChanged = QDateEdit.dateChanged

    def value(self):
        return self.date().toPyDate()

    def setValue(self, value):
        self.setDate(value)

    def valueFromText(self, text):
        return self.dateTimeFromText(text).date()


def validate_int(a0: str, a1: int) -> typing.Tuple['QValidator.State', str, int]:
    if a0.isdigit() or a0 == '':
        state = QValidator.State.Acceptable
    else:
        state = QValidator.State.Invalid
    return state, a0, a1


class IntegerLineEdit(LineEdit):
    def __init__(self):
        super().__init__()
        self.validate = validate_int

    def setValue(self, value):
        super().setValue(str(value))


TYPES_TO_WIDGETS = {
    int: IntegerLineEdit,
    str: LineEdit,
    float: QDoubleSpinBox,
    datetime.datetime: DateTimeEdit,
    datetime.time: TimeEdit,
    datetime.date: DateEdit
}


class Input:
    def __init__(self, column: Column):
        self.column = column
        if self.python_type in TYPES_TO_WIDGETS:
            widget_type = TYPES_TO_WIDGETS[self.python_type]
        else:
            widget_type = LineEdit
        self.label = QLabel(camel_to_normal(column.name))
        self.widget = widget_type()
        self.error = QLabel('Incorrect input')
        self.error.hide()
        self.set_validate()

    def set_validate(self):

        old_validate = self.widget.validate

        def new_validate(string, pos):
            result = old_validate(string, pos)
            self.error.setHidden(result[0] == QValidator.State.Acceptable)
            self.validate()
            return result

        self.widget.validate = new_validate

    def validate(self):
        return self.error.isHidden()

    @property
    def python_type(self):
        return self.column.type.python_type

    @property
    def table(self):
        return Table(self.column.table.name)

    def connect_to(self, other):
        self.widget.setValue(other.widget.value())
        self.widget.setDisabled(True)
        connect(other.widget.valueChanged, lambda: self.widget.setValue(other.widget.value()))


class UniqueInput(Input):
    def __init__(self, column, *except_values):
        self.except_values = except_values
        super().__init__(column)

        if self.python_type is int:
            instances = self.table.get()
            maximum = max(map(lambda instance: getattr(instance, column.name), instances), default=-1)
            self.widget.setValue(maximum + 1)

    def set_validate(self):
        old_validate = self.widget.validate

        def new_validate(string, pos):
            result = old_validate(string, pos)
            if result[0] is QValidator.State.Acceptable:
                return self.validate_uniqueness(string, pos)
            return result

        self.widget.validate = new_validate

        super().set_validate()

    def validate_uniqueness(self, string, pos):
        state = QValidator.State.Acceptable
        value = self.widget.valueFromText(string)
        if (self.column.unique or self.column.primary_key) and value not in self.except_values:
            conditions = {self.column.name: value}
            instances = self.table.get(**conditions)
            if instances.first():
                state = QValidator.State.Intermediate
        return state, string, pos


class Inputs(QWidget):
    def __init__(self, *columns):
        super().__init__()
        self.columns = columns
        self.list = []
        self.setLayout(QFormLayout())
        for column in columns:
            self.add_input(Input(column))

    def set_values_for(self, instance):
        for input_ in self.list:
            setattr(instance, input_.column.name, input_.widget.value())

    def set_values_from(self, instance):
        for input_ in self.list:
            value = getattr(instance, input_.column.name)
            input_.widget.setValue(value)

    def add_input(self, input_):
        self.list.append(input_)
        self.layout().addRow(input_.label, input_.widget)
        self.layout().addWidget(input_.error)

    def __getitem__(self, item):
        for input_ in self.list:
            if input_.column.name == item:
                return input_
