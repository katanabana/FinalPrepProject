from datetime import timedelta

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QDateEdit, QFileDialog, QHBoxLayout

from db_pyqt.table import Table
from pdf import Canvas


class Report(QWidget):
    def __init__(self):
        super().__init__()
        QVBoxLayout(self)

        self.button = QPushButton('Формировать')
        self.type_combobox = QComboBox()
        self.representation_combobox = QComboBox()
        self.start = QDateEdit()
        self.end = QDateEdit()

        self.type_combobox.addItem('Отчет по оказанным услугам')
        self.representation_combobox.addItems([
            'график', 'таблица', 'график и таблица'
        ])
        self.button.clicked.connect(self.form)

        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(self.start)
        time_range_layout.addWidget(self.end)
        self.layout().addLayout(time_range_layout)
        self.layout().addWidget(self.type_combobox)
        self.layout().addWidget(self.representation_combobox)
        self.layout().addWidget(self.button)

    def form(self):
        path, _ = QFileDialog.getSaveFileName(self, filter='(*.pdf)')
        if path:
            services = []
            clients_per_services = []
            clients = []
            results = []
            data = {
                'период': self.start.text() + '-' + self.end.text(),
                'количество оказанных услуг': len(services),
                'перечень услуг': '\n' + '\n'.join([service.name for service in services]),
                'количетсво клиентов': len(clients),
                'количество клиентов за день по каждой услуге': '\n' + '\n'.join(clients_per_services),
                'средний результат каждого заказа в день': '\n' + '\n'.join(results)
            }

            canvas = Canvas(path)

            representation_type = self.representation_combobox.currentText()
            if 'таблица' in representation_type:
                canvas.draw_table(data.items())
            if 'график' in representation_type:
                start_date, end_date = self.start.date().toPyDate(), self.end.date().toPyDate()
                days = (end_date - start_date).days
                x = np.arange(days)

                y_utilizations = np.zeros(days)
                for utilization in Table('Utilization').get():
                    for day in range(days):
                        if start_date <= utilization.StartDatetime.date() <= start_date + timedelta(days=day):
                            y_utilizations[day] += 1

                y_clients = np.zeros(days)
                for day in range(days):
                    client_ids = set()
                    for order in Table('Order').get():
                        if start_date <= order.CreationDate <= start_date + timedelta(days=day):
                            client_ids.add(order.ClientId)
                    y_clients[day] = len(client_ids)

                y_clients_per_day = np.zeros(days)
                for day in range(days):
                    client_ids = set()
                    for order in Table('Order').get():
                        if order.CreationDate == start_date + timedelta(days=day):
                            client_ids.add(order.ClientId)
                    y_clients_per_day[day] = len(client_ids)

                y_results = np.zeros(days)
                for day in range(days):
                    order_ids = set()
                    for utilization in Table('Utilization').get():
                        if utilization.StartDatetime.date() <= start_date + timedelta(days=day):
                            y_results[day] += 1
                            order_ids.add(utilization.ServiceToOrderId.OrderId)
                    y_results[day] = y_results[day] / len(order_ids)

                Y = [y_utilizations, y_clients, y_clients_per_day, y_results]
                print(Y)
                y_labels = [list(data)[i] for i in (1, 3, 4, 5)]

                canvas.draw_plot(x, Y, y_labels, 'Количество дней с начала промежутка ' + data['период'])
            canvas.save()
