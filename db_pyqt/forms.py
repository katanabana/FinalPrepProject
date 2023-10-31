from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

from database import DB
from db_pyqt.inputs import Inputs, Input, UniqueInput
from db_pyqt.table import Table, SearchableTableWidget, TableWidget, Selection
from db_pyqt.utilities import get_primary_and_foreign_key_columns, connect, camel_to_normal
from db_pyqt.widgets import LeftAlignedLayout, ScrollableDialog


class Element(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel(self.title)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.label)
        self.sub_elements_to_initial_validates = {}

    @property
    def title(self):
        return ''

    def connect_validation(self, sub_element):
        self.sub_elements_to_initial_validates[sub_element] = sub_element.validate
        sub_element.validate = self.validate

    def disconnect_validation(self, sub_element):
        sub_element.validate = self.sub_elements_to_initial_validates[sub_element]
        self.sub_elements_to_initial_validates.pop(sub_element)

    def _validate(self):
        for element, validate in self.sub_elements_to_initial_validates.items():
            if not validate():
                return False
        return True

    @property
    def validate(self):
        return self._validate

    @validate.setter
    def validate(self, value):
        self._validate = value
        for element in self.sub_elements_to_initial_validates:
            element.validate = value


class Mode(Element):

    @property
    def table(self):
        return None

    @property
    def title(self):
        return camel_to_normal(self.__class__.__name__ + self.table.name)

    def perform(self):
        pass


class Edit(Mode):
    def __init__(self, instance, **column_names_to_inputs):
        self.instance = instance
        self.column_names_to_inputs = column_names_to_inputs
        super().__init__()

        self.inputs = Inputs()
        for column in self.table.native_columns:
            if column.name not in column_names_to_inputs:
                value = getattr(instance, column.name)
                if column.unique or column.primary_key:
                    input_ = UniqueInput(column, value)
                else:
                    input_ = Input(column)
                if value is not None:
                    input_.widget.setValue(value)
                self.inputs.add_input(input_)

        for column_name, dependency_input in column_names_to_inputs.items():
            column = getattr(self.table.declarative_meta, column_name)
            dependant_input = Input(column)
            self.inputs.add_input(dependant_input)
            dependant_input.widget.setDisabled(True)
            connect(
                dependency_input.widget.valueChanged,
                lambda: dependant_input.widget.setValue(dependency_input.widget.value())
            )
            dependant_input.widget.setValue(dependency_input.widget.value())
        self.dependencies = []
        for dependency in self.table.dependencies:
            primary, foreign = get_primary_and_foreign_key_columns(dependency)
            if foreign.name not in self.column_names_to_inputs:
                add_or_choose = AddOrChoose(primary.table.name)
                table_widget = add_or_choose.searchable_table_widget.table_widget
                foreign_key_value = getattr(self.instance, foreign.name)
                for index, instance in enumerate(table_widget.instances):
                    current_foreign = getattr(instance, primary.name)
                    if current_foreign == foreign_key_value:
                        table_widget.selectRow(index)
                        table_widget.update_selection()
                        add_or_choose.validate()
                        break
                self.dependencies.append(add_or_choose)

        self.layout().addWidget(self.inputs)
        for i in self.dependencies:
            self.layout().addWidget(i)

        for element in self.inputs.list + self.dependencies:
            self.connect_validation(element)

    @property
    def table(self):
        return Table(self.instance.__class__.__name__)

    def perform(self):
        self.inputs.set_values_for(self.instance)
        for relationship, dependency in zip(self.table.dependencies, self.dependencies):
            instance = dependency.selected_instance
            primary, foreign = get_primary_and_foreign_key_columns(relationship)
            value = getattr(instance, primary.name)
            setattr(self.instance, foreign.name, value)


class Add(Edit):
    def __init__(self, table_name, **column_names_to_inputs):
        super().__init__(Table(table_name).declarative_meta(), **column_names_to_inputs)
        self.dependants = []
        for dependant in self.table.dependants:
            primary, foreign = get_primary_and_foreign_key_columns(dependant)
            kwargs = {foreign.name: self.inputs[primary.name]}
            element = OptionallyAddMultipleInstancesOf(foreign.table.name, **kwargs)
            self.layout().addWidget(element)
            self.dependants.append(element)
            self.connect_validation(element)
        self.inputs.set_values_for(self.instance)
        DB.current_session.add(self.instance)

    def perform(self):
        super().perform()
        for dependant in self.dependants:
            dependant.perform()


class OptionallyAddMultipleInstancesOf(Mode):
    def __init__(self, table_name, **column_names_to_inputs):
        self.table_name = table_name
        self.column_names_to_inputs = column_names_to_inputs
        super().__init__()
        self.adds = []
        self.add_button = QPushButton('+')
        self.remove_button = QPushButton('-')
        self.add_button.clicked.connect(self.add)
        self.remove_button.clicked.connect(self.remove)
        self.layout().addLayout(LeftAlignedLayout(self.add_button, self.remove_button))

    def add(self):
        add = Add(self.table_name, **self.column_names_to_inputs)
        self.adds.append(add)
        index = self.layout().count() - 1
        self.layout().insertWidget(index, add)
        self.connect_validation(add)

    def remove(self):
        widget = self.adds.pop(-1)
        self.disconnect_validation(widget)
        widget.deleteLater()

    @property
    def table(self):
        return Table(self.table_name)


class Form(Element):
    def __init__(self, *modes: Mode):
        self.modes = modes
        super().__init__()
        self.label.hide()
        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit)
        self.modes = modes
        for mode in modes:
            self.layout().addWidget(mode)
            self.connect_validation(mode)
            mode.validate()
        self.layout().addLayout(LeftAlignedLayout(self.submit_button))

    @property
    def title(self):
        return ', '.join([mode.title for mode in self.modes])

    def submit(self):
        for mode in self.modes:
            mode.perform()
        DB.current_session.commit()

    def _validate(self):
        result = super()._validate()
        self.submit_button.setEnabled(result)
        return result


class Dialog(ScrollableDialog):
    def __init__(self, form, parent):
        super().__init__(parent, form.title, form)
        self.setModal(True)
        self.form = form
        self.form.submit_button.clicked.connect(self.close)
        self.show()

    def closeEvent(self, a0) -> None:
        DB.current_session.rollback()
        super().closeEvent(a0)


class View(Mode):
    def __init__(self, table_name):
        self.table_name = table_name
        super().__init__()
        self.searchable_table_widget = SearchableTableWidget(TableWidget(self.table))
        self.layout().addWidget(self.searchable_table_widget)

    @property
    def table(self):
        return Table(self.table_name)

    @property
    def selected_instance(self):
        instances = self.searchable_table_widget.table_widget.selected_instances
        if instances:
            return instances[0]


class Choose(View):
    def __init__(self, table_name):
        self.error = QLabel('No instance is selected')
        super().__init__(table_name)
        self.searchable_table_widget.table_widget.selection = Selection.single
        self.error.hide()
        self.layout().addWidget(self.error)

    def _validate(self):
        result = bool(self.selected_instance)
        self.error.setHidden(result)
        return result

    @property
    def validate(self):
        return self._validate

    @validate.setter
    def validate(self, value):
        self.searchable_table_widget.table_widget.clicked.connect(value)
        self._validate = value


class AddOrChoose(Choose):
    def __init__(self, table_name):
        super().__init__(table_name)
        self.add_button = QPushButton('Add')
        self.add_button.clicked.connect(self.show_add_dialog)
        self.layout().addLayout(LeftAlignedLayout(self.add_button))

    def show_add_dialog(self):
        Dialog(Form(Add(self.table_name)), self)


class ViewToEdit(View):
    def __init__(self, table_name):
        super().__init__(table_name)
        self.searchable_table_widget.table_widget.selection = Selection.single
        connect(self.searchable_table_widget.table_widget.clicked, self.edit)

    def edit(self):
        instance = self.selected_instance
        if instance:
            edit_mode = Edit(instance)
            form = Form(edit_mode)
            Dialog(form, self.searchable_table_widget)
            form.submit_button.clicked.connect(self.searchable_table_widget.table_widget.update)
            return edit_mode
