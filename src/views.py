"""Модуль для генерации JSON-данных для веб-страниц.

Этот модуль содержит функции для генерации JSON-ответов
для главной страницы и страницы событий.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd  # type: ignore[import-untyped]

# Типы для pandas
try:
    from pandas import Timestamp  # type: ignore[import-untyped]
except ImportError:
    Timestamp = Any  # type: ignore[misc,assignment]
from dotenv import load_dotenv

from src.utils import (
    format_date,
    get_currency_rates,
    get_month_start,
    get_stock_prices,
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
PERIOD_CUSTOM = "CUSTOM"
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


def home_page(date_time: str, transactions: pd.DataFrame) -> Dict[str, Any]:
    """
    Генерирует JSON-данные для главной страницы.

    Функция принимает дату и время, обрабатывает транзакции с начала месяца
    по указанную дату и возвращает JSON с:
    - Приветствием по времени суток
    - Данными по картам (последние 4 цифры, сумма расходов, кешбэк)
    - Топ-5 транзакций по сумме платежа
    - Курсами валют
    - Ценами акций

    Args:
        date_time: Дата и время в формате YYYY-MM-DD HH:MM:SS
        transactions: DataFrame с транзакциями

    Returns:
        Словарь с данными для главной страницы

    Example:
        >>> df = load_transactions_from_excel("data/operations.xlsx")
        >>> result = home_page("2024-03-15 14:30:00", df)
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
        # Устанавливаем date_range_end на конец дня (23:59:59), чтобы включить все транзакции в этот день
        date_range_end = current_datetime.replace(hour=23, minute=59, second=59)

        logger.debug(f"Диапазон данных: {format_date(date_range_start)} - {format_date(date_range_end)}")

        # Проверка данных
        if transactions.empty:
            logger.warning("Загружен пустой DataFrame")
            return {
                "greeting": _get_greeting(current_datetime.hour),
                "cards": [],
                "top_transactions": [],
                "currency_rates": [],
                "stock_prices": [],
            }

        # Фильтрация по диапазону дат и статусу
        df_filtered = transactions[
            (transactions["Дата операции"] >= date_range_start)
            & (transactions["Дата операции"] <= date_range_end)
            & (transactions["Статус"] == "OK")
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
                # Получаем дату операции из строки DataFrame
                operation_date_value: Any = row["Дата операции"]
                # Преобразуем в datetime, если это не datetime
                if isinstance(operation_date_value, datetime):
                    operation_date = operation_date_value
                elif isinstance(operation_date_value, pd.Timestamp):
                    # Для pandas Timestamp используем to_pydatetime()
                    operation_date = operation_date_value.to_pydatetime()
                else:
                    # Пытаемся преобразовать строку или другой формат
                    operation_date_dt = pd.to_datetime(operation_date_value)
                    if isinstance(operation_date_dt, pd.Timestamp):
                        operation_date = operation_date_dt.to_pydatetime()
                    else:
                        operation_date = datetime.now()

                # Получаем сумму платежа из строки DataFrame
                amount_value: Any = row["Сумма платежа"]
                # Если это массив (Series), берем первое значение, иначе используем как есть
                if isinstance(amount_value, pd.Series):
                    amount = float(amount_value.iloc[0])
                else:
                    amount = float(amount_value)

                top_transactions.append(
                    {
                        "date": format_date(operation_date),
                        "amount": round(amount, 2),
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
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        # Возвращаем базовую структуру при ошибке
        try:
            current_datetime = datetime.strptime(date_time, DATE_TIME_FORMAT)
            greeting = _get_greeting(current_datetime.hour)
        except Exception:
            greeting = DEFAULT_GREETING

        return {
            "greeting": greeting,
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": [],
        }


def events_page(
    date: str,
    period: str,
    transactions: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    card_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Генерирует JSON-данные для страницы событий.

    Функция принимает дату и период, обрабатывает транзакции за указанный период
    и возвращает JSON с:
    - Расходами (общая сумма, основные категории, переводы и наличные)
    - Поступлениями (общая сумма, категории)
    - Курсами валют и ценами акций

    Args:
        date: Дата в формате YYYY-MM-DD (используется для стандартных периодов)
        period: Период данных (W - неделя, M - месяц, Y - год, ALL - все данные, CUSTOM - кастомный диапазон)
        transactions: DataFrame с транзакциями
        start_date: Начальная дата в формате YYYY-MM-DD (для периода CUSTOM)
        end_date: Конечная дата в формате YYYY-MM-DD (для периода CUSTOM)
        card_filter: Последние 4 цифры карты для фильтрации (например, "7197")

    Returns:
        Словарь с данными для страницы событий

    Example:
        >>> result = events_page("2024-03-15", "M", df)
        >>> print(result["expenses"]["total_amount"])
        32101
    """
    logger.info(f"Генерация данных для страницы событий: date={date}, period={period}")

    try:
        # Если период CUSTOM, используем переданные даты
        if period == PERIOD_CUSTOM:
            if not start_date or not end_date:
                error_msg = "Для периода CUSTOM необходимо указать start_date и end_date"
                logger.error(error_msg)
                raise ValueError(error_msg)

            try:
                date_range_start = datetime.strptime(start_date, DATE_FORMAT)
                date_range_end = datetime.strptime(end_date, DATE_FORMAT).replace(hour=23, minute=59, second=59)
            except ValueError as e:
                error_msg = f"Некорректный формат даты: {start_date} или {end_date}. Ожидается формат: {DATE_FORMAT}"
                logger.error(error_msg)
                raise ValueError(error_msg) from e
        else:
            # Парсинг даты для стандартных периодов
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
                # Неделя: последние 7 дней (включая текущий день)
                # Вычитаем 6 дней, чтобы получить диапазон из 7 дней: [current_date-6, current_date]
                date_range_start = current_date - timedelta(days=WEEK_DAYS - 1)
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
                    f"{PERIOD_YEAR}, {PERIOD_ALL}, {PERIOD_CUSTOM}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        logger.debug(f"Диапазон данных: {format_date(date_range_start)} - {format_date(date_range_end)}")

        # Проверка данных
        if transactions.empty:
            logger.warning("Загружен пустой DataFrame")
            return {
                "expenses": {
                    "total_amount": 0,
                    "main": [],
                    "transfers_and_cash": [],
                },
                "income": {"total_amount": 0, "main": []},
                "currency_rates": [],
                "stock_prices": [],
            }

        # Фильтрация по диапазону дат и статусу
        df_filtered = transactions[
            (transactions["Дата операции"] >= date_range_start)
            & (transactions["Дата операции"] <= date_range_end)
            & (transactions["Статус"] == "OK")
        ].copy()

        # Фильтрация по карте, если указан фильтр
        if card_filter:
            # Извлекаем последние 4 цифры из номера карты и сравниваем с фильтром
            def matches_card(card_str: str) -> bool:
                """Проверяет, совпадают ли последние 4 цифры карты с фильтром."""
                card_clean = str(card_str).replace("*", "")
                last_digits = card_clean[-4:] if len(card_clean) >= 4 else card_clean
                return last_digits == card_filter

            # Применяем фильтр по карте
            df_filtered = df_filtered[df_filtered["Номер карты"].apply(matches_card)].copy()
            logger.info(f"Применен фильтр по карте ****{card_filter}")

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
                # Получаем сумму для категории
                amount_value: Any = expenses_by_category[category]
                # Если это массив (Series), берем первое значение, иначе используем как есть
                if isinstance(amount_value, pd.Series):
                    amount_scalar = float(amount_value.iloc[0])
                else:
                    amount_scalar = float(amount_value)
                amount = int(abs(amount_scalar))
                transfers_and_cash.append({"category": category, "amount": amount})

        # Обработка поступлений
        income_total = int(income_df["Сумма платежа"].sum())

        income_by_category = income_df.groupby("Категория")["Сумма платежа"].sum().sort_values(ascending=False)

        income_main: List[Dict[str, Any]] = []
        for category, amount in income_by_category.items():
            # Если amount - это Series (массив), берем первое значение, иначе используем как есть
            if isinstance(amount, pd.Series):
                amount_value = float(amount.iloc[0])
            else:
                amount_value = float(amount)
            income_main.append({"category": category, "amount": int(amount_value)})

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
        logger.error(f"{error_msg}: {type(e).__name__} - {e}")
        # Возвращаем базовую структуру при ошибке
        return {
            "expenses": {"total_amount": 0, "main": [], "transfers_and_cash": []},
            "income": {"total_amount": 0, "main": []},
            "currency_rates": [],
            "stock_prices": [],
        }
