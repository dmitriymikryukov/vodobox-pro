from ui.widgets.buy_window.products import Product, Water, PlugWithWater, ContainerWithWater, LoyalCard
from PyQt5.QtCore import pyqtSignal, QTimer, QThread, Qt, QEasingCurve, QSequentialAnimationGroup
from ui.widgets.buy_window.graphics import WaterBottleWidget
from PyQt5.Qt import QPropertyAnimation, QColor, pyqtProperty
from PyQt5.QtWidgets import QWidget, QButtonGroup, QLabel
from configuration.config import BuyConfig, UiConfig
from ui.widgets.buy_window.handlers import FlowHandler
from ui.converted.gen_buy_window import Ui_Form
from PyQt5.QtGui import QPixmap, QFont
from ui import app
import os


class BuyWindow(QWidget):
    """
    Виджет окна покупок и выбора товара:
    - Вода (быстрый выбор объема для контейнера или объема для пробки, также выбор пользователя)
    - Пробка
    - Контейнер
    """

    # custom signals initialization
    get_money_change = pyqtSignal(float)
    deposit_balance_changed = pyqtSignal()
    no_money_left_to_change = pyqtSignal()

    session_started = pyqtSignal()
    session_timeout = pyqtSignal()
    buy_window_closed = pyqtSignal()

    payment_started = pyqtSignal()
    payment_canceled = pyqtSignal()
    payment_succeed = pyqtSignal()
    payment_failed = pyqtSignal()

    filling_started = pyqtSignal(Water)
    filling_finished = pyqtSignal()

    product_chosen = pyqtSignal(Product)
    # plug_taken = pyqtSignal()
    # container_taken = pyqtSignal()
    # loyal_card_taken = pyqtSignal()
    product_list_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        if app.sgn_gui:
            app.sgn_gui.current_window = self

        # object instances
        self.flow_handler = FlowHandler()
        self.last_current_liters_changed = 0
        self.flowed_liter_count = 0
        self.TOTAL_PRICE = 0
        self.config = BuyConfig()
        self.bottle_progress_bar_widget = WaterBottleWidget()
        self.update_buy_session_time_btn_group = QButtonGroup()
        self._session_time = self.config.session_time
        self._cancellation_time = self.config.cancellation_time
        self.session_timer = QTimer()
        self.payment_cancellation_timer = QTimer()
        self.bottle_filling_thread = QThread()
        self.stop_bottle_filling_thread = QThread()
        # self.start_session_thread = QThread()
        # self.start_session_thread.run = self.start_session
        self.last_popped_water: Water = None
        self.is_pouring_running = True
        self._chosen_products: list[Product] = []
        self.remaining_price: float = 0
        self._confirm_btn_color = QColor(245, 245, 245)

        # customizations
        self.animate_confirm_btn()
        self.ui.payment_success_lbl.setPixmap(
            QPixmap(os.path.join(os.getcwd(), '..', 'resources', 'icons', 'large_passed.svg')))
        self.ui.payment_failed_lbl.setPixmap(
            QPixmap(os.path.join(os.getcwd(), '..', 'resources', 'icons', 'large_failed.svg')))

        # initialization
        self.init_values_from_config()
        self.init_update_session_time_signals()
        self.init_choose_signals()
        self.init_payment_signals()
        self.init_pouring_signals()

    def init_values_from_config(self) -> None:
        """
        Инициализация меню покупок конфигурационными значениями
        """
        # устанавливаем адрес киоска
        self.ui.address_lbl.setText(UiConfig.kiosk_address())

        # устанавливаем значения для начального значения при пользовательском выборе литров
        lbl = self.ui.liters_count_lbl.text().split()
        lbl[0] = str(self.config.min_liters_count)
        self.ui.liters_count_lbl.setText(' '.join(lbl))

        # устанавливаем значение для выбора быстрого количества литров для пробки
        lbl = self.ui.plug_ltr_btn.text().split()
        lbl[0] = str(self.config.plug_liters_count)
        self.ui.plug_ltr_btn.setText(' '.join(lbl))

        # устанавливаем значение для цены за воду при быстром выборе литров для пробки
        lbl = self.ui.plug_ltr_price_lbl.text().split()
        lbl[0] = str(self.config.water_price_per_liter * self.config.plug_liters_count)
        self.ui.plug_ltr_price_lbl.setText(' '.join(lbl))

        # устанавливаем значение для выбора быстрого количества литров для контейнера
        lbl = self.ui.container_ltr_btn.text().split()
        lbl[0] = str(self.config.container_liters_count)
        self.ui.container_ltr_btn.setText(' '.join(lbl))

        # устанавливаем значение для цены за воду при быстром выборе литров для контейнера
        lbl = self.ui.container_ltr_price_lbl.text().split()
        lbl[0] = str(self.config.water_price_per_liter * self.config.container_liters_count)
        self.ui.container_ltr_price_lbl.setText(' '.join(lbl))

        # устанавливаем значение цены для быстрого выбора воды + контейнер
        lbl = self.ui.container_and_water_price_lbl.text().split()
        lbl[0] = str(self.config.container_price_with_water)
        self.ui.container_and_water_price_lbl.setText(' '.join(lbl))

        # устанавливаем значение цены для карты лояльности
        lbl = self.ui.loyal_card_price_lbl.text().split()
        lbl[0] = str(self.config.loyal_card_price)
        self.ui.loyal_card_price_lbl.setText(' '.join(lbl))

        # устанавливаем значение цены для быстрого выбора воды + пробки
        lbl = self.ui.plug_and_water_price_lbl.text().split()
        lbl[0] = str(self.config.plug_price_with_water)
        self.ui.plug_and_water_price_lbl.setText(' '.join(lbl))

    def init_update_session_time_signals(self) -> None:
        """
        Инициализация кнопок, при нажатии на которые происходит обновление
        таймера покупочной сессии к начальному времени
        """
        for btn in [
            self.ui.plug_ltr_btn, self.ui.plus_btn, self.ui.choose_ltr_btn, self.ui.confirm_btn,
            self.ui.container_ltr_btn, self.ui.minus_btn, self.ui.stop_btn, self.ui.back_btn,
            self.ui.start_pouring_btn, self.ui.continue_btn, self.ui.top_up_card_btn,
            self.ui.loyal_card_btn, self.ui.qr_btn, self.ui.container_btn, self.ui.plug_btn,
            self.ui.cash_or_loyal_card_btn, self.ui.bank_card_btn, self.ui.cancel_payment_btn
        ]:
            self.update_buy_session_time_btn_group.addButton(btn)
        self.update_buy_session_time_btn_group.buttonClicked.connect(self.set_session_time_to_initial_value)

    def init_choose_signals(self) -> None:
        """
        Инициализация сигналов для выбора товаров: (Вода, пробка, тара)
        """
        self.ui.plus_btn.clicked.connect(self.increase_liters_count)
        self.ui.minus_btn.clicked.connect(self.decrease_liters_count)
        self.ui.choose_ltr_btn.clicked.connect(self.switch_on_choose_window)
        self.ui.add_more_btn.clicked.connect(self.switch_on_cart_window)
        self.ui.back_btn.clicked.connect(self.remove_last_product)

        self.ui.confirm_btn.clicked.connect(lambda: self.product_chosen.emit(
            Water(float(self.ui.liters_count_lbl.text().split()[0]), self.config.water_price_per_liter)))
        self.ui.container_ltr_btn.clicked.connect(lambda: self.product_chosen.emit(
            Water(self.config.container_liters_count, self.config.water_price_per_liter)))
        self.ui.plug_ltr_btn.clicked.connect(lambda: self.product_chosen.emit(
            Water(self.config.plug_liters_count, self.config.water_price_per_liter)))
        self.ui.loyal_card_btn.clicked.connect(lambda: self.product_chosen.emit(
            LoyalCard(self.config.loyal_card_price)))
        self.ui.plug_btn.clicked.connect(lambda: self.product_chosen.emit(
            PlugWithWater(self.config.plug_price_with_water)))
        self.ui.container_btn.clicked.connect(lambda: self.product_chosen.emit(
            ContainerWithWater(self.config.container_price_with_water)))

        # custom signals
        self.product_chosen.connect(self.add_product)
        self.product_chosen.connect(self.switch_on_choose_payment_window)
        self.product_chosen.connect(self.render_consumer_info)
        self.product_list_changed.connect(self.render_product_cart)

    def init_payment_signals(self) -> None:
        """
        Инициализация сигналов для оплаты:
        (банковской картой, наличными, картой лояльности, qr-код)
        """
        self.ui.cash_or_loyal_card_btn.clicked.connect(self.start_session)
        self.ui.cash_or_loyal_card_btn.clicked.connect(self.switch_on_cash_or_loyal_window)
        self.ui.bank_card_btn.clicked.connect(self.switch_on_bank_card_window)
        self.ui.qr_btn.clicked.connect(self.switch_on_qr_window)
        self.ui.qr_btn.clicked.connect(self.payment_started.emit)
        self.ui.bank_card_btn.clicked.connect(self.payment_started.emit)
        self.payment_canceled.connect(self.set_cancellation_time_to_initial_value)
        self.ui.cancel_payment_btn.clicked.connect(self.switch_on_choose_payment_window)
        self.ui.cancel_payment_btn.clicked.connect(self.render_consumer_info)
        self.ui.testing_success_payment_btn.clicked.connect(self.payment_succeed.emit)
        self.ui.testing_failed_payment_btn.clicked.connect(self.payment_failed.emit)

        self.ui.get_back_money_btn.clicked.connect(lambda: app.sgn_gui.RejectEscrow())
        self.ui.get_back_money_btn.clicked.connect(self.switch_on_choose_payment_window)
        self.ui.continue_without_change_btn.clicked.connect(lambda: app.sgn_gui.NominalIsHighContinue())
        self.ui.continue_without_change_btn.clicked.connect(lambda: self.payment_succeed.emit())
        self.no_money_left_to_change.connect(self.switch_on_not_enough_change_window)

        # custom signals
        self.deposit_balance_changed.connect(self.set_deposited_amount_cash)
        self.payment_succeed.connect(self.payment_cancellation_timer.stop)
        self.payment_succeed.connect(self.switch_on_success_payment_window)
        self.payment_succeed.connect(self.hide_cancel_payment_btn)
        self.payment_succeed.connect(lambda: self.set_total_price(sum([p.price for p in self._chosen_products])))

        self.payment_failed.connect(self.switch_on_failed_payment_window)
        self.payment_failed.connect(self.payment_cancellation_timer.stop)
        self.payment_failed.connect(self.set_cancellation_time_to_initial_value)

        self.payment_canceled.connect(self.switch_on_choose_payment_window)
        self.payment_cancellation_timer.timeout.connect(self.update_cancellation_time)
        self.session_timer.timeout.connect(self.update_session_time)
        self.payment_started.connect(lambda: self.payment_cancellation_timer.start(1000))
        self.session_started.connect(lambda: self.session_timer.start(1000))

    def init_pouring_signals(self) -> None:
        """
        Инициализация сигналов по наливу:
        (начать налив, остановить или продолжить налив, завершить налив)
        """
        self.ui.stop_btn.clicked.connect(self.switch_continue_stop_btn)
        self.ui.stop_btn.clicked.connect(self.stop_bottle_filling)
        self.ui.stop_btn.clicked.connect(self.update_flowed_liters_count)
        self.ui.continue_btn.clicked.connect(self.switch_continue_stop_btn)
        self.ui.continue_btn.clicked.connect(self.start_bottle_filling)

        self.flow_handler.liters_changed.connect(self.update_water_progres)

        self.ui.terminate_session_btn.clicked.connect(lambda: app.sgn_gui.EndSession() if app.sgn_gui['session']['started'] else None)
        self.ui.terminate_session_btn.clicked.connect(self.buy_window_closed.emit)
        self.ui.terminate_pouring_btn.clicked.connect(lambda: app.sgn_gui.AcknowlegeAmount(self.TOTAL_PRICE * 100))
        # self.ui.terminate_pouring_btn.clicked.connect(self.give_product_with_priority)
        # self.ui.terminate_pouring_btn.clicked.connect()
        self.ui.start_pouring_btn.clicked.connect(self.start_pouring)
        self.ui.start_pouring_btn.clicked.connect(lambda: self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.stop_page))

        # custom signals
        self.filling_started.connect(self.switch_on_water_bottle_window)
        self.filling_started.connect(self.start_bottle_filling)
        self.filling_started.connect(self.set_liter_progress_to_zero)

        self.bottle_progress_bar_widget.progress_changed.connect(self.update_remaining_price_for_water)
        self.filling_finished.connect(self.hide_continue_and_stop_filling_btn)
        self.filling_finished.connect(self.switch_on_water_bottle_window)
        self.filling_finished.connect(self.check_on_empty_water)

        self.ui.give_container_btn.clicked.connect(self.give_product_with_priority)
        self.ui.give_plug_btn.clicked.connect(self.give_product_with_priority)
        self.ui.give_loyal_card_btn.clicked.connect(self.give_product_with_priority)

    def update_flowed_liters_count(self):
        self.flowed_liter_count += self.last_current_liters_changed

    def set_liter_progress_to_zero(self):
        self.bottle_progress_bar_widget.progress = 0

    def check_on_empty_water(self):
        if not self._chosen_products:
            self.buy_window_closed.emit()

    def start_session(self):
        if not app.sgn_gui['session']['started']:
            app.sgn_gui.StartSession('CASH')
        app.sgn_gui.info(f'total price {sum([product.price for product in self._chosen_products])}')
        # передаем сумму заказа в копейках
        app.sgn_gui['session']['query_amount'] = sum([product.price for product in self._chosen_products]) * 100
        app.sgn_gui.ActivateCash()

    @pyqtProperty(QColor)
    def confirm_btn_color(self) -> QColor:
        """
        Getter для отрисовки анимации цвета кнопки начала покупок
        :return: текущий цвет кнопки начала покупок
        """
        return self._confirm_btn_color

    @confirm_btn_color.setter
    def confirm_btn_color(self, col: QColor) -> None:
        """
        Setter для отрисовки анимации цвета кнопки начала покупок
        :param col: новый цвет для кнопки начала покупок
        :return:
        """
        stylesheet = f'''
        background-color: rgb({col.red()}, {col.green()}, {col.blue()});
        border: 1px solid blue;
        border-top-right-radius: 35px;
        border-bottom-right-radius: 20px;
        border-top-left-radius: 20px;
        border-bottom-left-radius: 35px;
        '''
        self.ui.confirm_btn.setStyleSheet(stylesheet)
        self._confirm_btn_color = col

    def animate_confirm_btn(self) -> None:
        """
        Анимация кнопки начала покупок
        """
        self.animation_group = QSequentialAnimationGroup()
        self.first_animation = QPropertyAnimation(self, b'confirm_btn_color')
        self.second_animation = QPropertyAnimation(self, b'confirm_btn_color')

        self.first_animation.setDuration(2000)
        self.first_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.first_animation.setStartValue(QColor(245, 245, 245))
        self.first_animation.setEndValue(QColor(0, 105, 180))

        self.second_animation.setDuration(2000)
        self.second_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.second_animation.setStartValue(QColor(0, 105, 180))
        self.second_animation.setEndValue(QColor(245, 245, 245))

        self.animation_group.addAnimation(self.first_animation)
        self.animation_group.addAnimation(self.second_animation)

        self.animation_group.start()
        self.animation_group.setLoopCount(-1)

    def turn_on_dark_theme(self) -> None:
        """
        Переключение на темную тему
        """
        # set dark stylesheets
        dark_stylesheet = 'color: white; background-color: rgb(46, 62, 77); border: 1px solid #C0C0BF;'
        self.ui.frame.setStyleSheet('#frame{background-color: black;}')

        # set frame and btn to dark mode with curves turn to left
        [wgt.setStyleSheet(f'''
        #{wgt.objectName()} {{
            {dark_stylesheet}
            border-top-right-radius: 20px;
            border-top-left-radius: 35px;
            border-bottom-right-radius: 35px;
            border-bottom-left-radius: 20px;
        }}
        ''') for wgt in [
            self.ui.frame_22, self.ui.plus_btn, self.ui.frame_23, self.ui.minus_btn, self.ui.frame_14, self.ui.qr_btn,
            self.ui.top_up_card_btn,
        ]]

        # set frame and btn to dark mode with curves turn to right
        [wgt.setStyleSheet(f'''
        #{wgt.objectName()} {{
            {dark_stylesheet}
            border-top-right-radius: 35px;
            border-bottom-right-radius: 20px;
            border-top-left-radius: 20px;
            border-bottom-left-radius: 35px;
        }}
        ''') for wgt in [
            self.ui.choose_ltr_btn, self.ui.confirm_btn, self.ui.frame_15, self.ui.cash_or_loyal_card_btn,
            self.ui.frame_16, self.ui.bank_card_btn
        ]]

        # set main frames to dark mode
        [wgt.setStyleSheet(f'''
        #{wgt.objectName()} {{
            {dark_stylesheet}
        }}
        ''') for wgt in [self.ui.product_cart_frame, self.ui.frame_12, self.ui.frame_24, self.ui.frame_26,
                         self.ui.frame_25,self.ui.choose_payment_display_frame, self.ui.choose_ltr_display_frame,
                         self.ui.frame_11, self.ui.frame_18, self.ui.frame_28]]

        # set widgets to white color
        [wgt.setStyleSheet('color: white; background-color: transparent; border:0px;')
         for wgt in [self.ui.plug_ltr_btn, self.ui.container_ltr_btn, self.ui.loyal_card_btn, self.ui.container_btn,
                     self.ui.plug_btn, self.ui.init_cart_lbl, self.ui.datetime_lbl, self.ui.address_lbl,
                     self.ui.bottom_cart_lbl, self.ui.take_plug_lbl, self.ui.take_loyal_card_lbl,
                     self.ui.take_container_lbl, self.ui.chose_payment_lbl, self.ui.liters_count_lbl, self.ui.label,
                     self.ui.label_2, self.ui.label_4, self.ui.label_17, self.ui.payment_cancellation_lbl,
                     self.ui.cash_or_loyal_card_lbl, self.ui.label_3, self.ui.label_7, self.ui.label_8, self.ui.label_20,
                     self.ui.label_10, self.ui.label_18, self.ui.label_21, self.ui.label_19, self.ui.label_9,
                     self.bottle_progress_bar_widget.progress_lbl]]

        self.ui.frame_10.setStyleSheet(f'''
        #frame_10 {{
            {dark_stylesheet}
            border-top-right-radius: 20px;
            border-top-left-radius: 20px;
            border-bottom-right-radius: 35px;
            border-bottom-left-radius: 35px;
        }}
        ''')
        self.ui.frame_12.setStyleSheet(f'''
        #frame_12 {{
            {dark_stylesheet}
            border-top-right-radius: 35px;
            border-top-left-radius: 35px;
            border-bottom-right-radius: 15px;
            border-bottom-left-radius: 15px
        }}
        ''')

    def set_deposited_amount_cash(self):
        if self.ui.choosed_product_stack_widget.currentWidget() != self.ui.deposit_cash_page:
            self.ui.choosed_product_stack_widget.setCurrentWidget(self.ui.deposit_cash_page)
            self.ui.consumer_info_bottom_stack_widget.setCurrentWidget(self.ui.empty_consumer_bottom_page)

        if self.ui.product_price_stack_widget.currentWidget() != self.ui.product_price_page:
            self.ui.product_price_stack_widget.setCurrentWidget(self.ui.product_price_page)

        lbl = self.ui.product_price_lbl.text().split()
        lbl[0] = str(app.sgn_gui.nominal_to_text(
            app.sgn_gui['session']['cash_balance'] + app.sgn_gui['session']['escrow_balance']
        ))
        self.ui.product_price_lbl.setText(' '.join(lbl))

    def give_plug(self) -> None:
        """
        Отрисовка на основе выдачи пробки
        """
        self.ui.main_stack_widget.setCurrentWidget(self.ui.take_plug_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)
        self.set_total_price(self.TOTAL_PRICE - self.config.plug_price)
        app.sgn_gui.info('Выдана пробка')
        # self.plug_taken.emit()

    def give_container(self) -> None:
        """
        Отрисовка на основе выдачи тары
        """
        self.ui.main_stack_widget.setCurrentWidget(self.ui.take_container_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)
        self.set_total_price(self.TOTAL_PRICE - self.config.container_price)
        app.sgn_gui.info('Выдана тара')
        # self.container_taken.emit()

    def give_loyal_card(self) -> None:
        """
        Отрисовка на основе выдачи карты лояльности
        """
        self.ui.main_stack_widget.setCurrentWidget(self.ui.take_loyal_card_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)
        self.set_total_price(self.TOTAL_PRICE - self.config.loyal_card_price)
        app.sgn_gui.info('Выдана карта лояльности')
        # self.loyal_card_taken.emit()

    def give_product_with_priority(self) -> None:
        """
        Выдача продукта в зависимости от его категории, со следующим приоритетом
        1. Карта(-ы) лояльности
        2. Тара(-ы)
        3. Пробка(-и)
        4. Вода
        """

        # self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.start_pouring_page)
        self.sort_chosen_products()
        p = self._chosen_products.pop(0) if self._chosen_products else None

        if isinstance(p, LoyalCard):
            self._chosen_products = [p for p in self._chosen_products if not isinstance(p, LoyalCard)]
            self.give_loyal_card()
            return
        if isinstance(p, ContainerWithWater):
            # меняем все тары с водой на просто воду
            self._chosen_products = [
                p
                if not isinstance(p, ContainerWithWater)
                else Water(self.config.container_liters_count, self.config.water_price_per_liter)
                for p in self._chosen_products
            ]
            self.give_container()
            return
        if isinstance(p, PlugWithWater):
            # меняем все пробки с водой на просто воду без пробки
            self._chosen_products = [
                p
                if not isinstance(p, PlugWithWater) else Water(self.config.plug_liters_count, self.config.water_price_per_liter)
                for p in self._chosen_products
            ]
            self.give_plug()
            return
        # if isinstance(p, Water):
        #     self.set_total_price(sum([p.price for p in self._chosen_products]))
        #     self.last_popped_water = p
        #     app.sgn_gui.DepositAmount(self.last_popped_water.price * 100)
        #     return

        # self.buy_window_closed.emit()

    def start_pouring(self):
        self.set_total_price(sum([p.price for p in self._chosen_products]))
        self.last_popped_water = self._chosen_products.pop(0)
        app.sgn_gui.DepositAmount(self.last_popped_water.price * 100)
        self.filling_started.emit(self.last_popped_water)

    def add_product(self, product: Product) -> None:
        """
        Добавление продукта в корзину
        :param product: выбранный продукт
        """
        self._chosen_products.append(product)
        self.product_list_changed.emit()
        if len(self._chosen_products) == self.config.max_product_count:
            self.ui.add_more_btn.setEnabled(False)

    def remove_last_product(self) -> None:
        """
        Удаление последнего выбранного продукта
        """
        self._chosen_products.pop()
        self.product_list_changed.emit()
        self.ui.add_more_btn.setEnabled(True)
        if len(self._chosen_products) == 0:
            self.switch_on_cart_window()
        self.render_consumer_info()

    def sort_chosen_products(self):
        loyal_cards, containers, plugs, water = [], [], [], []
        for p in self._chosen_products:
            if isinstance(p, LoyalCard):
                loyal_cards.append(p)
            elif isinstance(p, ContainerWithWater):
                containers.append(p)
            elif isinstance(p, PlugWithWater):
                plugs.append(p)
            elif isinstance(p, Water):
                water.append(p)
        self._chosen_products = loyal_cards + containers + plugs + water

    def hide_cancel_payment_btn(self) -> None:
        """
        Спрятать кнопку отмены оплаты
        """
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bottom_right_second_empty_page)

    def update_water_progres(self, current_progress: float):
        self.last_current_liters_changed = current_progress
        temp = int(((current_progress + self.flowed_liter_count) / (self.last_popped_water.liters_count * 1000)) * 100)
        self.bottle_progress_bar_widget.progress = temp
        print(f'temp: {temp}')
        print(f'flowed_liter_count: {self.flowed_liter_count}')
        print(f'current_progress: {current_progress}')
        print(f'liters_count: {self.last_popped_water.liters_count}')

    def stop_bottle_filling(self) -> None:
        self.stop_bottle_filling_thread.run = self.flow_handler.stop_flow
        self.stop_bottle_filling_thread.start()

    def start_bottle_filling(self) -> None:
        """
        Начать отрисовку налива воды
        """
        self.bottle_filling_thread.run = lambda: self.flow_handler.run_flow((100 - self.bottle_progress_bar_widget.progress) * self.last_popped_water.liters_count * 10, 12.075)
        self.bottle_filling_thread.start()

    def render_product_cart(self) -> None:
        """
        Отрисовать весь текущий список выбранных товаров из корзины в меню выбранных товаров
        """
        for i in reversed(range(self.ui.product_layout.count())):
            self.ui.product_layout.itemAt(i).widget().deleteLater()

        for p in self._chosen_products:
            lbl = QLabel(p.name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumHeight(50)
            lbl.setFont(QFont('Rubik', 18))
            lbl.setStyleSheet(f'color: {"black" if UiConfig.is_light_theme() else "white"};')
            self.ui.product_layout.addWidget(lbl)

    def switch_continue_stop_btn(self) -> None:
        """
        Отрисовка кнопок "Остановить"/"Продолжить" для налива воды
        """
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(
            self.ui.stop_page if self.ui.bottom_left_btn_stack_widget.currentWidget() == self.ui.continue_page else self.ui.continue_page
        )

    # def render_after_filling_finished(self) -> None:
    #     if self._chosen_products:
    #         self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.start_pouring_page)
    #     else:
    #         self.buy_window_closed.emit()

    def hide_continue_and_stop_filling_btn(self) -> None:
        """
        Спрятать кнопки "Продолжить" и "Остановить" для налива
        """
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)

    def render_consumer_info(self) -> None:
        """
        Отрисовка выбранных товаров в меню предоплаты
        """
        consumer_header_page = self.ui.empty_consumer_bottom_page
        top_payment_hint_page = self.ui.empty_payment_page
        top_payment_price_page = self.ui.top_payment_empty_page

        product_page = self.ui.choosed_product_empty_page
        price_page = self.ui.product_price_empty_page

        if len(self._chosen_products) != 0:
            price_page = self.ui.product_price_page
            consumer_header_page = self.ui.bottom_cart_page

            lbl = self.ui.product_price_lbl.text().split()
            lbl[0] = str(self._chosen_products[-1].price)
            self.ui.product_price_lbl.setText(' '.join(lbl))

            top_payment_hint_page = self.ui.summary_page
            top_payment_price_page = self.ui.top_payment_summary_price_page
            lbl = self.ui.top_payment_summary_price_lbl.text().split()
            lbl[0] = str(sum([p.price for p in self._chosen_products]))
            self.ui.top_payment_summary_price_lbl.setText(' '.join(lbl))

            if isinstance(self._chosen_products[-1], Water):
                product_page = self.ui.choosed_water_page
                lbl = self.ui.choosed_water_lbl.text().split()
                lbl[1] = str(self._chosen_products[-1].liters_count)
                self.ui.choosed_water_lbl.setText(' '.join(lbl))

            elif isinstance(self._chosen_products[-1], PlugWithWater):
                product_page = self.ui.choosed_water_and_plug_page
                lbl = self.ui.choosed_water_and_plug_lbl.text().split()
                lbl[1] = str(self.config.plug_liters_count)
                self.ui.choosed_water_and_plug_lbl.setText(' '.join(lbl))

            elif isinstance(self._chosen_products[-1], ContainerWithWater):
                product_page = self.ui.choosed_water_and_container_page
                lbl = self.ui.choosed_water_and_container_lbl.text().split()
                lbl[1] = str(self.config.container_liters_count)
                self.ui.choosed_water_and_container_lbl.setText(' '.join(lbl))

            elif isinstance(self._chosen_products[-1], LoyalCard):
                product_page = self.ui.choosed_loyal_card_page

        self.ui.top_payment_hint_stack_widget.setCurrentWidget(top_payment_hint_page)
        self.ui.top_payment_price_stack_widget.setCurrentWidget(top_payment_price_page)

        self.ui.consumer_info_bottom_stack_widget.setCurrentWidget(consumer_header_page)
        self.ui.choosed_product_stack_widget.setCurrentWidget(product_page)
        self.ui.product_price_stack_widget.setCurrentWidget(price_page)

    def update_remaining_price_for_water(self, progress_percentage: int) -> None:
        """
        Отрисовка оставшейся общей суммы
        :param progress_percentage: колчиество в процентах от общей потраченной суммы
        """
        lbl = self.ui.top_payment_summary_price_lbl.text().split()
        water_summary_price = self._chosen_products[0].price if self._chosen_products else self.TOTAL_PRICE
        progress_percentage /= 100

        lbl[0] = str(round(self.TOTAL_PRICE - water_summary_price * progress_percentage, 2))
        self.ui.top_payment_summary_price_lbl.setText(' '.join(lbl))

        app.sgn_gui.info(f'progress: {self.bottle_progress_bar_widget.progress}')
        if self.bottle_progress_bar_widget.progress == 100:
            self.filling_finished.emit()

    def switch_on_success_payment_window(self) -> None:
        """
        Переключение на меню успешной оплаты
        """
        curr_wgt = self.ui.payment_stack_widget.currentWidget()

        if curr_wgt is self.ui.qr_payment_page:
            self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.qr_success_status_page)
        elif curr_wgt is self.ui.cash_or_loyal_card_page:
            self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.cash_or_loyal_card_success_status_page)
        elif curr_wgt is self.ui.bank_card_waiting_page:
            self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.bank_card_success_status_page)

        is_loyal_card_chosen = False
        is_plug_chosen = False
        is_container_chosen = False
        is_water_chosen = False
        for p in self._chosen_products:
            if isinstance(p, LoyalCard):
                is_loyal_card_chosen = True
            elif isinstance(p, PlugWithWater):
                is_plug_chosen = True
            elif isinstance(p, ContainerWithWater):
                is_container_chosen = True
            elif isinstance(p, Water):
                is_water_chosen = True

        self.ui.bottom_hints_stack_widget.setCurrentWidget(
            self.ui.container_hint_page if is_water_chosen else self.ui.empty_hint_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_right_page)
        self.ui.payment_stack_widget.setCurrentWidget(self.ui.payment_success_icon_page)

        if is_water_chosen:
            self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.start_pouring_page)
        if is_plug_chosen:
            self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.give_plug_page)
        if is_container_chosen:
            self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.give_container_page)
        if is_loyal_card_chosen:
            self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.give_loyal_card_page)

    def switch_on_failed_payment_window(self) -> None:
        """
        Переключение на меню при неуспешной оплате
        """
        curr_wgt = self.ui.payment_stack_widget.currentWidget()
        if curr_wgt is self.ui.cash_or_loyal_card_page:
            self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.cash_or_loyal_card_failed_status_page)
            self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.qr_page)
            self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bank_card_page)
        elif curr_wgt is self.ui.qr_payment_page:
            self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.qr_failed_status_page)
            self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.cash_loyal_card_page)
            self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bank_card_page)
        elif curr_wgt is self.ui.bank_card_waiting_page:
            self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.bank_card_failed_status_page)
            self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.cash_loyal_card_page)
            self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.qr_page)

        self.ui.payment_stack_widget.setCurrentWidget(self.ui.payment_failed_icon_page)
        self.ui.bottom_hints_stack_widget.setCurrentWidget(self.ui.empty_hint_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_right_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)

    def switch_on_bank_card_window(self) -> None:
        """
        Переключение на меню оплаты картой банка
        """
        self.ui.top_payment_hint_stack_widget.setCurrentWidget(self.ui.bank_card_hint_page)
        self.ui.main_stack_widget.setCurrentWidget(self.ui.payment_page)

        self.ui.payment_stack_widget.setCurrentWidget(self.ui.bank_card_waiting_page)
        self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.bank_card_waiting_status_page)
        self.ui.bottom_hints_stack_widget.setCurrentWidget(self.ui.payment_cancel_page)

        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_top_left_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.empty_second_top_left_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.empty_second_bottom_left_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)

        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.top_right_empty_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.top_right_second_empty_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bottom_right_second_empty_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_right_page)

        # self.TESTING_PAYMENT_RENDER()

    def switch_on_qr_window(self) -> None:
        """
        Переключение на меню оплаты по qr-коду
        """
        self.ui.top_payment_hint_stack_widget.setCurrentWidget(self.ui.qr_hint_page)
        self.ui.main_stack_widget.setCurrentWidget(self.ui.payment_page)

        self.ui.payment_stack_widget.setCurrentWidget(self.ui.qr_payment_page)
        self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.qr_waiting_status_page)
        self.ui.bottom_hints_stack_widget.setCurrentWidget(self.ui.payment_cancel_page)

        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_top_left_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.empty_second_top_left_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.empty_second_bottom_left_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)

        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.top_right_empty_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.top_right_second_empty_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bottom_right_second_empty_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_right_page)

        # self.TESTING_PAYMENT_RENDER()

    def switch_on_cash_or_loyal_window(self) -> None:
        """
        Переключение на меню оплаты наличными или картой лояльности
        """
        app.sgn_gui.info('Выбрана оплата наличными или по карте лояльности')
        self.set_deposited_amount_cash()

        self.ui.main_stack_widget.setCurrentWidget(self.ui.payment_page)
        self.ui.payment_stack_widget.setCurrentWidget(self.ui.cash_or_loyal_card_page)
        self.ui.top_payment_hint_stack_widget.setCurrentWidget(self.ui.cash_hint_page)
        self.ui.payment_status_stack_widget.setCurrentWidget(self.ui.cash_or_loyal_card_status_page)
        self.ui.bottom_hints_stack_widget.setCurrentWidget(self.ui.empty_hint_page)

        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_top_left_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.empty_second_top_left_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.empty_second_bottom_left_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)

        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.top_right_empty_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.top_right_second_empty_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bottom_right_second_empty_page)

        # self.TESTING_PAYMENT_RENDER()
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.cancel_payment_page)

    def switch_on_choose_payment_window(self) -> None:
        """
        Переключение на меню выбора способа оплаты
        """
        app.sgn_gui.info('Переход в меню выбора оплаты')
        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_top_left_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.add_more_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.empty_second_bottom_left_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.empty_bottom_left_page)

        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.cash_loyal_card_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.qr_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bank_card_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.back_page)

        self.ui.main_stack_widget.setCurrentWidget(self.ui.choose_payment_page)
        self.ui.top_payment_hint_stack_widget.setCurrentWidget(self.ui.summary_page)
        self.ui.top_payment_price_stack_widget.setCurrentWidget(self.ui.top_payment_summary_price_page)
        lbl = self.ui.top_payment_summary_price_lbl.text().split()
        lbl[0] = str(sum([p.price for p in self._chosen_products]))
        self.ui.top_payment_summary_price_lbl.setText(' '.join(lbl))

    def switch_on_not_enough_change_window(self) -> None:
        self.ui.main_stack_widget.setCurrentWidget(self.ui.no_money_change_page)
        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_top_left_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.empty_second_top_left_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.empty_second_bottom_left_page)

        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.top_right_empty_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.top_right_second_empty_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bottom_right_second_empty_page)

        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.get_back_money_page)
        self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.continue_without_change_page)

    def switch_on_cart_window(self) -> None:
        """
        Переключение на меню выбора товара
        """
        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.plug_ltr_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.choose_ltr_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.container_ltr_page)

        self.ui.top_payment_hint_stack_widget.setCurrentWidget(self.ui.empty_payment_page)
        self.ui.consumer_info_bottom_stack_widget.setCurrentWidget(self.ui.empty_consumer_bottom_page)
        self.ui.choosed_product_stack_widget.setCurrentWidget(self.ui.choosed_product_empty_page)
        self.ui.product_price_stack_widget.setCurrentWidget(self.ui.product_price_empty_page)
        self.ui.main_stack_widget.setCurrentWidget(self.ui.product_cart_page)

        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.container_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.loyal_card_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.plug_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.terminate_session_page)

        self.ui.top_payment_price_stack_widget.setCurrentWidget(self.ui.top_payment_empty_page)

    def switch_on_choose_window(self) -> None:
        """
        Переключение на меню выбора своего объема для налива воды
        """
        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.plus_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.confirm_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.minus_page)
        self.ui.main_stack_widget.setCurrentWidget(self.ui.choose_ltr_display_page)

    def switch_on_water_bottle_window(self):
        """
        Переключение на меню налива воды
        """

        def render_top_consumer_info():
            self.ui.top_payment_hint_stack_widget.setCurrentWidget(self.ui.remaining_amount_money_page)
            self.ui.top_payment_price_stack_widget.setCurrentWidget(self.ui.top_payment_summary_price_page)

        def render_bottom_consumer_info():
            self.ui.choosed_product_stack_widget.setCurrentWidget(self.ui.choosed_water_page)
            text = self.ui.choosed_water_lbl.text().split()
            text[1] = str(self.last_popped_water.liters_count)
            self.ui.choosed_water_lbl.setText(' '.join(text))

        self.ui.top_left_stack_widget.setCurrentWidget(self.ui.empty_top_left_page)
        self.ui.second_top_left_stack_widget.setCurrentWidget(self.ui.empty_second_top_left_page)
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.empty_second_bottom_left_page)
        self.ui.top_right_btn_stack_widget.setCurrentWidget(self.ui.top_right_empty_page)
        self.ui.top_right_second_stack_widget.setCurrentWidget(self.ui.top_right_second_empty_page)
        self.ui.bottom_right_second_stack_widget.setCurrentWidget(self.ui.bottom_right_second_empty_page)
        self.ui.bottom_right_btn_stack_widget.setCurrentWidget(self.ui.terminate_pouring_page)

        self.ui.main_stack_widget.setCurrentWidget(self.ui.bottle_page)
        self.ui.consumer_info_bottom_stack_widget.setCurrentWidget(self.ui.empty_consumer_bottom_page)
        self.ui.product_price_stack_widget.setCurrentWidget(self.ui.product_price_empty_page)

        render_top_consumer_info()
        render_bottom_consumer_info()

        if self._chosen_products:
            self.ui.bottom_left_btn_stack_widget.setCurrentWidget(self.ui.start_pouring_page)

        self.ui.bottle_layout.addWidget(self.bottle_progress_bar_widget)

    def increase_liters_count(self) -> None:
        """
        Увеличивает количество выбранных литров в дисплее налива до максимально возможного
        """
        count, liters_letter = self.ui.liters_count_lbl.text().split(' ')
        if int(count) < self.config.max_liters_count:
            self.ui.liters_count_lbl.setText(f'{int(count) + 1} {liters_letter}')

    def decrease_liters_count(self) -> None:
        """
        Уменьшает количество выбранных литров в дисплее налива до минимально возможного
        """
        count, liters_letter = self.ui.liters_count_lbl.text().split(' ')
        if int(count) > self.config.min_liters_count:
            self.ui.liters_count_lbl.setText(f'{int(count) - 1} {liters_letter}')

    def set_session_time_to_initial_value(self) -> None:
        """
        Устанавливает время сессии покупок в исходное значение
        """
        self._session_time = self.config.session_time

    def set_cancellation_time_to_initial_value(self) -> None:
        """
        Устанавливает время отмены оплаты в исходное значение
        """
        self._cancellation_time = self.config.cancellation_time

    def set_total_price(self, price: float):
        self.TOTAL_PRICE = price

    def update_cancellation_time(self) -> None:
        """
        Обновляет таймер отмены оплаты на дисплее, путем изменения предыдущего состояния
        """
        lbl_text = self.ui.payment_cancellation_lbl.text().split()
        self._cancellation_time -= 1
        if self._cancellation_time < 0:
            self.payment_cancellation_timer.stop()
            self.payment_canceled.emit()
            return
        minutes, secs = divmod(self._cancellation_time, 60)
        lbl_text[-1] = f'{"0" + str(minutes) if minutes < 10 else minutes}:{"0" + str(secs) if secs < 10 else secs}'
        self.ui.payment_cancellation_lbl.setText(' '.join(lbl_text))

    def update_session_time(self) -> None:
        """
        Обновляет таймер сессии покупок на дисплее, путем изменения предыдущего состояния
        """
        lbl_text = self.ui.datetime_lbl.text().split(' ')
        self._session_time -= 1
        if self._session_time < 0:
            self.session_timer.stop()
            self.session_timeout.emit()
            return
        minutes, secs = divmod(self._session_time, 60)
        lbl_text[-1] = f'{"0" + str(minutes) if minutes < 10 else minutes}:{"0" + str(secs) if secs < 10 else secs}'
        self.ui.datetime_lbl.setText(' '.join(lbl_text))
