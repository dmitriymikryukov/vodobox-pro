from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from configuration.testing import UiConfig
from ui.widgets.buy_window import BuyWindow
from ui.widgets.waiting_window import WaitingWindow
from ui.widgets.translate_widget import TranslateWidget
from ui.widgets.activation_window import ActivationWindow
from ui.widgets.service_menu_window import ServiceMenuWindow
import logging


class MainWindow(QMainWindow):
    """
    Главное окно, соединяющее:
    - Окно ожидания
    - Окно покупок
    - Окно активации
    - Окно сервисного меню
    """

    def __init__(self):
        super().__init__()

        # global utility-instances
        self.translate_widget = TranslateWidget()
        self.windows_stack_widget = QStackedWidget(self)

        # windows
        self.activate_window = ActivationWindow()
        self.waiting_window = WaitingWindow(self.translate_widget)
        self.service_menu = ServiceMenuWindow()
        self.buy_window = BuyWindow()

        # theme switching
        if not UiConfig.is_light_theme():
            self.activate_window.turn_on_dark_theme()
            self.waiting_window.turn_on_dark_theme()
            self.buy_window.turn_on_dark_theme()

        # add app windows
        self.setCentralWidget(self.windows_stack_widget)

        # self.windows_stack_widget.addWidget(self.activate_window)
        self.windows_stack_widget.addWidget(self.waiting_window)
        self.windows_stack_widget.addWidget(self.service_menu)
        self.windows_stack_widget.addWidget(self.buy_window)

        # add app windows to translator
        self.translate_widget.add_widget(self.activate_window)
        self.translate_widget.add_widget(self.waiting_window)
        self.translate_widget.add_widget(self.buy_window)
        self.translate_widget.add_widget(self.service_menu)

        # signals
        self.init_switch_signals()
        self.init_translate_signal()

        self.translate_widget.language_selected.emit(self.translate_widget.DEFAULT_LANGUAGE_ID)

    def init_switch_signals(self) -> None:
        """
        Инициализация сигналов для смены окон
        """
        self.activate_window.ui.start_work_btn.clicked.connect(
            lambda: self.windows_stack_widget.setCurrentWidget(self.waiting_window)
        )
        self.waiting_window.ui.buy_btn.clicked.connect(
            self.switch_on_buy_window
        )
        self.waiting_window.ui.spare_buy_btn.clicked.connect(
            self.switch_on_buy_window
        )
        self.waiting_window.service_menu_sequence_passed.connect(
            lambda: self.windows_stack_widget.setCurrentWidget(self.service_menu)
        )
        self.service_menu.service_menu_exited.connect(
            lambda: self.windows_stack_widget.setCurrentWidget(self.waiting_window)
        )
        self.buy_window.session_terminated.connect(self.cancel_buy_window_by_termination)
        self.buy_window.session_timeout.connect(self.cancel_buy_window_by_timeout)

    def init_translate_signal(self):
        self.translate_widget.language_selected.connect(self.buy_window.init_values_from_config)

    def switch_on_buy_window(self) -> None:
        """
        Переход на меню покупки, но перед этим происходит проверка на последовательность для перехода в сервисное
        меню
        """
        sender = self.sender()
        if sender == self.waiting_window.ui.buy_btn:
            sequence_passed = self.waiting_window.check_on_service_menu_button_sequence(7)
        else:
            sequence_passed = self.waiting_window.check_on_service_menu_button_sequence(6)
        if not sequence_passed:
            self.buy_window.session_started.emit()
            self.windows_stack_widget.setCurrentWidget(self.buy_window)

    def cancel_buy_window_by_timeout(self):
        logging.info('закрыли меню покупки по timeout сессии')
        self.render_buy_window()

    def cancel_buy_window_by_termination(self):
        logging.info('закрыли меню покупки принудительно по нажатию')
        self.buy_window.session_timer.stop()
        self.render_buy_window()

    def render_buy_window(self):
        # происходит перерендер при создании нового окна покупок после возвращения
        # в меню ожидания
        from ui import app
        try:

            self.windows_stack_widget.removeWidget(self.buy_window)
            # self.buy_window.deleteLater()
            self.buy_window = BuyWindow()
            app.sgn_gui.current_window = self.buy_window

            if not UiConfig.is_light_theme():
                self.buy_window.turn_on_dark_theme()

            self.windows_stack_widget.addWidget(self.buy_window)
            self.windows_stack_widget.setCurrentWidget(self.waiting_window)

            self.translate_widget.pop_buy_window()
            self.translate_widget.add_widget(self.buy_window)
            self.init_translate_signal()
            self.waiting_window.switch_on_waiting_widget()

            self.buy_window.session_terminated.connect(self.cancel_buy_window_by_termination)
            self.buy_window.session_timeout.connect(self.cancel_buy_window_by_timeout)
        except Exception as err:
            logging.error(f'Ошибка при пересоздании меню покупки: {err}')
