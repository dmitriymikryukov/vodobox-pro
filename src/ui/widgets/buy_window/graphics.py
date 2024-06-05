from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import os


class WaterBottleWidget(QWidget):
    progress_changed = pyqtSignal(int)
    filling_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self.setLayout(QVBoxLayout())
        self.progress_lbl = QLabel(f'{self.progress}%')
        self.progress_lbl.setFont(QFont('Rubik', 15))
        self.progress_lbl.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.progress_lbl)

    def paintEvent(self, event):
        painter = QPainter(self)
        svg_render = QSvgRenderer(os.path.join(os.getcwd(), '..', 'resources', 'icons', 'empty-bottle.svg'))
        svg_render.render(painter)

        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        diff = self.height() / 100

        empty_bottle_pixmap = QPixmap(os.path.join(os.getcwd(), '..', 'resources', 'icons', 'filled-bottle.svg'))
        empty_bottle_pixmap = empty_bottle_pixmap.scaled(self.width(), self.height())
        rect = QRect(self.rect().x(), self.height() - int(diff * self.progress),
                     self.width(), int(diff * self.progress))
        painter.drawPixmap(
            rect,
            empty_bottle_pixmap.copy(rect),
        )

        self.progress_lbl.setText(f'{self.progress}%')

    @property
    def progress(self) -> int:
        return self._progress

    @progress.setter
    def progress(self, value: int) -> None:
        try:
            if 0 <= value <= 100:
                self._progress = value
                self.progress_changed.emit(self.progress)
                if self.progress == 100:
                    self.filling_finished.emit()
                self.update()
        # TODO объект пытается обновить себя, хотя уже удален (возникает при принудительном завершении налива)
        except RuntimeError:
            pass
