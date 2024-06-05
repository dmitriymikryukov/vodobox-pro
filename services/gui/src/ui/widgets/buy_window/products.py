from ui.widgets.translate_widget import TranslateWidget
from abc import ABC, abstractmethod


class Product(ABC):
    @property
    @abstractmethod
    def price(self) -> float:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class Water(Product):
    def __init__(self, liters_count: float, price_per_liter: float):
        self.liters_count = liters_count
        self._price_per_liter = price_per_liter

    @property
    def price(self) -> float:
        return self._price_per_liter * self.liters_count

    @property
    def name(self) -> str:
        code = TranslateWidget.CURRENT_LANGUAGE_CODE
        match code:
            case 'RU':
                return f'Вода {self.liters_count} Л'
            case 'RO':
                return f'Apă {self.liters_count} L'
            case 'EN':
                return f'Water {self.liters_count} L'


class PlugWithWater(Product):
    def __init__(self, plug_price):
        self._price = plug_price

    @property
    def price(self) -> float:
        return self._price

    @property
    def name(self) -> str:
        code = TranslateWidget.CURRENT_LANGUAGE_CODE
        match code:
            case 'RU':
                return 'Вода + Пробка'
            case 'RO':
                return 'Apă + Plută'
            case 'EN':
                return 'Water + Plug'


class ContainerWithWater(Product):
    def __init__(self, container_price):
        self._price = container_price

    @property
    def price(self) -> float:
        return self._price

    @property
    def name(self) -> str:
        code = TranslateWidget.CURRENT_LANGUAGE_CODE
        match code:
            case 'RU':
                return 'Вода + Тара'
            case 'RO':
                return 'Apă + Container'
            case 'EN':
                return 'Water + Container'


class LoyalCard(Product):
    def __init__(self, loyal_card_price):
        self._price = loyal_card_price

    @property
    def price(self) -> float:
        return self._price

    @property
    def name(self) -> str:
        code = TranslateWidget.CURRENT_LANGUAGE_CODE
        match code:
            case 'RU':
                return 'Карта лояльности'
            case 'RO':
                return 'Card De Fidelitate'
            case 'EN':
                return 'Loyal card'
