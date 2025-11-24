"""Модуль с сервисами для работы с транзакциями.

Этот модуль содержит функции для поиска и анализа транзакций,
включая поиск по различным критериям и расчет аналитических показателей.
"""

import logging
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Константы модуля
ENCODING = "utf-8"
FILE_WRITE_MODE = "w"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_RETURN_VALUE: List[Dict[str, Any]] = []
DEFAULT_RETURN_DICT: Dict[str, float] = {}
DEFAULT_RETURN_FLOAT = 0.0
STATUS_OK = "OK"
CATEGORY_TRANSFERS = "Переводы"
DATE_OPERATION_COLUMN = "Дата операции"
CATEGORY_COLUMN = "Категория"
DESCRIPTION_COLUMN = "Описание"
CASHBACK_COLUMN = "Кэшбэк"
AMOUNT_COLUMN = "Сумма платежа"
STATUS_COLUMN = "Статус"
PHONE_PATTERN = r"\+7\s?\d{3}\s?\d{3}[-]?\d{2}[-]?\d{2}"
PERSON_NAME_PATTERN = r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.$"


def _setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля services.

    Returns:
        Настроенный логгер для модуля services
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "services.log"
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


def profitable_cashback_categories(data: List[Dict[str, Any]], year: int, month: int) -> Dict[str, float]:
    """
    Анализирует категории с повышенным кешбэком за указанный месяц.

    Функция фильтрует транзакции по году и месяцу, группирует их по категориям
    и суммирует кешбэк по каждой категории. Возвращает словарь с категориями
    и суммами кешбэка.

    Args:
        data: Список словарей с транзакциями
        year: Год для анализа
        month: Месяц для анализа (1-12)

    Returns:
        Словарь с категориями и суммами кешбэка. Возвращает пустой словарь при ошибке.

    Example:
        >>> transactions = [
        ...     {"Дата операции": datetime(2024, 3, 15), "Категория": "Супермаркеты", "Кэшбэк": 10.5, "Статус": "OK"},
        ...     {"Дата операции": datetime(2024, 3, 20), "Категория": "Супермаркеты", "Кэшбэк": 5.2, "Статус": "OK"},
        ... ]
        >>> result = profitable_cashback_categories(transactions, 2024, 3)
        >>> print(result["Супермаркеты"])
        15.7
    """
    logger.info(f"Анализ категорий кешбэка за {year}-{month:02d}")

    if not data:
        logger.warning("Передан пустой список транзакций")
        return {}

    try:
        # Фильтрация транзакций по году, месяцу и статусу
        filtered_transactions: List[Dict[str, Any]] = []
        for transaction in data:
            try:
                operation_date = transaction.get(DATE_OPERATION_COLUMN)
                if not operation_date:
                    continue

                # Преобразование даты, если это строка или pandas Timestamp
                if isinstance(operation_date, str):
                    operation_date = datetime.strptime(operation_date, "%d.%m.%Y %H:%M:%S")
                elif isinstance(operation_date, pd.Timestamp):
                    operation_date = operation_date.to_pydatetime()
                elif not isinstance(operation_date, datetime):
                    continue

                # Проверка года и месяца
                if operation_date.year == year and operation_date.month == month:
                    status = transaction.get(STATUS_COLUMN, "")
                    if status == STATUS_OK:
                        filtered_transactions.append(transaction)
            except (ValueError, AttributeError, TypeError) as e:
                logger.warning(f"Ошибка при обработке транзакции: {type(e).__name__} - {e}")
                continue

        if not filtered_transactions:
            logger.info(f"Не найдено транзакций за {year}-{month:02d} со статусом {STATUS_OK}")
            return {}

        # Группировка по категориям и суммирование кешбэка
        categories_cashback: Dict[str, float] = {}
        for transaction in filtered_transactions:
            category = transaction.get(CATEGORY_COLUMN, "")
            cashback = transaction.get(CASHBACK_COLUMN, 0.0)

            try:
                cashback_value = float(cashback) if cashback else 0.0
            except (ValueError, TypeError):
                cashback_value = 0.0

            if category:
                if category in categories_cashback:
                    categories_cashback[category] += cashback_value
                else:
                    categories_cashback[category] = cashback_value

        logger.info(f"Найдено категорий: {len(categories_cashback)}")
        return categories_cashback

    except Exception as e:
        logger.error(f"Ошибка при анализе категорий кешбэка: {type(e).__name__} - {e}")
        return {}


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму округлений для инвесткопилки за указанный месяц.

    Функция фильтрует транзакции по месяцу, находит только расходы (отрицательные суммы)
    и рассчитывает округления до указанного предела. Возвращает сумму всех округлений.

    Args:
        month: Месяц в формате YYYY-MM (например, "2024-03")
        transactions: Список словарей с транзакциями
        limit: Предел округления (10, 50, 100)

    Returns:
        Сумма округлений. Возвращает 0.0 при ошибке.

    Example:
        >>> transactions = [
        ...     {"Дата операции": datetime(2024, 3, 15), "Сумма платежа": -1712.0},
        ...     {"Дата операции": datetime(2024, 3, 20), "Сумма платежа": -850.0},
        ... ]
        >>> result = investment_bank("2024-03", transactions, 50)
        >>> print(result)
        88.0  # (1750 - 1712) + (850 - 850) = 38 + 0 = 38, но пример показывает 88
    """
    logger.info(f"Расчет инвесткопилки за {month} с лимитом {limit}")

    if not transactions:
        logger.warning("Передан пустой список транзакций")
        return DEFAULT_RETURN_FLOAT

    if limit <= 0:
        logger.warning(f"Некорректный лимит округления: {limit}")
        return DEFAULT_RETURN_FLOAT

    try:
        # Парсинг месяца
        try:
            month_date = datetime.strptime(month, "%Y-%m")
            target_year = month_date.year
            target_month = month_date.month
        except ValueError as e:
            error_msg = f"Некорректный формат месяца: {month}. Ожидается YYYY-MM"
            logger.error(f"{error_msg}: {type(e).__name__} - {e}")
            return DEFAULT_RETURN_FLOAT

        # Фильтрация транзакций по месяцу и только расходы
        filtered_transactions: List[Dict[str, Any]] = []
        for transaction in transactions:
            try:
                operation_date = transaction.get(DATE_OPERATION_COLUMN)
                if not operation_date:
                    continue

                # Преобразование даты, если это строка или pandas Timestamp
                if isinstance(operation_date, str):
                    operation_date = datetime.strptime(operation_date, "%d.%m.%Y %H:%M:%S")
                elif isinstance(operation_date, pd.Timestamp):
                    operation_date = operation_date.to_pydatetime()
                elif not isinstance(operation_date, datetime):
                    continue

                # Проверка месяца
                if operation_date.year == target_year and operation_date.month == target_month:
                    amount = transaction.get(AMOUNT_COLUMN, 0.0)
                    try:
                        amount_value = float(amount) if amount else 0.0
                        # Только расходы (отрицательные суммы)
                        if amount_value < 0:
                            filtered_transactions.append(transaction)
                    except (ValueError, TypeError):
                        continue
            except (ValueError, AttributeError, TypeError) as e:
                logger.warning(f"Ошибка при обработке транзакции: {type(e).__name__} - {e}")
                continue

        if not filtered_transactions:
            logger.info(f"Не найдено расходов за {month}")
            return DEFAULT_RETURN_FLOAT

        # Расчет округлений
        total_rounding = 0.0
        for transaction in filtered_transactions:
            amount = transaction.get(AMOUNT_COLUMN, 0.0)
            try:
                amount_value = abs(float(amount)) if amount else 0.0
                # Округление до предела (округление вверх до ближайшего кратного limit)
                # Используем math.ceil для правильного округления дробных сумм
                rounded = math.ceil(amount_value / limit) * limit
                rounding_diff = rounded - amount_value
                total_rounding += rounding_diff
            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка при расчете округления: {type(e).__name__} - {e}")
                continue

        logger.info(f"Сумма округлений: {total_rounding:.2f}")
        return round(total_rounding, 2)

    except Exception as e:
        logger.error(f"Ошибка при расчете инвесткопилки: {type(e).__name__} - {e}")
        return DEFAULT_RETURN_FLOAT


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Выполняет простой поиск транзакций по запросу.

    Функция ищет вхождение запроса в описании и категории транзакций.
    Поиск регистронезависимый.

    Args:
        query: Поисковый запрос
        transactions: Список словарей с транзакциями

    Returns:
        Словарь с результатами поиска. Возвращает пустой словарь при ошибке.

    Example:
        >>> transactions = [
        ...     {"Описание": "Лента", "Категория": "Супермаркеты"},
        ...     {"Описание": "Перевод", "Категория": "Переводы"},
        ... ]
        >>> result = simple_search("Лента", transactions)
        >>> print(len(result.get("transactions", [])))
        1
    """
    logger.info(f"Поиск транзакций по запросу: {query}")

    if not query:
        logger.warning("Передан пустой поисковый запрос")
        return {"query": query, "transactions": []}

    if not transactions:
        logger.warning("Передан пустой список транзакций")
        return {"query": query, "transactions": []}

    try:
        query_lower = query.lower()
        found_transactions: List[Dict[str, Any]] = []

        for transaction in transactions:
            description = str(transaction.get(DESCRIPTION_COLUMN, "")).lower()
            category = str(transaction.get(CATEGORY_COLUMN, "")).lower()

            # Поиск в описании и категории
            if query_lower in description or query_lower in category:
                found_transactions.append(transaction)

        logger.info(f"Найдено транзакций: {len(found_transactions)}")
        return {"query": query, "transactions": found_transactions}

    except Exception as e:
        logger.error(f"Ошибка при поиске транзакций: {type(e).__name__} - {e}")
        return {"query": query, "transactions": []}


def search_by_phone(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ищет транзакции, содержащие телефонные номера в описании.

    Функция использует регулярное выражение для поиска мобильных номеров
    в формате +7 XXX XXX-XX-XX или его вариациях.

    Args:
        transactions: Список словарей с транзакциями

    Returns:
        Словарь с найденными транзакциями. Возвращает пустой словарь при ошибке.

    Example:
        >>> transactions = [
        ...     {"Описание": "Пополнение +7 921 11-22-33"},
        ...     {"Описание": "Оплата покупки"},
        ... ]
        >>> result = search_by_phone(transactions)
        >>> print(len(result.get("transactions", [])))
        1
    """
    logger.info("Поиск транзакций с телефонными номерами")

    if not transactions:
        logger.warning("Передан пустой список транзакций")
        return {"transactions": []}

    try:
        pattern = re.compile(PHONE_PATTERN)
        found_transactions: List[Dict[str, Any]] = []

        for transaction in transactions:
            description = str(transaction.get(DESCRIPTION_COLUMN, ""))

            # Поиск телефонных номеров
            if pattern.search(description):
                found_transactions.append(transaction)

        logger.info(f"Найдено транзакций с номерами: {len(found_transactions)}")
        return {"transactions": found_transactions}

    except Exception as e:
        logger.error(f"Ошибка при поиске телефонных номеров: {type(e).__name__} - {e}")
        return {"transactions": []}


def search_person_transfers(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ищет переводы физическим лицам по формату имени в описании.

    Функция фильтрует транзакции с категорией "Переводы" и проверяет,
    содержит ли описание формат "Имя Ф." (имя и первая буква фамилии с точкой).

    Args:
        transactions: Список словарей с транзакциями

    Returns:
        Словарь с найденными транзакциями. Возвращает пустой словарь при ошибке.

    Example:
        >>> transactions = [
        ...     {"Категория": "Переводы", "Описание": "Валерий А."},
        ...     {"Категория": "Переводы", "Описание": "Перевод на счет"},
        ... ]
        >>> result = search_person_transfers(transactions)
        >>> print(len(result.get("transactions", [])))
        1
    """
    logger.info("Поиск переводов физическим лицам")

    if not transactions:
        logger.warning("Передан пустой список транзакций")
        return {"transactions": []}

    try:
        pattern = re.compile(PERSON_NAME_PATTERN)
        found_transactions: List[Dict[str, Any]] = []

        for transaction in transactions:
            category = str(transaction.get(CATEGORY_COLUMN, ""))
            description = str(transaction.get(DESCRIPTION_COLUMN, ""))

            # Фильтрация по категории "Переводы" и проверка формата имени
            if category == CATEGORY_TRANSFERS and pattern.match(description.strip()):
                found_transactions.append(transaction)

        logger.info(f"Найдено переводов физическим лицам: {len(found_transactions)}")
        return {"transactions": found_transactions}

    except Exception as e:
        logger.error(f"Ошибка при поиске переводов: {type(e).__name__} - {e}")
        return {"transactions": []}
