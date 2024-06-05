from ui.widgets.activation_window.const import GET_KEY_LINK, ACTIVATE_KEY_LINK
from ui.converted.gen_activation_window import Ui_Form
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from datetime import datetime
from io import BytesIO
import requests
import qrcode


class ActivationWindow(QWidget):
    """
    Виджет окна активации киоска
    """

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # object instances
        self._seconds_blink_flag = False
        self.datetime_timer = QTimer()

        # signals
        self.ui.activation_btn.clicked.connect(self.switch_on_link_page)
        self.datetime_timer.timeout.connect(self.update_datetime)

        self.datetime_timer.start(500)

    def turn_on_dark_theme(self) -> None:
        """
        Переключение на темную тему
        """
        self.ui.frame.setStyleSheet('background-color: black;')
        changed_frame = [self.ui.frame_10, self.ui.index_page, self.ui.link_page, self.ui.no_connection_page]
        frame_stylesheet = "{background-color: rgb(42, 48, 58); border: 1px solid #C0C0BF; border-radius: 20px;}"
        [frame.setStyleSheet('#' + frame.objectName() + frame_stylesheet) for frame in changed_frame]

        changed_lbl = [self.ui.activate_link_lbl, self.ui.datetime_lbl, self.ui.label, self.ui.label_2, self.ui.label_4, self.ui.label_5]
        [lbl.setStyleSheet('color: white; background-color: transparent;') for lbl in changed_lbl]

    def update_datetime(self) -> None:
        """
        Callback-функция для обновления даты и времени
        """
        self.ui.datetime_lbl.setText(
            datetime.now().strftime('%H:%M %d/%m/%Y' if self._seconds_blink_flag else '%H %M %d/%m/%Y'))
        self._seconds_blink_flag = not self._seconds_blink_flag

    def switch_on_link_page(self) -> None:
        """
        Переключение на страницу с результатом запроса на активацию
        """
        self.ui.testing_stack_widget.setCurrentWidget(self.ui.empty_testing_page)
        try:
            activate_resp = requests.get(GET_KEY_LINK)
            # при успешном запросе
            if activate_resp.status_code == 200:
                self.ui.btn_stack_widget.setCurrentWidget(self.ui.start_work_btn_page)

                activate_key_link = f'{ACTIVATE_KEY_LINK}/{activate_resp.json()["key"]}'
                self.ui.activate_link_lbl.setText(activate_key_link)
                self.set_qr_link(activate_key_link)

                self.ui.stack_widget.setCurrentWidget(self.ui.link_page)
            else:
                self.ui.stack_widget.setCurrentWidget(self.ui.no_connection_page)
        except (requests.ConnectionError, requests.ConnectTimeout):
            self.ui.stack_widget.setCurrentWidget(self.ui.no_connection_page)

    def set_qr_link(self, text: str) -> None:
        """
        Генерация и вывод qr-кода на экран на основе ссылки на активацию
        :param text: ссылка на активацию
        :return:
        """
        buf = BytesIO()
        img = qrcode.make(text)

        img.save(buf, "PNG")
        qt_pixmap = QPixmap()
        qt_pixmap.loadFromData(buf.getvalue(), "PNG")

        self.ui.qr_lbl.setPixmap(qt_pixmap)
        self.ui.qr_lbl.setStyleSheet('background-color: transparent')

