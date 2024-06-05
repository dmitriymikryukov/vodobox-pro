import os


class NotImplementedCountryCode(Exception):
    pass


def get_translator_filepath(country_code: str):
    if country_code == 'RU':
        return ''
    elif country_code == 'EN':
        return os.path.join(os.getcwd(), '..', 'resources', 'translation', 'qm', 'applang_en')
    elif country_code == 'RO':
        return os.path.join(os.getcwd(), '..', 'resources', 'translation', 'qm', 'applang_ro')
    raise NotImplementedCountryCode(f'Неизвестный код страны: {country_code}')
