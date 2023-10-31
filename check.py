import csv

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateTimeEdit, QFileDialog

from db_pyqt.forms import Choose, Dialog, Form
from pdf import Canvas


class Check(QWidget):
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.title = 'Формировать счет'
        self.start = QDateTimeEdit()
        self.end = QDateTimeEdit()
        QVBoxLayout(self)
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(self.start)
        time_range_layout.addWidget(self.end)
        self.layout().addLayout(time_range_layout)

    @property
    def data(self):
        services = []
        total_price = 0
        for service in self.services:
            services.append(f'{service.Name} {service.Price}')
            total_price += service.Price
        data = [
            f'период для оплаты: {self.start.text()}-{self.end.text()}',
            'список оказанных услуг и цен:' + '\n'.join(services),
            'стоимостью услуг общая: ' + str(total_price)
        ]
        return data

    def validate(self):
        return True

    def save_to_csv(self, path):
        with open(path, 'w+', encoding='utf-8') as file:
            writer = csv.writer(file)
            for line in self.data:
                writer.writerow([line])

    def save_to_pdf(self, path):
        canvas = Canvas(path)
        for i, line in enumerate(self.data):
            canvas.drawString(0, i * 20, line)
        canvas.save()

    def perform(self):
        filter_sting = 'pdf file (*.pdf);;csv file (*.csv)'
        path, _ = QFileDialog.getSaveFileName(self, self.title, filter=filter_sting)
        if path:
            extension = path.split('.')[-1]
            methods = {'csv': self.save_to_csv, 'pdf': self.save_to_pdf}
            methods[extension](path)


def get_services(client):
    services = []
    for order in client.order_collection:
        for service_to_order in order.servicetoorder_collection:
            services.append(service_to_order.service)
    return services


class EntityCheck(Choose):
    def __init__(self, name, table_name, parent):
        self.name = name
        super().__init__(table_name)
        self.setParent(parent)
        form = Form(self)
        form.submit_button.setText('Формировать')
        Dialog(form, parent)

    @property
    def services(self):
        return []

    def perform(self):
        Dialog(Form(Check(self.services)), self.parent())

    @property
    def title(self):
        return 'Формировать счет ' + self.name


class PhysicalEntityCheck(EntityCheck):
    def __init__(self, parent):
        super().__init__('клиенту', 'Client', parent)

    @property
    def services(self):
        return get_services(self.selected_instance)


class LegalEntityCheck(EntityCheck):
    def __init__(self, parent):
        super().__init__('предприятию', 'Insurance', parent)

    @property
    def services(self):
        return get_services(self.selected_instance.client)
