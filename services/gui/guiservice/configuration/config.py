import json
import os


class ServiceMenuConfig:
    """
    Тестовый класс конфигураций для сервисного меню
    """
    @property
    def password(self) -> list[int]:
        """
        Пароль для перехода в сервисное меню.
        *Представлен в виде количества нажатий по кнопкам на позициях 2, 3, 6, 7 (смотреть схему)
        ** Пример: пароль 1211 - 1 нажатие по кнопке на позиции два, 2 нажатия по кнопке на позиции три,
        1 нажатие по кнопке на позиции шесть, 1 нажатие по кнопке на позиции семь.
        *Примечание: если кнопка покупки находится на позиции 6, то в пароле конфигурации необходимо, чтобы был
        ноль на месте третьей или четвертой цифры (пример: 1101 или 1110) иначе происходит переход в меню выбора товара

        :return: пароль в виде списка
        """
        return [1, 1, 1, 1]


class UiConfig:
    """
    Тестовый класс конфигураций для глобального UI интерфейса
    """
    _session_config = json.load(open(os.path.join(os.getcwd(), 'configuration', 'test', 'session_config.json')))
    _consumer_info_config = json.load(open(os.path.join(os.getcwd(), 'configuration', 'test', 'consumer_info_config.json')))
    _language_config = json.load(open(os.path.join(os.getcwd(), 'configuration', 'test', 'language_config.json')))
    _logo_config = json.load(open(os.path.join(os.getcwd(), 'configuration', 'test', 'logo_config.json')))
    _common_settings_config = json.load(open(os.path.join(os.getcwd(), 'configuration', 'test', 'common_settings_config.json')))

    @staticmethod
    def buy_btn_position() -> int:
        """
        Возвращает положение кнопки покупки, возможные значения 6 или 7 (смотреть схему)
        :return: Положение кнопки начала покупки
        """
        return UiConfig._session_config['session_begin']['button']
    
    @staticmethod
    def consumer_info_show_btn() -> bool:
        """
        Отвечает за отображение кнопки перехода на окно информации о производителе
        :return: Статус отображения
        """
        return UiConfig._consumer_info_config['info']['button']

    @staticmethod
    def translate_show_btn() -> bool:
        """
        Отвечает за отображение кнопки перевода языка интерфейса
        :return: Статус отображения
        """
        return UiConfig._language_config['lang']['button']

    @staticmethod
    def logotype() -> str:
        """
        Логотип компании, который будет расположен на главном экране меню ожидания
        :return: Название файла логотипа
        """
        return UiConfig._logo_config['logotype']

    @staticmethod
    def is_light_theme() -> bool:
        """
        Отвечает за переключение между светлой и темной темой
        :return: статус светлой темы
        """
        return UiConfig._common_settings_config['is_light_theme']

    @staticmethod
    def kiosk_address() -> str:
        """
        :return: Адрес киоска
        """
        return UiConfig._consumer_info_config['post_address']

    @staticmethod
    def seller_name() -> str:
        """
        :return: Имя продовца
        """
        return UiConfig._consumer_info_config['seller_name']

    @staticmethod
    def water_created_date() -> str:
        """
        :return: Дата производства воды
        """
        return UiConfig._consumer_info_config['water_created_date']

    @staticmethod
    def water_refill_date() -> str:
        """
        :return: Дата заправки воды
        """
        return UiConfig._consumer_info_config['water_refill_date']

    @staticmethod
    def wash_dates() -> tuple[str, str, str]:
        """
        :return: Даты моек емкости
        """
        return UiConfig._consumer_info_config['wash_dates']

    @staticmethod
    def default_language_code() -> str:
        """
        :return: Код языка по умолчанию возможные значения (RU | RO | EN)
        """
        return UiConfig._language_config['lang']['default'].upper()

    @staticmethod
    def second_language_code() -> str:
        """
        :return: Код второго языка для перевода возможные значения (RU | RO | EN)
        """
        return UiConfig._language_config['lang']['change'][1].upper()

    @staticmethod
    def third_language_code() -> str:
        """
        :return: Код третьего языка для перевода возможные значения (RU | RO | EN)
        """
        return UiConfig._language_config['lang']['change'][2].upper()


class BuyConfig:
    """
    Тестовый класс конфигураций для меню покупок
    """
    def __init__(self):
        self._cancellation_time: int = 40

    @property
    def water_price_per_liter(self) -> float:
        """
        :return: Цена воды за литр
        """
        return 5

    @property
    def container_price(self) -> float:
        """
        :return: Цена за тару
        """
        return 50

    @property
    def container_price_with_water(self) -> float:
        """
        :return: Цена за тару с водой
        """
        return self.container_price + self.water_price_per_liter * self.container_liters_count

    @property
    def loyal_card_price(self) -> float:
        """
        :return: Цена за карту лояльности
        """
        return 100

    @property
    def plug_price(self) -> float:
        """
        :return: Цена за пробку
        """
        return 20

    @property
    def plug_price_with_water(self) -> float:
        """
        :return: Цена за пробку с водой
        """
        return self.plug_price + self.water_price_per_liter * self.plug_liters_count

    @property
    def container_liters_count(self) -> int:
        """
        :return: Количество литров для тары
        """
        return 5

    @property
    def plug_liters_count(self) -> int:
        """
        :return: Количество литров для пробки
        """
        return 19

    @property
    def max_product_count(self) -> int:
        """
        :return: Максимальное количество продуктов в корзине выбранных товаров
        """
        return 5

    @property
    def max_liters_count(self) -> int:
        """
        :return: Максимальное количество литров, которое может выбрать пользователь
        """
        return 100

    @property
    def min_liters_count(self) -> int:
        """
        :return: Минимальное количество литров, которое может выбрать пользователь
        """
        return 1

    @property
    def session_time(self) -> int:
        """
        :return: Время сессии для покупок в секундах
        """
        return 5 * 60

    @property
    def cancellation_time(self) -> int:
        """
        Getter функция для получения времени, через которое можно произвести отмену оплаты (QR, Карта банка)
        :return: Время для отмены оплаты
        """
        return self._cancellation_time

    @cancellation_time.setter
    def cancellation_time(self, seconds: int) -> None:
        """
        Setter функция для установки времени, через которое можно произвести отмену оплаты (QR, Карта банка)
        :param seconds: Оставшееся время в секундах
        """
        if seconds < 0:
            raise ValueError('Неверное значение для времени отмены оплаты')
        self._cancellation_time = seconds
