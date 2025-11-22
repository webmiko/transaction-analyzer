"""Модуль для генерации JSON-данных для веб-страниц.

Этот модуль содержит функции для генерации JSON-ответов
для главной страницы и страницы событий.
"""

import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd  # type: ignore[import-untyped]
from dotenv import load_dotenv

from src.logger_config import setup_logger

# Загрузка переменных окружения из .env файла
load_dotenv()
from src.utils import (
    format_date,
    get_currency_rates,
    get_month_start,
    get_stock_prices,
    load_transactions_from_excel,
    load_user_settings,
)

# Настройка логгера
logger = setup_logger(__name__)

# Константы
DEFAULT_EXCEL_FILE = os.getenv("EXCEL_FILE", "data/operations.xlsx")
CASHBACK_RATE = 0.01  # 1 рубль кешбэка на каждые 100 рублей
TOP_TRANSACTIONS_COUNT = 5
TOP_CATEGORIES_COUNT = 7


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
            current_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            error_msg = f"Некорректный формат даты: {date_time}"
            logger.error(f"{error_msg}. Ожидается формат: YYYY-MM-DD HH:MM:SS")
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
                "cards": [],
                "top_transactions": [],
                "currency_rates": [],
                "stock_prices": [],
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
                card_str = str(card)
                last_digits = card_str.replace("*", "") if "*" in card_str else card_str[-4:]

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
        user_currencies = settings.get("user_currencies", [])
        user_stocks = settings.get("user_stocks", [])

        currency_rates = get_currency_rates(user_currencies) if user_currencies else []
        stock_prices = get_stock_prices(user_stocks) if user_stocks else []

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
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        # Возвращаем базовую структуру при ошибке
        try:
            current_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
            greeting = _get_greeting(current_datetime.hour)
        except Exception:
            greeting = "Добрый день"

        return {
            "greeting": greeting,
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": [],
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
            current_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError as e:
            error_msg = f"Некорректный формат даты: {date}"
            logger.error(f"{error_msg}. Ожидается формат: YYYY-MM-DD")
            raise ValueError(error_msg) from e

        # Определение диапазона данных по периоду
        if period == "W":
            # Неделя: последние 7 дней
            from datetime import timedelta

            date_range_start = current_date - timedelta(days=7)
            date_range_end = current_date
        elif period == "M":
            # Месяц: с начала месяца по указанную дату
            date_range_start = get_month_start(current_date)
            date_range_end = current_date
        elif period == "Y":
            # Год: с начала года по указанную дату
            date_range_start = datetime(current_date.year, 1, 1)
            date_range_end = current_date
        elif period == "ALL":
            # Все данные до указанной даты
            date_range_start = datetime(2000, 1, 1)  # Начальная дата
            date_range_end = current_date
        else:
            error_msg = f"Некорректный период: {period}. Допустимые значения: W, M, Y, ALL"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"Диапазон данных: {format_date(date_range_start)} - {format_date(date_range_end)}")

        # Загрузка транзакций
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)
        if df.empty:
            logger.warning("Загружен пустой DataFrame")
            return {
                "expenses": {"total_amount": 0, "main": [], "transfers_and_cash": []},
                "income": {"total_amount": 0, "main": []},
                "currency_rates": [],
                "stock_prices": [],
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

        for idx, (category, amount) in enumerate(expenses_by_category.items()):
            if idx < TOP_CATEGORIES_COUNT:
                main_categories.append({"category": category, "amount": int(amount)})
            else:
                other_amount += amount

        if other_amount > 0:
            main_categories.append({"category": "Остальное", "amount": int(other_amount)})

        # Переводы и наличные отдельно
        transfers_and_cash: List[Dict[str, Any]] = []
        for category in ["Переводы", "Наличные"]:
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
        user_currencies = settings.get("user_currencies", [])
        user_stocks = settings.get("user_stocks", [])

        currency_rates = get_currency_rates(user_currencies) if user_currencies else []
        stock_prices = get_stock_prices(user_stocks) if user_stocks else []

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
        logger.error(f"{error_msg}: {type(e).__name__}", exc_info=True)
        # Возвращаем базовую структуру при ошибке
        return {
            "expenses": {"total_amount": 0, "main": [], "transfers_and_cash": []},
            "income": {"total_amount": 0, "main": []},
            "currency_rates": [],
            "stock_prices": [],
        }
