from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTranslator, QCoreApplication, pyqtSignal
from ui.widgets.translate_widget.utils import get_translator_filepath
from configuration.config import UiConfig
from typing import List
import logging


class TranslateWidget(QWidget):
    DEFAULT_LANGUAGE_ID: int = 0
    CURRENT_LANGUAGE_CODE: str = UiConfig.default_language_code()
    language_selected = pyqtSignal(int)
    COUNTRY_DATAS = [
        get_translator_filepath(UiConfig.default_language_code()),
        get_translator_filepath(UiConfig.second_language_code()),
        get_translator_filepath(UiConfig.third_language_code()),
    ]

    def __init__(self):
        super().__init__()

        self._translator = QTranslator()
        self._widgets: List[QWidget] = []

        # signals
        self.language_selected.connect(lambda: logging.info('язык выбран'))
        self.language_selected.connect(self.set_current_language)
        self.language_selected.connect(self.change_app_language)

    def add_widget(self, widget: QWidget):
        self._widgets.append(widget)

    def pop_buy_window(self) -> None:
        from ui.widgets.buy_window import BuyWindow

        for i, w in enumerate(self._widgets):
            if isinstance(w, BuyWindow):
                self._widgets.pop(i)
                return

    @classmethod
    def set_current_language(cls, lang_idx):
        lang_codes = [UiConfig.default_language_code(), UiConfig.second_language_code(), UiConfig.third_language_code()]
        cls.CURRENT_LANGUAGE_CODE = lang_codes[lang_idx]

    def change_app_language(self, lang_index: int):
        QCoreApplication.removeTranslator(self._translator)

        self._translator = QTranslator()
        self._translator.load(self.COUNTRY_DATAS[lang_index])

        QCoreApplication.installTranslator(self._translator)
        for i, widget in enumerate(self._widgets):
            try:
                widget.ui.retranslateUi(widget)
            # could be runtime error after deleting buy window
            # we have to handle it with pop out old (deleted buy window) from list of rendered widgets without overflow
            except RuntimeError as err:
                logging.info(err)
                # self._widgets.pop(i)
