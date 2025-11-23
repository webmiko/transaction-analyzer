"""Модуль для генерации отчетов по транзакциям.

Этот модуль содержит функции для анализа трат по различным критериям
и декоратор для автоматического сохранения отчетов в файлы.
"""

import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd  # type: ignore[import-untyped]

from src.utils import get_three_months_back

# Константы модуля
ENCODING = "utf-8"
FILE_WRITE_MODE = "w"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
DATE_OPERATION_COLUMN = "Дата операции"
CATEGORY_COLUMN = "Категория"
AMOUNT_COLUMN = "Сумма платежа"
REPORTS_DIR = "reports"
REPORT_PREFIX = "report_"
REPORT_EXTENSION = ".json"
WEEKDAY_COLUMN = "день_недели"
AVERAGE_AMOUNT_COLUMN = "средняя_сумма"
DAY_TYPE_COLUMN = "тип_дня"
WORKDAY = "рабочий"
WEEKEND = "выходной"
WORKDAY_START = 0
WORKDAY_END = 4
WEEKEND_START = 5
WEEKEND_END = 6


def _setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля reports.

    Returns:
        Настроенный логгер для модуля reports
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "reports.log"
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


def save_report(filename: Optional[str] = None) -> Callable[..., Any]:
    """
    Декоратор для сохранения результатов отчетов в JSON-файл.

    Декоратор может использоваться с параметром (имя файла) или без параметра
    (автоматическая генерация имени файла).

    Args:
        filename: Имя файла для сохранения. Если None, генерируется автоматически
                 в формате: report_{function_name}_{timestamp}.json

    Returns:
        Декорированная функция

    Example:
        >>> @save_report()
        ... def my_report():
        ...     return {"data": "test"}
        ...
        >>> @save_report("custom_report.json")
        ... def my_custom_report():
        ...     return {"data": "test"}
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Выполнение функции
            result = func(*args, **kwargs)

            # Определение пути к файлу
            if filename:
                file_path = Path(filename)
                # Создаем родительские директории, если они не существуют
                file_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Генерация имени файла
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{REPORT_PREFIX}{func.__name__}_{timestamp}{REPORT_EXTENSION}"
                reports_dir = Path(__file__).parent.parent / REPORTS_DIR
                reports_dir.mkdir(exist_ok=True)
                file_path = reports_dir / file_name

            # Сохранение в JSON
            try:
                with open(file_path, FILE_WRITE_MODE, encoding=ENCODING) as f:
                    # Преобразование DataFrame в словарь, если необходимо
                    if isinstance(result, pd.DataFrame):
                        result_dict = result.to_dict(orient="records")
                        json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)
                    else:
                        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

                logger.info(f"Отчет сохранен в файл: {file_path}")
            except (OSError, PermissionError, TypeError) as e:
                logger.error(f"Ошибка при сохранении отчета: {type(e).__name__} - {e}")

            return result

        return wrapper

    # Поддержка вызова с параметром и без
    if callable(filename):
        func = filename
        filename = None
        return decorator(func)
    return decorator


@save_report()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Анализирует траты по указанной категории за последние 3 месяца.

    Функция фильтрует транзакции по категории и датам, группирует их
    и возвращает DataFrame с тратами по категории за последние 3 месяца.

    Args:
        transactions: DataFrame с транзакциями
        category: Категория для анализа
        date: Дата в формате YYYY-MM-DD. Если None, используется текущая дата

    Returns:
        DataFrame с тратами по категории. Возвращает пустой DataFrame при ошибке.

    Example:
        >>> df = pd.DataFrame({
        ...     "Дата операции": [datetime(2024, 3, 15)],
        ...     "Категория": ["Супермаркеты"],
        ...     "Сумма платежа": [-1000.0],
        ... })
        >>> result = spending_by_category(df, "Супермаркеты", "2024-03-15")
    """
    logger.info(f"Анализ трат по категории '{category}' за последние 3 месяца")

    if transactions.empty:
        logger.warning("Передан пустой DataFrame")
        return pd.DataFrame()

    try:
        # Определение даты
        if date:
            try:
                current_date = datetime.strptime(date, DATE_FORMAT)
            except ValueError as e:
                error_msg = f"Некорректный формат даты: {date}. Ожидается {DATE_FORMAT}"
                logger.error(f"{error_msg}: {type(e).__name__} - {e}")
                return pd.DataFrame()
        else:
            current_date = datetime.now()

        # Вычисление диапазона (последние 3 месяца)
        period_start, period_end = get_three_months_back(current_date)

        # Фильтрация данных
        df_filtered = transactions.copy()

        # Преобразование даты операции в datetime, если необходимо
        if DATE_OPERATION_COLUMN in df_filtered.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_filtered[DATE_OPERATION_COLUMN]):
                df_filtered[DATE_OPERATION_COLUMN] = pd.to_datetime(
                    df_filtered[DATE_OPERATION_COLUMN], format="%d.%m.%Y %H:%M:%S", errors="coerce"
                )

        # Фильтрация по категории
        df_filtered = df_filtered[df_filtered[CATEGORY_COLUMN] == category]

        # Фильтрация по диапазону дат
        df_filtered = df_filtered[
            (df_filtered[DATE_OPERATION_COLUMN] >= period_start) & (df_filtered[DATE_OPERATION_COLUMN] <= period_end)
        ]

        # Только расходы (отрицательные суммы)
        df_filtered = df_filtered[df_filtered[AMOUNT_COLUMN] < 0]

        if df_filtered.empty:
            logger.info(f"Не найдено трат по категории '{category}' за последние 3 месяца")
            return pd.DataFrame()

        # Группировка по месяцам и суммирование
        df_filtered["месяц"] = df_filtered[DATE_OPERATION_COLUMN].dt.to_period("M")
        result_df = df_filtered.groupby("месяц")[AMOUNT_COLUMN].sum().abs().reset_index()
        result_df.columns = pd.Index(["месяц", "сумма_трат"], dtype=object)
        result_df["месяц"] = result_df["месяц"].astype(str)

        logger.info(f"Найдено трат по категории '{category}': {len(result_df)} месяцев")
        return result_df

    except Exception as e:
        logger.error(f"Ошибка при анализе трат по категории: {type(e).__name__} - {e}")
        return pd.DataFrame()


@save_report()
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """
    Анализирует средние траты по дням недели за последние 3 месяца.

    Функция фильтрует транзакции по датам, определяет день недели для каждой транзакции
    и возвращает DataFrame со средними тратами по каждому дню недели.

    Args:
        transactions: DataFrame с транзакциями
        date: Дата в формате YYYY-MM-DD. Если None, используется текущая дата

    Returns:
        DataFrame со средними тратами по дням недели. Возвращает пустой DataFrame при ошибке.

    Example:
        >>> df = pd.DataFrame({
        ...     "Дата операции": [datetime(2024, 3, 15)],
        ...     "Сумма платежа": [-1000.0],
        ... })
        >>> result = spending_by_weekday(df, "2024-03-15")
    """
    logger.info("Анализ средних трат по дням недели за последние 3 месяца")

    if transactions.empty:
        logger.warning("Передан пустой DataFrame")
        return pd.DataFrame()

    try:
        # Определение даты
        if date:
            try:
                current_date = datetime.strptime(date, DATE_FORMAT)
            except ValueError as e:
                error_msg = f"Некорректный формат даты: {date}. Ожидается {DATE_FORMAT}"
                logger.error(f"{error_msg}: {type(e).__name__} - {e}")
                return pd.DataFrame()
        else:
            current_date = datetime.now()

        # Вычисление диапазона (последние 3 месяца)
        period_start, period_end = get_three_months_back(current_date)

        # Фильтрация данных
        df_filtered = transactions.copy()

        # Преобразование даты операции в datetime
        if DATE_OPERATION_COLUMN in df_filtered.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_filtered[DATE_OPERATION_COLUMN]):
                df_filtered[DATE_OPERATION_COLUMN] = pd.to_datetime(
                    df_filtered[DATE_OPERATION_COLUMN], format="%d.%m.%Y %H:%M:%S", errors="coerce"
                )

        # Фильтрация по диапазону дат
        df_filtered = df_filtered[
            (df_filtered[DATE_OPERATION_COLUMN] >= period_start) & (df_filtered[DATE_OPERATION_COLUMN] <= period_end)
        ]

        # Только расходы (отрицательные суммы)
        df_filtered = df_filtered[df_filtered[AMOUNT_COLUMN] < 0]

        if df_filtered.empty:
            logger.info("Не найдено трат за последние 3 месяца")
            return pd.DataFrame()

        # Определение дня недели (понедельник = 0, воскресенье = 6)
        df_filtered[WEEKDAY_COLUMN] = df_filtered[DATE_OPERATION_COLUMN].dt.dayofweek

        # Группировка по дню недели и расчет среднего
        result_df = df_filtered.groupby(WEEKDAY_COLUMN)[AMOUNT_COLUMN].mean().abs().reset_index()
        result_df.columns = pd.Index([WEEKDAY_COLUMN, AVERAGE_AMOUNT_COLUMN], dtype=object)

        logger.info(f"Рассчитаны средние траты для {len(result_df)} дней недели")
        return result_df

    except Exception as e:
        logger.error(f"Ошибка при анализе трат по дням недели: {type(e).__name__} - {e}")
        return pd.DataFrame()


@save_report()
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """
    Анализирует средние траты в рабочие и выходные дни за последние 3 месяца.

    Функция фильтрует транзакции по датам, определяет тип дня (рабочий/выходной)
    и возвращает DataFrame со средними тратами по типам дней.

    Args:
        transactions: DataFrame с транзакциями
        date: Дата в формате YYYY-MM-DD. Если None, используется текущая дата

    Returns:
        DataFrame со средними тратами по типам дней. Возвращает пустой DataFrame при ошибке.

    Example:
        >>> df = pd.DataFrame({
        ...     "Дата операции": [datetime(2024, 3, 15)],
        ...     "Сумма платежа": [-1000.0],
        ... })
        >>> result = spending_by_workday(df, "2024-03-15")
    """
    logger.info("Анализ средних трат в рабочие и выходные дни за последние 3 месяца")

    if transactions.empty:
        logger.warning("Передан пустой DataFrame")
        return pd.DataFrame()

    try:
        # Определение даты
        if date:
            try:
                current_date = datetime.strptime(date, DATE_FORMAT)
            except ValueError as e:
                error_msg = f"Некорректный формат даты: {date}. Ожидается {DATE_FORMAT}"
                logger.error(f"{error_msg}: {type(e).__name__} - {e}")
                return pd.DataFrame()
        else:
            current_date = datetime.now()

        # Вычисление диапазона (последние 3 месяца)
        period_start, period_end = get_three_months_back(current_date)

        # Фильтрация данных
        df_filtered = transactions.copy()

        # Преобразование даты операции в datetime
        if DATE_OPERATION_COLUMN in df_filtered.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_filtered[DATE_OPERATION_COLUMN]):
                df_filtered[DATE_OPERATION_COLUMN] = pd.to_datetime(
                    df_filtered[DATE_OPERATION_COLUMN], format="%d.%m.%Y %H:%M:%S", errors="coerce"
                )

        # Фильтрация по диапазону дат
        df_filtered = df_filtered[
            (df_filtered[DATE_OPERATION_COLUMN] >= period_start) & (df_filtered[DATE_OPERATION_COLUMN] <= period_end)
        ]

        # Только расходы (отрицательные суммы)
        df_filtered = df_filtered[df_filtered[AMOUNT_COLUMN] < 0]

        if df_filtered.empty:
            logger.info("Не найдено трат за последние 3 месяца")
            return pd.DataFrame()

        # Определение типа дня (рабочий/выходной)
        df_filtered["day_of_week"] = df_filtered[DATE_OPERATION_COLUMN].dt.dayofweek
        df_filtered[DAY_TYPE_COLUMN] = df_filtered["day_of_week"].apply(
            lambda x: WORKDAY if WORKDAY_START <= x <= WORKDAY_END else WEEKEND
        )

        # Группировка по типу дня и расчет среднего
        result_df = df_filtered.groupby(DAY_TYPE_COLUMN)[AMOUNT_COLUMN].mean().abs().reset_index()
        result_df.columns = pd.Index([DAY_TYPE_COLUMN, AVERAGE_AMOUNT_COLUMN], dtype=object)

        logger.info(f"Рассчитаны средние траты для {len(result_df)} типов дней")
        return result_df

    except Exception as e:
        logger.error(f"Ошибка при анализе трат по типам дней: {type(e).__name__} - {e}")
        return pd.DataFrame()
