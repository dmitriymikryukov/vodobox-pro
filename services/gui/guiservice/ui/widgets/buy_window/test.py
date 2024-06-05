from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QRect, QThread
from PyQt5.QtGui import QPainter, QFont, QPixmap, QImage
import sys
import time


class WaterBottleWidget(QWidget):
    def __init__(self, parent=None, max_water_volume: float = 0):
        super().__init__(parent)
        self._max_water_volume = max_water_volume
        self._progress = 0
        self.setLayout(QVBoxLayout())
        self.progress_lbl = QLabel(f'{self.progress}%')
        self.progress_lbl.setFont(QFont('Rubik', 15))
        self.progress_lbl.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.progress_lbl)

    def paintEvent(self, event):
        painter = QPainter(self)
        svg_render = QSvgRenderer("D:\\projects\\vodobox\\resources\\icons\\empty-bottle.svg")
        svg_render.render(painter)

        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        diff = self.height() / 100

        empty_bottle_pixmap = QPixmap("D:\\projects\\vodobox\\resources\\icons\\filled-bottle.svg")
        empty_bottle_pixmap = empty_bottle_pixmap.scaled(self.width(), self.height())
        rect = QRect(self.rect().x(), self.height() - int(diff * self.progress),
                     self.width(), int(diff * self.progress))
        painter.drawPixmap(
            rect,
            empty_bottle_pixmap.copy(rect),
        )

        self.progress_lbl.setText(f'{self.progress}%')

    @property
    def current_water_volume(self):
        return self._progress * self._max_water_volume / 100

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value: int):
        if 0 <= value <= 100:
            self._progress = value
            self.update()


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.progressBar = WaterBottleWidget(self, 19.2)

        # Button to test the progress bar
        self.button = QPushButton('Increase Progress', self)
        self.button.clicked.connect(self.increase_progress)

        layout = QVBoxLayout(self)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.button)

        self.setGeometry(300, 300, 300, 600)
        self.setWindowTitle('Image Progress Bar')
        self.show()

    def increase_progress(self):
        def incr():
            while self.progressBar.progress <= 100:
                self.progressBar.progress += 1
                time.sleep(0.3)
        thread = QThread(self)
        thread.run = incr
        thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
