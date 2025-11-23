"""Модуль с вспомогательными функциями для работы с данными.

Этот модуль содержит функции для загрузки данных из Excel,
работы с датами, JSON и API.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Константы модуля
ENCODING = "utf-8"
DATE_OPERATION_FORMAT = "%d.%m.%Y %H:%M:%S"
DATE_PAYMENT_FORMAT = "%d.%m.%Y"
DATE_FORMAT = "%d.%m.%Y"
DATE_FORMAT_OUTPUT = "%d.%m.%Y"
FILE_WRITE_MODE = "w"
FILE_READ_MODE = "r"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_RETURN_VALUE: List[Dict[str, Any]] = []
DEFAULT_RETURN_DICT: Dict[str, Any] = {}
DEFAULT_API_KEY_PLACEHOLDER = "your_api_key_here"
DEFAULT_API_URL = "https://api.exchangerate-api.com/v4"
ALPHA_VANTAGE_API_URL = "https://www.alphavantage.co/query"
REQUEST_TIMEOUT = 10
STOCK_REQUEST_DELAY = 0.2
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
USER_SETTINGS_FILE = "user_settings.json"


def _setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля utils.

    Returns:
        Настроенный логгер для модуля utils
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "utils.log"
    file_handler = logging.FileHandler(log_file, mode=FILE_WRITE_MODE, encoding=ENCODING)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=TIMESTAMP_FORMAT,
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


# Создаем логгер для модуля
logger = _setup_logger()


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
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
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
    logger.info("Загрузка настроек пользователя")

    if not os.path.exists(USER_SETTINGS_FILE):
        logger.warning(f"Файл {USER_SETTINGS_FILE} не найден. Возвращаем пустой словарь.")
        return DEFAULT_RETURN_DICT

    try:
        with open(USER_SETTINGS_FILE, FILE_READ_MODE, encoding=ENCODING) as f:
            settings: Dict[str, Any] = json.load(f)

        logger.info(f"Настройки успешно загружены из {USER_SETTINGS_FILE}")
        return settings

    except json.JSONDecodeError as e:
        error_msg = f"Ошибка парсинга JSON в файле {USER_SETTINGS_FILE}"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        return DEFAULT_RETURN_DICT
    except Exception as e:
        error_msg = f"Ошибка при загрузке настроек из {USER_SETTINGS_FILE}"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        return DEFAULT_RETURN_DICT


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
        with open(file_path, FILE_WRITE_MODE, encoding=ENCODING) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Данные успешно сохранены в {Path(file_path).name}")

    except OSError as e:
        error_msg = f"Ошибка при сохранении файла {Path(file_path).name}"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        raise
    except Exception as e:
        error_msg = "Неожиданная ошибка при сохранении JSON"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
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

    if not currencies:
        logger.warning("Список валют пуст")
        return DEFAULT_RETURN_VALUE

    # Загрузка API ключа из переменных окружения
    api_key = os.getenv("API_KEY")
    api_url = os.getenv("API_URL", DEFAULT_API_URL)

    try:
        # Формирование URL для запроса
        # Для exchangerate-api.com можно использовать без ключа (бесплатный tier)
        if "exchangerate-api.com" in api_url:
            # Бесплатный API exchangerate-api.com - используем базовую валюту RUB
            base_currency = "RUB"
            url = f"{api_url}/latest/{base_currency}"
            params = {}  # Не требует ключа для базового использования
            logger.debug("Использование бесплатного API exchangerate-api.com")
        else:
            # Другие API требуют ключ
            if not api_key or api_key == DEFAULT_API_KEY_PLACEHOLDER:
                error_msg = "API ключ не найден или не установлен"
                logger.error(error_msg)
                return DEFAULT_RETURN_VALUE
            symbols = ",".join(currencies)
            url = f"{api_url}/latest"
            params = {"access_key": api_key, "symbols": symbols}

        logger.debug(f"Запрос к API: {url}")

        # Выполнение запроса
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

        # Проверка статуса ответа
        response.raise_for_status()

        data = response.json()

        # Обработка ответа API
        rates: List[Dict[str, Any]] = []
        # Поддержка разных форматов ответа API
        if "rates" in data:
            # Формат exchangerate-api.com и подобных
            for currency in currencies:
                if currency in data["rates"]:
                    rates.append({"currency": currency, "rate": data["rates"][currency]})
                else:
                    logger.warning(f"Курс для валюты {currency} не найден в ответе API")
        elif "conversion_rates" in data:
            # Альтернативный формат
            for currency in currencies:
                if currency in data["conversion_rates"]:
                    rates.append({"currency": currency, "rate": data["conversion_rates"][currency]})
        else:
            logger.warning(f"Неожиданный формат ответа API. Доступные ключи: {list(data.keys())}")
            return DEFAULT_RETURN_VALUE

        logger.info(f"Получено курсов валют: {len(rates)}")
        return rates

    except requests.exceptions.RequestException as e:
        error_msg = "Ошибка при запросе к API валют"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        return DEFAULT_RETURN_VALUE
    except json.JSONDecodeError as e:
        error_msg = "Ошибка парсинга JSON ответа от API"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        return DEFAULT_RETURN_VALUE
    except Exception as e:
        error_msg = "Неожиданная ошибка при получении курсов валют"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        return DEFAULT_RETURN_VALUE


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие цены акций через Alpha Vantage API.

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

    if not stocks:
        logger.warning("Список акций пуст")
        return DEFAULT_RETURN_VALUE

    # Загрузка API ключа из переменных окружения
    api_key = os.getenv("API_KEY")

    if not api_key or api_key == DEFAULT_API_KEY_PLACEHOLDER:
        error_msg = "API ключ не найден или не установлен"
        logger.error(error_msg)
        return DEFAULT_RETURN_VALUE

    prices: List[Dict[str, Any]] = []

    # Alpha Vantage требует отдельный запрос для каждой акции
    # (или можно использовать BATCH_QUOTES, но GLOBAL_QUOTE проще)
    for stock in stocks:
        try:
            # Формирование параметров для Alpha Vantage
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": stock,
                "apikey": api_key,
            }

            logger.debug(f"Запрос к Alpha Vantage API для {stock}")

            # Выполнение запроса
            response = requests.get(ALPHA_VANTAGE_API_URL, params=params, timeout=REQUEST_TIMEOUT)

            # Проверка статуса ответа
            response.raise_for_status()

            data = response.json()

            # Обработка ответа Alpha Vantage
            # Формат: {"Global Quote": {"01. symbol": "AAPL", "05. price": "150.12", ...}}
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                # Alpha Vantage возвращает цену в поле "05. price"
                price_str = quote.get("05. price", "")
                if price_str:
                    try:
                        price = float(price_str)
                        prices.append({"stock": stock, "price": price})
                        logger.debug(f"Получена цена для {stock}: {price}")
                    except ValueError:
                        logger.warning(f"Некорректный формат цены для {stock}: {price_str}")
                else:
                    logger.warning(f"Цена не найдена в ответе API для {stock}")
            elif "Error Message" in data:
                error_msg = data.get("Error Message", "Неизвестная ошибка API")
                logger.warning(f"Ошибка API для {stock}: {error_msg}")
            elif "Note" in data:
                # Alpha Vantage может вернуть сообщение о лимите запросов
                # Не логируем это сообщение, так как оно содержит API ключ
                # Это просто информационное сообщение о лимите запросов
                pass
            else:
                logger.warning(f"Неожиданный формат ответа API для {stock}")

            # Небольшая задержка между запросами (Alpha Vantage имеет лимит 5 запросов/минуту для бесплатного плана)
            time.sleep(STOCK_REQUEST_DELAY)

        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка при запросе к API для акции {stock}"
            logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON ответа от API для {stock}"
            logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        except Exception as e:
            error_msg = f"Неожиданная ошибка при получении цены для {stock}"
            logger.error(f"{error_msg}: {type(e).__name__} - {e}")

    logger.info(f"Получено цен акций: {len(prices)} из {len(stocks)}")
    return prices
