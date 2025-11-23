"""Модуль для генерации JSON-данных для веб-страниц.

Этот модуль содержит функции для генерации JSON-ответов
для главной страницы и страницы событий.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd  # type: ignore[import-untyped]
from dotenv import load_dotenv

from src.utils import (
    format_date,
    get_currency_rates,
    get_month_start,
    get_stock_prices,
    load_transactions_from_excel,
    load_user_settings,
)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Константы модуля
ENCODING = "utf-8"
FILE_WRITE_MODE = "w"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
DEFAULT_EXCEL_FILE = os.getenv("EXCEL_FILE", "data/operations.xlsx")
CASHBACK_RATE = 0.01  # 1 рубль кешбэка на каждые 100 рублей
TOP_TRANSACTIONS_COUNT = 5
TOP_CATEGORIES_COUNT = 7
DEFAULT_STATUS = "OK"
DEFAULT_GREETING = "Добрый день"
WEEK_DAYS = 7
EARLIEST_YEAR = 2000
EARLIEST_MONTH = 1
EARLIEST_DAY = 1
PERIOD_WEEK = "W"
PERIOD_MONTH = "M"
PERIOD_YEAR = "Y"
PERIOD_ALL = "ALL"
CATEGORY_OTHER = "Остальное"
CATEGORY_TRANSFERS = "Переводы"
CATEGORY_CASH = "Наличные"
DEFAULT_RETURN_VALUE: List[Dict[str, Any]] = []
DEFAULT_RETURN_DICT: Dict[str, Any] = {}


def _setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля views.

    Returns:
        Настроенный логгер для модуля views
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "views.log"
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


def _get_greeting(hour: int) -> str:
    """
    Определяет приветствие в зависимости от времени суток.

    Args:
        hour: Час дня (0-23)

    Returns:
        Строка с приветствием
    """
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def home_page(date_time: str) -> Dict[str, Any]:
    """
    Генерирует JSON-данные для главной страницы.

    Функция принимает дату и время, загружает транзакции с начала месяца
    по указанную дату, обрабатывает данные и возвращает JSON с:
    - Приветствием по времени суток
    - Данными по картам (последние 4 цифры, сумма расходов, кешбэк)
    - Топ-5 транзакций по сумме платежа
    - Курсами валют
    - Ценами акций

    Args:
        date_time: Дата и время в формате YYYY-MM-DD HH:MM:SS

    Returns:
        Словарь с данными для главной страницы

    Example:
        >>> result = home_page("2024-03-15 14:30:00")
        >>> print(result["greeting"])
        "Добрый день"
    """
    logger.info(f"Генерация данных для главной страницы: {date_time}")

    try:
        # Парсинг даты и времени
        try:
            current_datetime = datetime.strptime(date_time, DATE_TIME_FORMAT)
        except ValueError as e:
            error_msg = f"Некорректный формат даты: {date_time}"
            logger.error(f"{error_msg}. Ожидается формат: {DATE_TIME_FORMAT}")
            raise ValueError(error_msg) from e

        # Определение диапазона данных (с начала месяца по указанную дату)
        month_start = get_month_start(current_datetime)
        date_range_start = month_start
        date_range_end = current_datetime

        logger.debug(f"Диапазон данных: {format_date(date_range_start)} - {format_date(date_range_end)}")

        # Загрузка транзакций
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)
        if df.empty:
            logger.warning("Загружен пустой DataFrame")
            return {
                "greeting": _get_greeting(current_datetime.hour),
                "cards": DEFAULT_RETURN_VALUE,
                "top_transactions": DEFAULT_RETURN_VALUE,
                "currency_rates": DEFAULT_RETURN_VALUE,
                "stock_prices": DEFAULT_RETURN_VALUE,
            }

        # Фильтрация по диапазону дат и статусу
        df_filtered = df[
            (df["Дата операции"] >= date_range_start)
            & (df["Дата операции"] <= date_range_end)
            & (df["Статус"] == "OK")
        ].copy()

        logger.info(f"Отфильтровано транзакций: {len(df_filtered)}")

        # Обработка данных по картам
        cards_data: List[Dict[str, Any]] = []
        if not df_filtered.empty:
            # Группировка по картам
            cards_grouped = df_filtered.groupby("Номер карты")

            for card, group in cards_grouped:
                # Только расходы (отрицательные суммы)
                expenses = group[group["Сумма платежа"] < 0]
                total_spent = abs(expenses["Сумма платежа"].sum())
                cashback = total_spent * CASHBACK_RATE

                # Извлекаем последние 4 цифры карты
                # Удаляем звездочки и берем последние 4 символа
                card_str = str(card)
                card_str_clean = card_str.replace("*", "")
                last_digits = card_str_clean[-4:]

                cards_data.append(
                    {
                        "last_digits": last_digits,
                        "total_spent": round(total_spent, 2),
                        "cashback": round(cashback, 2),
                    }
                )

            # Сортировка по сумме расходов (по убыванию)
            cards_data.sort(key=lambda x: x["total_spent"], reverse=True)

        # Топ-5 транзакций по сумме платежа
        top_transactions: List[Dict[str, Any]] = []
        if not df_filtered.empty:
            # Сортировка по сумме платежа (по убыванию, берем абсолютное значение)
            df_sorted = df_filtered.copy()
            df_sorted["abs_amount"] = df_sorted["Сумма платежа"].abs()
            df_sorted = df_sorted.sort_values("abs_amount", ascending=False)

            for _, row in df_sorted.head(TOP_TRANSACTIONS_COUNT).iterrows():
                # Извлекаем значения из Series
                operation_date_value = row["Дата операции"]
                # Преобразуем в datetime, если это не datetime
                if isinstance(operation_date_value, datetime):
                    operation_date = operation_date_value
                elif hasattr(operation_date_value, "to_pydatetime"):
                    operation_date = operation_date_value.to_pydatetime()
                else:
                    # Пытаемся преобразовать строку или другой формат
                    operation_date = pd.to_datetime(operation_date_value).to_pydatetime()

                top_transactions.append(
                    {
                        "date": format_date(operation_date),
                        "amount": round(float(row["Сумма платежа"]), 2),
                        "category": str(row["Категория"]),
                        "description": str(row["Описание"]),
                    }
                )

        # Получение внешних данных
        settings = load_user_settings()
        user_currencies = settings.get("user_currencies", DEFAULT_RETURN_VALUE)
        user_stocks = settings.get("user_stocks", DEFAULT_RETURN_VALUE)

        currency_rates = get_currency_rates(user_currencies) if user_currencies else DEFAULT_RETURN_VALUE
        stock_prices = get_stock_prices(user_stocks) if user_stocks else DEFAULT_RETURN_VALUE

        # Формирование ответа
        result = {
            "greeting": _get_greeting(current_datetime.hour),
            "cards": cards_data,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        logger.info("Данные для главной страницы успешно сгенерированы")
        return result

    except Exception as e:
        error_msg = "Ошибка при генерации данных для главной страницы"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        # Возвращаем базовую структуру при ошибке
        try:
            current_datetime = datetime.strptime(date_time, DATE_TIME_FORMAT)
            greeting = _get_greeting(current_datetime.hour)
        except Exception:
            greeting = DEFAULT_GREETING

        return {
            "greeting": greeting,
            "cards": DEFAULT_RETURN_VALUE,
            "top_transactions": DEFAULT_RETURN_VALUE,
            "currency_rates": DEFAULT_RETURN_VALUE,
            "stock_prices": DEFAULT_RETURN_VALUE,
        }


def events_page(date: str, period: str = "M") -> Dict[str, Any]:
    """
    Генерирует JSON-данные для страницы событий.

    Функция принимает дату и период, загружает транзакции за указанный период,
    обрабатывает расходы и поступления, и возвращает JSON с:
    - Расходами (общая сумма, основные категории, переводы и наличные)
    - Поступлениями (общая сумма, категории)
    - Курсами валют и ценами акций

    Args:
        date: Дата в формате YYYY-MM-DD
        period: Период данных (W - неделя, M - месяц, Y - год, ALL - все данные)

    Returns:
        Словарь с данными для страницы событий

    Example:
        >>> result = events_page("2024-03-15", "M")
        >>> print(result["expenses"]["total_amount"])
        32101
    """
    logger.info(f"Генерация данных для страницы событий: date={date}, period={period}")

    try:
        # Парсинг даты
        try:
            current_date = datetime.strptime(date, DATE_FORMAT)
        except ValueError as e:
            error_msg = f"Некорректный формат даты: {date}"
            logger.error(f"{error_msg}. Ожидается формат: {DATE_FORMAT}")
            raise ValueError(error_msg) from e

        # Определение диапазона данных по периоду
        # Устанавливаем date_range_end на конец дня (23:59:59), чтобы включить все транзакции в этот день
        date_range_end = current_date.replace(hour=23, minute=59, second=59)

        if period == PERIOD_WEEK:
            # Неделя: последние 7 дней
            date_range_start = current_date - timedelta(days=WEEK_DAYS)
        elif period == PERIOD_MONTH:
            # Месяц: с начала месяца по указанную дату
            date_range_start = get_month_start(current_date)
        elif period == PERIOD_YEAR:
            # Год: с начала года по указанную дату
            date_range_start = datetime(current_date.year, 1, 1)
        elif period == PERIOD_ALL:
            # Все данные до указанной даты
            date_range_start = datetime(EARLIEST_YEAR, EARLIEST_MONTH, EARLIEST_DAY)
        else:
            error_msg = (
                f"Некорректный период: {period}. "
                f"Допустимые значения: {PERIOD_WEEK}, {PERIOD_MONTH}, "
                f"{PERIOD_YEAR}, {PERIOD_ALL}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"Диапазон данных: {format_date(date_range_start)} - {format_date(date_range_end)}")

        # Загрузка транзакций
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)
        if df.empty:
            logger.warning("Загружен пустой DataFrame")
            return {
                "expenses": {
                    "total_amount": 0,
                    "main": DEFAULT_RETURN_VALUE,
                    "transfers_and_cash": DEFAULT_RETURN_VALUE,
                },
                "income": {"total_amount": 0, "main": DEFAULT_RETURN_VALUE},
                "currency_rates": DEFAULT_RETURN_VALUE,
                "stock_prices": DEFAULT_RETURN_VALUE,
            }

        # Фильтрация по диапазону дат и статусу
        df_filtered = df[
            (df["Дата операции"] >= date_range_start)
            & (df["Дата операции"] <= date_range_end)
            & (df["Статус"] == "OK")
        ].copy()

        logger.info(f"Отфильтровано транзакций: {len(df_filtered)}")

        # Разделение на расходы и поступления
        expenses_df = df_filtered[df_filtered["Сумма платежа"] < 0].copy()
        income_df = df_filtered[df_filtered["Сумма платежа"] > 0].copy()

        # Обработка расходов
        expenses_total = int(abs(expenses_df["Сумма платежа"].sum()))

        # Топ-7 категорий по расходам
        expenses_by_category = (
            expenses_df.groupby("Категория")["Сумма платежа"].sum().abs().sort_values(ascending=False)
        )

        main_categories: List[Dict[str, Any]] = []
        other_amount = 0.0

        # Исключаем "Переводы" и "Наличные" из основных категорий
        # так как они обрабатываются отдельно
        excluded_categories = {CATEGORY_TRANSFERS, CATEGORY_CASH}
        main_category_count = 0

        for category, amount in expenses_by_category.items():
            if category in excluded_categories:
                # Пропускаем "Переводы" и "Наличные" - они будут в transfers_and_cash
                continue
            if main_category_count < TOP_CATEGORIES_COUNT:
                main_categories.append({"category": category, "amount": int(amount)})
                main_category_count += 1
            else:
                other_amount += amount

        if other_amount > 0:
            main_categories.append({"category": CATEGORY_OTHER, "amount": int(other_amount)})

        # Переводы и наличные отдельно
        transfers_and_cash: List[Dict[str, Any]] = []
        for category in [CATEGORY_TRANSFERS, CATEGORY_CASH]:
            if category in expenses_by_category.index:
                amount = int(abs(expenses_by_category[category]))
                transfers_and_cash.append({"category": category, "amount": amount})

        # Обработка поступлений
        income_total = int(income_df["Сумма платежа"].sum())

        income_by_category = income_df.groupby("Категория")["Сумма платежа"].sum().sort_values(ascending=False)

        income_main: List[Dict[str, Any]] = []
        for category, amount in income_by_category.items():
            income_main.append({"category": category, "amount": int(amount)})

        # Получение внешних данных
        settings = load_user_settings()
        user_currencies = settings.get("user_currencies", DEFAULT_RETURN_VALUE)
        user_stocks = settings.get("user_stocks", DEFAULT_RETURN_VALUE)

        currency_rates = get_currency_rates(user_currencies) if user_currencies else DEFAULT_RETURN_VALUE
        stock_prices = get_stock_prices(user_stocks) if user_stocks else DEFAULT_RETURN_VALUE

        # Формирование ответа
        result = {
            "expenses": {
                "total_amount": expenses_total,
                "main": main_categories,
                "transfers_and_cash": transfers_and_cash,
            },
            "income": {
                "total_amount": income_total,
                "main": income_main,
            },
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        logger.info("Данные для страницы событий успешно сгенерированы")
        return result

    except Exception as e:
        error_msg = "Ошибка при генерации данных для страницы событий"
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        # Возвращаем базовую структуру при ошибке
        return {
            "expenses": {"total_amount": 0, "main": DEFAULT_RETURN_VALUE, "transfers_and_cash": DEFAULT_RETURN_VALUE},
            "income": {"total_amount": 0, "main": DEFAULT_RETURN_VALUE},
            "currency_rates": DEFAULT_RETURN_VALUE,
            "stock_prices": DEFAULT_RETURN_VALUE,
        }
