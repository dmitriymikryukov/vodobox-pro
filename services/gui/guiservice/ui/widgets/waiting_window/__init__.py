from PyQt5.QtCore import QTimer, pyqtSignal, QEasingCurve, QSequentialAnimationGroup
from configuration.config import UiConfig, ServiceMenuConfig
from PyQt5.QtWidgets import QWidget, QButtonGroup, QPushButton, QLabel
from PyQt5.Qt import QPropertyAnimation, QColor, pyqtProperty
from ui.widgets.translate_widget import TranslateWidget
from ui.converted.gen_waiting_window import Ui_Form
from PyQt5.QtGui import QIcon, QPixmap
from datetime import datetime
import os
from ui import app

class WaitingWindow(QWidget):
    """
    Виджет окна ожидания, содержащий:
    - Выбор языка (русский, румынский, английский, удмуртский)
    - Просмотр информации о продукте
    - Переход к окну оплаты
    """

    # custom signals initialization
    service_menu_sequence_passed = pyqtSignal()

    def __init__(self, translate_widget: TranslateWidget):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # проверка на выдачу сдачи
        if app.sgn_gui:
            self.show_money_change_warning(app.sgn_gui.can_dispense_cash())

        # object instances
        self.service_config = ServiceMenuConfig()

        self.true_service_menu_btn_sequence = self.create_service_menu_btn_sequence()
        self._buy_btn_color = QColor(145, 240, 134)
        self._seconds_blink_flag = False
        self.translate_widget = translate_widget
        self.language_btn_group = QButtonGroup()
        self.service_menu_btn_sequence: list[int] = []

        self.user_timeout_timer = QTimer(singleShot=True)
        self.datetime_timer = QTimer()

        # customization
        self.ui.up_arrow_btn.setIcon(QIcon(os.path.join(os.getcwd(), '..', 'resources', 'icons', 'up.svg')))
        self.ui.down_arrow_btn.setIcon(QIcon(os.path.join(os.getcwd(), '..', 'resources', 'icons', 'down.svg')))

        if not UiConfig.consumer_info_show_btn():
            self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_consumer_page)

        if not UiConfig.translate_show_btn():
            self.ui.top_right_stack_widget.setCurrentWidget(self.ui.empty_translate_page)

        if not UiConfig.buy_btn_position() == 7:
            self.ui.second_top_right_stack_widget.setCurrentWidget(self.ui.spare_buy_page)
            self.ui.second_bottom_right_stack_widget.setCurrentWidget(self.ui.empty_second_bottom_right_page)

        self.add_logo(UiConfig.logotype())
        self.animate_buy_btn()

        for i, lang_btn in enumerate([
            self.ui.lang_btn_1,
            self.ui.lang_btn_2,
            self.ui.lang_btn_3,
        ]):
            self.language_btn_group.addButton(lang_btn, i)
        self.language_btn_group.buttons()[0].setChecked(True)

        # signals
        self.init_translate_signals()
        self.init_service_signals()
        self.init_consumer_signals()
        self.init_timer_signals()

    def init_translate_signals(self) -> None:
        """
        Инициализация сигналов для выбора языка
        """
        self.ui.translate_btn.clicked.connect(self.switch_on_translate_widget)
        self.ui.up_arrow_btn.clicked.connect(self.select_language_up)
        self.ui.down_arrow_btn.clicked.connect(self.select_language_down)
        self.translate_widget.language_selected.connect(self.set_text_for_dynamically_translated_widget)

    def init_service_signals(self) -> None:
        """
        Инициализация сигналов для проверки на последовательность нажатий кнопок для перехода в сервисное меню
        """
        self.ui.consumer_info_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(1))
        self.ui.empty_consumer_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(1))

        self.ui.inv_up_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(2))
        self.ui.up_arrow_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(2))

        self.ui.inv_down_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(3))
        self.ui.down_arrow_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(3))

        self.ui.translate_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(5))
        self.ui.empty_translate_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(5))

        self.ui.inv_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(6))
        self.ui.inv_second_bottom_right_btn.clicked.connect(lambda: self.check_on_service_menu_button_sequence(7))

    def init_consumer_signals(self) -> None:
        """
        Инициализация сигнала для информации потребителя
        """
        self.ui.consumer_info_btn.clicked.connect(self.switch_on_consumer_info_widget)

    def init_timer_signals(self) -> None:
        """
        Инициализация сигналов таймеров
        """
        self.user_timeout_timer.timeout.connect(self.switch_on_waiting_widget)
        self.user_timeout_timer.timeout.connect(lambda: self.language_btn_group.buttons()[0].setChecked(True))
        self.ui.buy_btn.clicked.connect(self.user_timeout_timer.stop)
        self.ui.spare_buy_btn.clicked.connect(self.user_timeout_timer.stop)
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(500)

    def show_money_change_warning(self, status: bool):
        if status:
            self.ui.money_change_label.show()
        else:
            self.ui.money_change_label.hide()

    def switch_on_waiting_widget(self) -> None:
        """
        Переключение на меню ожидания
        """
        self.ui.stack_widget.setCurrentWidget(self.ui.home_widget)
        self.language_btn_group.buttons()[0].setChecked(True)
        self.change_arrow_buttons_visibility(False)
        self.translate_widget.language_selected.emit(TranslateWidget.DEFAULT_LANGUAGE_ID)

    def switch_on_translate_widget(self) -> None:
        """
        Переключение на меню выбора языка
        """
        self.ui.stack_widget.setCurrentWidget(self.ui.language_widget)
        self.change_arrow_buttons_visibility(True)
        self.user_timeout_timer.start(30_000)

    def switch_on_consumer_info_widget(self) -> None:
        """
        Переключение на меню информации о товаре
        """
        self.ui.stack_widget.setCurrentWidget(self.ui.consumer_widget)
        self.change_arrow_buttons_visibility(False)
        self.user_timeout_timer.start(30_000)

    def set_text_for_dynamically_translated_widget(self, lang_idx: int):
        self.ui.seller_info_lbl.setText(UiConfig.seller_name())
        self.ui.address_lbl.setText(UiConfig.kiosk_address())
        self.ui.water_created_lbl.setText(UiConfig.water_created_date())
        self.ui.water_refill_lbl.setText(UiConfig.water_refill_date())

        wash_dates = UiConfig.wash_dates()
        self.ui.wash1_lbl.setText(wash_dates[0])
        self.ui.wash2_lbl.setText(wash_dates[1])
        self.ui.wash3_lbl.setText(wash_dates[2])

        lang_codes = [UiConfig.default_language_code(), UiConfig.second_language_code(), UiConfig.third_language_code()]

        def get_translation_for_lang_buttons(translation_language: str, code_sequence: list) -> list:
            translation = {
                'RU': {
                    'RU': {
                        'RO': ['Русский', 'Румынский', 'Английский'],
                        'EN': ['Русский', 'Английский', 'Румынский']
                    },
                    'EN': {
                        'RU': ['Английский', 'Русский', 'Румынский'],
                        'RO': ['Английский', 'Румынский', 'Русский'],
                    },
                    'RO': {
                        'RU': ['Румынский', 'Русский', 'Английский'],
                        'EN': ['Румынский', 'Английский', 'Русский'],
                    },
                },
                'RO': {
                    'RU': {
                        'RO': ['Rusă', 'Română', 'Engleză'],
                        'EN': ['Rusă', 'Engleză', 'Română']
                    },
                    'EN': {
                        'RU': ['Engleză', 'Rusă', 'Română'],
                        'RO': ['Engleză', 'Română', 'Rusă'],
                    },
                    'RO': {
                        'RU': ['Română', 'Rusă', 'Engleză'],
                        'EN': ['Română', 'Engleză', 'Rusă'],
                    },
                },
                'EN': {
                    'RU': {
                        'RO': ['Russian', 'Romanian', 'English'],
                        'EN': ['Russian', 'English', 'Romanian']
                    },
                    'EN': {
                        'RU': ['English', 'Russian', 'Romanian'],
                        'RO': ['English', 'Romanian', 'Russian'],
                    },
                    'RO': {
                        'RU': ['Romanian', 'Russian', 'English'],
                        'EN': ['Romanian', 'English', 'Russian'],
                    },
                }
            }
            return translation[translation_language][code_sequence[0]][code_sequence[1]]

        [btn.setText(text) for btn, text in zip(
            [self.ui.lang_btn_1, self.ui.lang_btn_2, self.ui.lang_btn_3],
            get_translation_for_lang_buttons(lang_codes[lang_idx], lang_codes)
        )]

    def turn_on_dark_theme(self) -> None:
        """
        Переключение на темную тему
        """
        self.ui.frame.setStyleSheet('#frame{background-color: black;}')

        [btn.setStyleSheet('''
        QPushButton{
        color: white;
        background-color: rgb(42, 48, 58);
        border-top-right-radius: 20px;
        border-bottom-right-radius: 60px;
        border-top-left-radius: 60px;
        border-bottom-left-radius: 20px;
        border: 1px solid #C0C0BF;
        }
        ''') for btn in [self.ui.consumer_info_btn, self.ui.down_arrow_btn]]

        [btn.setStyleSheet('''
        QPushButton {
        color: white;
        background-color:rgb(42, 48, 58);
        border-top-right-radius: 60px;
        border-top-left-radius: 20px;
        border-bottom-right-radius: 20px;
        border-bottom-left-radius: 60px;
        border: 1px solid #C0C0BF;
        }
        ''') for btn in [self.ui.up_arrow_btn, self.ui.translate_btn]]

        self.ui.frame_2.setStyleSheet('''
        #frame_2 {
            color: rgb(0, 0, 0);
            background-color: rgb(42, 48, 58);
            border-radius: 40px;
            border: 1px solid #C0C0BF;
        }
        ''')
        self.ui.frame_10.setStyleSheet('''
        #frame_10{
        background-color: rgb(42, 48, 58); 
        border: 1px solid #C0C0BF;  
        border-top-right-radius: 20px;
        border-top-left-radius: 20px;
        border-bottom-right-radius: 60px;
        border-bottom-left-radius: 60px;
        }
        ''')
        self.ui.label_3.setStyleSheet('color: white; background-color: transparent; border-radius: 15px; border: 1px solid #C0C0BF;')
        [lbl.setStyleSheet('color: white; background-color: transparent;')
         for lbl in [self.ui.datetime_lbl, self.ui.address_lbl,
                     self.ui.label_4, self.ui.label_5, self.ui.label_7, self.ui.label_8, self.ui.label,
                     self.ui.water_created_lbl, self.ui.label_6, self.ui.wash1_lbl, self.ui.wash2_lbl,
                     self.ui.wash3_lbl, self.ui.label_2, self.ui.water_refill_lbl, self.ui.seller_info_lbl]]

        self.ui.frame_17.setStyleSheet('#frame_17{background-color: rgb(42, 48, 58); border-radius: 20px; border: 1px solid #C0C0BF;}')

        [btn.setStyleSheet('''
        QPushButton {
        color: white;
        background-color:transparent;
        border-radius: 15px;
        }

        QPushButton:checked {
            color: black;
             background-color: rgb(245, 245, 245);
            border: 1px solid #696969;
        }
        ''') for btn in [self.ui.lang_btn_1, self.ui.lang_btn_2, self.ui.lang_btn_3]]

        self.ui.frame_24.setStyleSheet('''
        #frame_24 {
            background-color: rgb(42, 48, 58);
            border-radius: 20px;
        }
        ''')

    def add_logo(self, logo_filepath: str) -> None:
        """
        Добавление логотипа на главную страницу меню ожидания
        :param logo_filepath: название файла добавляемого логотипа
        """
        lbl = QLabel()
        lbl.setPixmap(QPixmap(logo_filepath))
        lbl.setScaledContents(True)
        lbl.setMaximumSize(220, 220)
        self.ui.logo_layout.addWidget(lbl)

    def change_buy_btn_position(self) -> None:
        """
        Смена позиции кнопки начала покупки на позицию 6 (смотреть схему расположения кнопок)
        *смена происходит на основе конфига, который в свою очередь основывается на возможной поломке физической
        кнопки на позиции 7
        """
        self.ui.second_top_right_stack_widget.setCurrentWidget(self.ui.spare_buy_page)
        self.ui.second_bottom_right_stack_widget.setCurrentWidget(self.ui.empty_second_bottom_right_page)

    def create_service_menu_btn_sequence(self) -> list:
        """
        Формирование нужной комбинации кнопок для перехода в сервисное меню на основе пароля из файла конфигураций
        Пример: пароль 1211 - 1 нажатие по кнопке на позиции два, 2 нажатия по кнопке на позиции три,
        1 нажатие по кнопке на позиции шесть, 1 нажатие по кнопке на позиции семь.
        *Примечание: если кнопка покупки находится на позиции 6, то в пароле конфигурации необходимо, чтобы был
        ноль на месте третьей или четвертой цифры (пример: 1101 или 1110) иначе происходит переход в меню выбора товара
        :return: список с нужной последовательностью кнопок для нажатия
        """
        true_sequence = []
        for pos, mult_count in zip([2, 3, 6, 7], self.service_config.password):
            true_sequence += [pos for _ in range(mult_count)]
        return true_sequence

    @pyqtProperty(QColor)
    def buy_btn_color(self) -> QColor:
        """
        Getter для отрисовки анимации цвета кнопки начала покупок
        :return: текущий цвет кнопки начала покупок
        """
        return self._buy_btn_color

    @buy_btn_color.setter
    def buy_btn_color(self, col: QColor) -> None:
        """
        Setter для отрисовки анимации цвета кнопки начала покупок
        :param col: новый цвет для кнопки начала покупок
        :return:
        """
        stylesheet = f'''
        background-color: rgb({col.red()}, {col.green()}, {col.blue()});
        border-top-right-radius: {'40' if UiConfig.buy_btn_position() == 7 else '20'}px;
        border-bottom-right-radius: {'20' if UiConfig.buy_btn_position() == 7 else '40'}px;
        border-top-left-radius: {'20' if UiConfig.buy_btn_position() == 7 else '40'}px;
        border-bottom-left-radius: {'40' if UiConfig.buy_btn_position() == 7 else '20'}px;
        border: 1px solid #B3B3B3;
        '''
        self.ui.buy_btn.setStyleSheet(stylesheet)
        self.ui.spare_buy_btn.setStyleSheet(stylesheet)
        self._buy_btn_color = col

    def animate_buy_btn(self) -> None:
        """
        Анимация кнопки начала покупок
        """
        self.animation_group = QSequentialAnimationGroup()
        self.first_animation = QPropertyAnimation(self, b'buy_btn_color')
        self.second_animation = QPropertyAnimation(self, b'buy_btn_color')

        self.first_animation.setDuration(2000)
        self.first_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.first_animation.setStartValue(QColor(145, 240, 134))
        self.first_animation.setEndValue(QColor(17, 130, 59))

        self.second_animation.setDuration(2000)
        self.second_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.second_animation.setStartValue(QColor(17, 130, 59))
        self.second_animation.setEndValue(QColor(145, 240, 134))

        self.animation_group.addAnimation(self.first_animation)
        self.animation_group.addAnimation(self.second_animation)

        self.animation_group.start()
        self.animation_group.setLoopCount(-1)

    def check_on_service_menu_button_sequence(self, position: int) -> bool:
        """
        Проверка на нужную последовательность нажатий кнопок для перехода в сервисное меню
        :return: статус нажатия нужной последовательности
        """

        if len(self.service_menu_btn_sequence) >= len(self.true_service_menu_btn_sequence):
            self.service_menu_btn_sequence.pop(0)
        self.service_menu_btn_sequence.append(position)

        if self.service_menu_btn_sequence == self.true_service_menu_btn_sequence:
            self.service_menu_sequence_passed.emit()
            return True
        return False

    def update_datetime(self) -> None:
        """
        Callback-функция для обновления даты и времени на интерфейсе
        """
        self.ui.datetime_lbl.setText(
            datetime.now().strftime('%H:%M %d.%m.%Y' if self._seconds_blink_flag else '%H %M %d.%m.%Y'))
        self._seconds_blink_flag = not self._seconds_blink_flag

    def change_arrow_buttons_visibility(self, state: bool) -> None:
        """
        state - функция-состояния, меняющая видимость кнопок-стрелок
        При значении True: кнопки видно.
        При значении False: кнопки скрыты.
        """
        if state:
            self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.up_arrow_page)
            self.ui.second_bottom_left_stack_widget.setCurrentWidget(self.ui.down_arrow_page)
        else:
            self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.empty_up_arrow_page)
            self.ui.second_bottom_left_stack_widget.setCurrentWidget(self.ui.empty_down_arrow_page)

    def select_language_up(self) -> None:
        """
        Выбрать язык сверху из списка доступных
        """
        self.language_btn_group.buttons()[
            self.language_btn_group.checkedId() - 1
            ].setChecked(True)
        self.translate_widget.language_selected.emit(self.language_btn_group.checkedId())
        self.user_timeout_timer.start(30_000)

    def select_language_down(self) -> None:
        """
        Выбрать язык снизу из списка доступных
        """
        try:
            self.language_btn_group.buttons()[
                self.language_btn_group.checkedId() + 1
                ].setChecked(True)
        except IndexError:
            self.language_btn_group.buttons()[0].setChecked(True)
        finally:
            self.translate_widget.language_selected.emit(self.language_btn_group.checkedId())
            self.user_timeout_timer.start(30_000)
