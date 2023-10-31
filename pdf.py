import os

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from matplotlib import pyplot as plt

from data import fonts

FONT_NAME = 'FreeSans'

font_path = os.path.join(fonts.__path__[0], FONT_NAME + '.ttf')
pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))


class Canvas(canvas.Canvas):
    def __init__(self, path):
        super().__init__(path)
        self.setFont(FONT_NAME, 15)

    def draw_table(self, data, x=0, y=0):
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.fontName = FONT_NAME

        paragraphs = []
        for row in data:
            row_paragraphs = []
            for value in row:
                paragraph = Paragraph(str(value), style)
                row_paragraphs.append(paragraph)
            paragraphs.append(row_paragraphs)

        table = Table(paragraphs)

        table.setStyle(TableStyle(
            [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black), ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]
        ))

        table.wrapOn(self, 0, 0)
        table.drawOn(self, x, y)

    def draw_plot(self, x, Y, y_labels, x_label):
        plt.xlabel(x_label)
        for y, label in zip(Y, y_labels):
            plt.plot(x, y, label=label)
        plt.legend(loc='best')
        img_path = self.temp_file_name('png')
        plt.savefig(img_path)
        px_per_inch = plt.rcParams['figure.dpi']  # pixel in inches
        y_plot = self._pagesize[-1] - plt.figure().get_figheight() * px_per_inch
        self.drawImage(img_path, 0, y_plot)
        os.remove(img_path)

    @property
    def directory(self):
        return os.path.dirname(self._filename)

    def file_name(self, name_value, extension):
        return os.path.join(self.directory, str(name_value) + '.' + extension)

    def temp_file_name(self, extension):
        i = 0
        while os.path.exists(self.file_name(i, extension)):
            i += 1
        return self.file_name(i, extension)