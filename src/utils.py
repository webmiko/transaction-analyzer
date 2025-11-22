"""Модуль с вспомогательными функциями для работы с данными.

Этот модуль содержит функции для загрузки данных из Excel,
работы с датами, JSON и API.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]

from src.logger_config import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

# Константы
ENCODING = "utf-8"
DATE_OPERATION_FORMAT = "%d.%m.%Y %H:%M:%S"
DATE_PAYMENT_FORMAT = "%d.%m.%Y"
DATE_FORMAT = "%d.%m.%Y"
DATE_FORMAT_OUTPUT = "%d.%m.%Y"
REQUIRED_COLUMNS = [
    "Дата операции",
    "Дата платежа",
    "Номер карты",
    "Статус",
    "Сумма операции",
    "Валюта операции",
    "Сумма платежа",
    "Валюта платежа",
    "Кэшбэк",
    "Категория",
    "MCC",
    "Описание",
    "Бонусы (включая кэшбэк)",
    "Округление на инвесткопилку",
    "Сумма операции с округлением",
]


def load_transactions_from_excel(file_path: str) -> pd.DataFrame:
    """
    Загружает транзакции из Excel-файла и возвращает DataFrame.

    Функция загружает данные из Excel-файла, обрабатывает формат дат
    и выполняет валидацию данных. Логирует операции без конфиденциальных данных.

    Args:
        file_path: Путь к Excel-файлу с транзакциями

    Returns:
        DataFrame с транзакциями. Возвращает пустой DataFrame при ошибке.

    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если файл не содержит необходимых колонок

    Example:
        >>> df = load_transactions_from_excel("data/operations.xlsx")
        >>> print(df.shape)
        (100, 15)
    """
    logger.info("Начало загрузки транзакций из файла")

    # Проверка существования файла
    if not os.path.exists(file_path):
        error_msg = "Файл не найден"
        logger.error(f"{error_msg}: {Path(file_path).name}")
        raise FileNotFoundError(f"{error_msg}: {file_path}")

    try:
        # Загрузка данных из Excel
        logger.debug(f"Чтение Excel-файла: {Path(file_path).name}")
        df = pd.read_excel(file_path, engine="openpyxl")

        # Валидация: проверка наличия необходимых колонок
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            error_msg = f"Отсутствуют необходимые колонки: {', '.join(missing_columns)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Загружено строк: {len(df)}")

        # Обработка формата дат
        logger.debug("Обработка формата дат")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format=DATE_OPERATION_FORMAT, errors="coerce")
        df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], format=DATE_PAYMENT_FORMAT, errors="coerce")

        # Проверка успешности парсинга дат
        invalid_dates_operation = df["Дата операции"].isna().sum()
        invalid_dates_payment = df["Дата платежа"].isna().sum()

        if invalid_dates_operation > 0:
            logger.warning(f"Найдено некорректных дат операции: {invalid_dates_operation}")
        if invalid_dates_payment > 0:
            logger.warning(f"Найдено некорректных дат платежа: {invalid_dates_payment}")

        # Валидация: проверка на пустой DataFrame
        if df.empty:
            logger.warning("Загружен пустой файл")
            return df

        logger.info(f"Загрузка завершена успешно: {len(df)} транзакций")
        return df

    except FileNotFoundError:
        # Повторно пробрасываем FileNotFoundError
        raise
    except ValueError:
        # Повторно пробрасываем ValueError (валидация колонок)
        raise
    except Exception as e:
        error_msg = "Ошибка при загрузке файла"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        # Возвращаем пустой DataFrame вместо проброса исключения
        return pd.DataFrame()


def parse_date(date_string: str) -> datetime:
    """
    Парсит дату из строки формата DD.MM.YYYY.

    Args:
        date_string: Строка с датой в формате DD.MM.YYYY

    Returns:
        Объект datetime с распарсенной датой

    Raises:
        ValueError: Если строка не соответствует формату DD.MM.YYYY

    Example:
        >>> date = parse_date("15.03.2024")
        >>> print(date)
        2024-03-15 00:00:00
    """
    try:
        parsed_date = datetime.strptime(date_string, DATE_FORMAT)
        logger.debug(f"Успешно распарсена дата: {date_string}")
        return parsed_date
    except ValueError as e:
        error_msg = f"Некорректный формат даты: {date_string}"
        logger.error(f"{error_msg}. Ожидается формат: {DATE_FORMAT}")
        raise ValueError(error_msg) from e


def format_date(date: datetime) -> str:
    """
    Форматирует дату в строку формата DD.MM.YYYY.

    Args:
        date: Объект datetime для форматирования

    Returns:
        Строка с датой в формате DD.MM.YYYY

    Example:
        >>> date = datetime(2024, 3, 15)
        >>> formatted = format_date(date)
        >>> print(formatted)
        15.03.2024
    """
    formatted = date.strftime(DATE_FORMAT_OUTPUT)
    logger.debug(f"Дата отформатирована: {formatted}")
    return formatted


def get_month_start(date: datetime) -> datetime:
    """
    Возвращает начало месяца для указанной даты.

    Args:
        date: Дата, для которой нужно найти начало месяца

    Returns:
        Объект datetime с началом месяца (первый день, 00:00:00)

    Example:
        >>> date = datetime(2024, 3, 15, 14, 30, 0)
        >>> month_start = get_month_start(date)
        >>> print(month_start)
        2024-03-01 00:00:00
    """
    month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    logger.debug(f"Начало месяца для {date.strftime(DATE_FORMAT_OUTPUT)}: {month_start.strftime(DATE_FORMAT_OUTPUT)}")
    return month_start


def get_month_range(date: datetime) -> Tuple[datetime, datetime]:
    """
    Возвращает диапазон месяца (начало и конец) для указанной даты.

    Args:
        date: Дата, для которой нужно найти диапазон месяца

    Returns:
        Кортеж (начало_месяца, конец_месяца)
        Конец месяца - последний день месяца, 23:59:59

    Example:
        >>> date = datetime(2024, 3, 15)
        >>> start, end = get_month_range(date)
        >>> print(start, end)
        2024-03-01 00:00:00 2024-03-31 23:59:59
    """
    month_start = get_month_start(date)

    # Вычисляем начало следующего месяца
    if date.month == 12:
        next_month_start = datetime(date.year + 1, 1, 1)
    else:
        next_month_start = datetime(date.year, date.month + 1, 1)

    # Конец месяца = начало следующего месяца минус 1 секунда
    month_end = next_month_start - timedelta(seconds=1)

    logger.debug(
        f"Диапазон месяца для {date.strftime(DATE_FORMAT_OUTPUT)}: "
        f"{month_start.strftime(DATE_FORMAT_OUTPUT)} - {month_end.strftime(DATE_FORMAT_OUTPUT)}"
    )
    return (month_start, month_end)


def get_three_months_back(date: datetime) -> Tuple[datetime, datetime]:
    """
    Возвращает диапазон последних 3 месяцев от указанной даты.

    Args:
        date: Дата, от которой отсчитываются последние 3 месяца

    Returns:
        Кортеж (начало_периода, конец_периода)
        Начало периода - начало месяца, который был 3 месяца назад
        Конец периода - конец указанного месяца

    Example:
        >>> date = datetime(2024, 3, 15)
        >>> start, end = get_three_months_back(date)
        >>> # Вернет период с начала декабря 2023 по конец марта 2024
    """
    # Конец периода - конец указанного месяца
    _, period_end = get_month_range(date)

    # Начало периода - начало месяца, который был 3 месяца назад
    # Вычисляем дату 3 месяца назад
    if date.month <= 3:
        # Если текущий месяц <= 3, нужно перейти в предыдущий год
        start_year = date.year - 1
        start_month = date.month + 9  # 12 - 3 + date.month
    else:
        start_year = date.year
        start_month = date.month - 3

    period_start = datetime(start_year, start_month, 1, 0, 0, 0)

    logger.debug(
        f"Диапазон последних 3 месяцев от {date.strftime(DATE_FORMAT_OUTPUT)}: "
        f"{period_start.strftime(DATE_FORMAT_OUTPUT)} - {period_end.strftime(DATE_FORMAT_OUTPUT)}"
    )
    return (period_start, period_end)


def load_user_settings() -> Dict[str, Any]:
    """
    Загружает настройки пользователя из файла user_settings.json.

    Returns:
        Словарь с настройками пользователя. Возвращает пустой словарь при ошибке.

    Example:
        >>> settings = load_user_settings()
        >>> print(settings.get('user_currencies'))
        ['USD', 'EUR']
    """
    settings_file = "user_settings.json"
    logger.info("Загрузка настроек пользователя")

    try:
        if not os.path.exists(settings_file):
            logger.warning(f"Файл {settings_file} не найден. Возвращаем пустой словарь.")
            return {}

        with open(settings_file, "r", encoding=ENCODING) as f:
            settings: Dict[str, Any] = json.load(f)

        logger.info(f"Настройки успешно загружены из {settings_file}")
        return settings

    except json.JSONDecodeError as e:
        error_msg = f"Ошибка парсинга JSON в файле {settings_file}"
        logger.error(f"{error_msg}: {e}")
        return {}
    except Exception as e:
        error_msg = f"Ошибка при загрузке настроек из {settings_file}"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        return {}


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """
    Сохраняет данные в JSON-файл.

    Args:
        data: Словарь с данными для сохранения
        file_path: Путь к файлу для сохранения

    Raises:
        OSError: Если не удалось создать или записать файл

    Example:
        >>> data = {"key": "value"}
        >>> save_json(data, "output.json")
    """
    logger.info(f"Сохранение данных в JSON-файл: {Path(file_path).name}")

    try:
        with open(file_path, "w", encoding=ENCODING) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Данные успешно сохранены в {Path(file_path).name}")

    except OSError as e:
        error_msg = f"Ошибка при сохранении файла {Path(file_path).name}"
        logger.error(f"{error_msg}: {e}", exc_info=True)
        raise
    except Exception as e:
        error_msg = "Неожиданная ошибка при сохранении JSON"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        raise


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие курсы валют через API.

    Использует эндпоинт /latest для получения актуальных курсов.
    API ключ загружается из переменной окружения API_KEY.

    Args:
        currencies: Список кодов валют (например, ['USD', 'EUR'])

    Returns:
        Список словарей с курсами валют. Каждый словарь содержит:
        - currency: код валюты
        - rate: курс валюты
        Возвращает пустой список при ошибке.

    Example:
        >>> rates = get_currency_rates(['USD', 'EUR'])
        >>> print(rates)
        [{'currency': 'USD', 'rate': 73.21}, {'currency': 'EUR', 'rate': 87.08}]
    """
    logger.info(f"Запрос курсов валют: {', '.join(currencies)}")

    # Загрузка API ключа из переменных окружения
    api_key = os.getenv("API_KEY")
    api_url = os.getenv("API_URL", "https://api.exchangerate-api.com/v4")

    if not api_key:
        error_msg = "API ключ не найден в переменных окружения"
        logger.error(error_msg)
        return []

    if not currencies:
        logger.warning("Список валют пуст")
        return []

    try:
        # Формирование URL для запроса
        symbols = ",".join(currencies)
        url = f"{api_url}/latest"
        params = {"access_key": api_key, "symbols": symbols}

        logger.debug(f"Запрос к API: {url}")

        # Выполнение запроса
        response = requests.get(url, params=params, timeout=10)

        # Проверка статуса ответа
        response.raise_for_status()

        data = response.json()

        # Обработка ответа API
        rates = []
        if "rates" in data:
            for currency in currencies:
                if currency in data["rates"]:
                    rates.append({"currency": currency, "rate": data["rates"][currency]})
                else:
                    logger.warning(f"Курс для валюты {currency} не найден в ответе API")
        else:
            logger.warning("В ответе API отсутствует поле 'rates'")
            return []

        logger.info(f"Получено курсов валют: {len(rates)}")
        return rates

    except requests.exceptions.RequestException as e:
        error_msg = "Ошибка при запросе к API валют"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        return []
    except json.JSONDecodeError as e:
        error_msg = "Ошибка парсинга JSON ответа от API"
        logger.error(f"{error_msg}: {e}")
        return []
    except Exception as e:
        error_msg = "Неожиданная ошибка при получении курсов валют"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        return []


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие цены акций через API.

    API ключ загружается из переменной окружения API_KEY.

    Args:
        stocks: Список тикеров акций (например, ['AAPL', 'AMZN'])

    Returns:
        Список словарей с ценами акций. Каждый словарь содержит:
        - stock: тикер акции
        - price: цена акции
        Возвращает пустой список при ошибке.

    Example:
        >>> prices = get_stock_prices(['AAPL', 'AMZN'])
        >>> print(prices)
        [{'stock': 'AAPL', 'price': 150.12}, {'stock': 'AMZN', 'price': 3173.18}]
    """
    logger.info(f"Запрос цен акций: {', '.join(stocks)}")

    # Загрузка API ключа из переменных окружения
    api_key = os.getenv("API_KEY")
    api_url = os.getenv("API_URL", "https://api.example.com")

    if not api_key:
        error_msg = "API ключ не найден в переменных окружения"
        logger.error(error_msg)
        return []

    if not stocks:
        logger.warning("Список акций пуст")
        return []

    try:
        # Формирование URL для запроса
        symbols = ",".join(stocks)
        url = f"{api_url}/stocks"
        params = {"apikey": api_key, "symbols": symbols}

        logger.debug(f"Запрос к API: {url}")

        # Выполнение запроса
        response = requests.get(url, params=params, timeout=10)

        # Проверка статуса ответа
        response.raise_for_status()

        data = response.json()

        # Обработка ответа API (структура зависит от конкретного API)
        prices = []
        if isinstance(data, list):
            # Если API возвращает список
            for item in data:
                if "symbol" in item and "price" in item:
                    prices.append({"stock": item["symbol"], "price": item["price"]})
        elif isinstance(data, dict):
            # Если API возвращает словарь
            for stock in stocks:
                if stock in data:
                    prices.append({"stock": stock, "price": data[stock]})
                else:
                    logger.warning(f"Цена для акции {stock} не найдена в ответе API")
        else:
            logger.warning("Неожиданный формат ответа от API акций")
            return []

        logger.info(f"Получено цен акций: {len(prices)}")
        return prices

    except requests.exceptions.RequestException as e:
        error_msg = "Ошибка при запросе к API акций"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        return []
    except json.JSONDecodeError as e:
        error_msg = "Ошибка парсинга JSON ответа от API"
        logger.error(f"{error_msg}: {e}")
        return []
    except Exception as e:
        error_msg = "Неожиданная ошибка при получении цен акций"
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        return []
