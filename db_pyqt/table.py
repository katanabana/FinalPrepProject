from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from sqlalchemy import inspect, select
from sqlalchemy.orm import Relationship, RelationshipProperty

from database import DB
from .utilities import connect, camel_to_normal
from .widgets import SmartScrollArea, SubStringSearch


class Table:
    initialized = set()

    def __new__(cls, name, *args, **kwargs):
        for table in cls.initialized:
            if table.name == name:
                return table
        table = super().__new__(cls)
        cls.initialized.add(table)
        return table

    def __init__(self, name):
        self.declarative_meta = getattr(DB.base.classes, name)
        self.native_columns = []
        self.foreign_columns = []
        self.joins = []

        for column in self.columns:
            if column.foreign_keys:
                for foreign_key in column.foreign_keys:
                    target_column = foreign_key.column
                    target_table = self.__class__(target_column.table.name)
                    self.foreign_columns.extend(target_table.recursive_columns)
                    self.joins.append([target_table.declarative_meta, target_column == column])
            else:
                self.native_columns.append(column)

    @property
    def name(self):
        return self.declarative_meta.__table__.name

    @property
    def relationships(self):
        return inspect(self.declarative_meta).relationships

    def get_relationships(self, relationship_type):
        return [i for i in self.relationships if type(i) is relationship_type]

    @property
    def dependencies(self):
        return self.get_relationships(Relationship)

    @property
    def dependants(self):
        return self.get_relationships(RelationshipProperty)

    def instances(self, count):
        query = DB.current_session.query(self.declarative_meta).select_from(self.declarative_meta)
        for join in self.joins:
            query = query.join(*join)
        query = query.limit(count)
        return query.all()

    def data(self, instances):
        for instance in instances:
            yield self.values(instance)

    def values(self, instance):
        values = []
        for column in self.native_columns:
            values.append(getattr(instance, column.name))
        for column in self.columns:
            for foreign_key in column.foreign_keys:
                value = getattr(instance, column.name)
                table = Table(foreign_key.column.table.name)
                sub_instance = table.get_by_primary_key(value)
                values.extend(table.values(sub_instance))
        return values

    def get_by_primary_key(self, value):
        return self.get(**{self.primary_key.name: value}).first()

    @property
    def columns(self):
        return self.declarative_meta.__table__.columns

    @property
    def recursive_columns(self):
        return self.native_columns + self.foreign_columns

    def recursive_column_names(self, translation_language=None):
        processors = []

        if len(set([column.table for column in self.recursive_columns])) > 1:
            processors.append(lambda column: column.table.name + column.name)
        else:
            processors.append(lambda column: column.name)

        processors.append(camel_to_normal)



        names = []
        for column in self.recursive_columns:
            result = column
            for processor in processors:
                result = processor(result)
            names.append(result)
        return names

    @property
    def primary_key(self):
        return inspect(self.declarative_meta).primary_key[0]

    def get(self, **conditions):
        query = select(self.declarative_meta)
        where = []
        for column_name, value in conditions.items():
            where.append(getattr(self.declarative_meta, column_name) == value)
        if where:
            query = query.where(*where)
        return DB.current_session.scalars(query)


class Selection:
    @staticmethod
    def none(rows, row):
        return []

    @staticmethod
    def single(rows, row):
        return [] if row in rows else [row]

    @staticmethod
    def multiple(rows, row):
        if row in rows:
            return [i for i in rows if i != row]
        return rows + [row]


class TableWidget(QTableWidget):
    def __init__(self, table: Table):
        super().__init__()

        self.table = table
        self.row_count = 10
        self.selection = Selection.none
        self.flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        self.selection_color = QColor(200, 250, 200)
        self.no_selection_color = QColor(255, 255, 255)
        self.start = 0
        self.selected_rows = []
        self.filter = lambda values: values
        self.translation_language = None
        self.labels = self.table.recursive_column_names(self.translation_language)
        self.update()

    def update(self):
        self.clicked.connect(self.update_selection)
        self.setColumnCount(len(self.labels))
        self.setHorizontalHeaderLabels(self.labels)
        self.verticalHeader().hide()
        self.clearContents()
        row_count = 0
        self.setRowCount(row_count)
        for i, instance in enumerate(self.table.instances(self.row_count)):
            values = self.table.values(instance)
            if self.filter(values):
                row_count += 1
                self.setRowCount(row_count)
                self.instances.append(instance)
                color = self.selection_color if i in self.selected_rows else self.no_selection_color
                for j, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(self.flags)
                    item.setBackground(color)
                    self.setItem(row_count - 1, j, item)
            if row_count == self.row_count:
                break
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.fix_size()

    def size_hint(self):
        height = self.horizontalHeader().height() + 2
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        width = 2
        for j in range(self.columnCount()):
            width += self.columnWidth(j)
        return width, height

    def fix_size(self):
        self.setMinimumSize(*self.size_hint())
        self.setMaximumSize(*self.size_hint())

    def update_selection(self):
        item = self.currentItem()
        if item is not None:
            self.selected_rows = self.selection(self.selected_rows, item.row())
            self.update()

    @property
    def instances(self):
        return self.table.instances(self.row_count)

    @property
    def selected_instances(self):
        return [self.instances[i] for i in self.selected_rows]


class SearchableTableWidget(SmartScrollArea):
    def __init__(self, table_widget):
        self.table_widget = table_widget
        self.search = SubStringSearch(table_widget.columnCount(), table_widget.columnWidth)
        super().__init__(self.search, table_widget)
        self.search.connect_to(self.perform_search)
        self.widget().layout().setSpacing(0)
        self.update_size()

    def update_size(self):
        size = self.widget().sizeHint()
        height = size.height() + self.verticalScrollBar().height()
        self.setMinimumHeight(height)
        self.setMinimumHeight(height)

    def perform_search(self):
        self.table_widget.update_items(self.search.validate)
        self.update_size()
