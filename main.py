"""Главный модуль для запуска всех функций приложения.

Этот модуль демонстрирует работу всех реализованных функциональностей:
- Веб-страницы (views)
- Сервисы (services)
- Отчеты (reports)
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, cast

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (
    investment_bank,
    profitable_cashback_categories,
    search_by_phone,
    search_person_transfers,
    simple_search,
)
from src.utils import load_transactions_from_excel
from src.views import events_page, home_page

# Константы модуля
ENCODING = "utf-8"
FILE_WRITE_MODE = "w"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_EXCEL_FILE = "data/operations.xlsx"
DEFAULT_DATE_TIME = "2024-03-15 12:00:00"
DEFAULT_DATE = "2024-03-15"
DEFAULT_YEAR = 2024
DEFAULT_MONTH = 3
DEFAULT_LIMIT = 50
DEFAULT_SEARCH_QUERY = "Лента"
DEFAULT_CATEGORY = "Супермаркеты"


def _setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля main.

    Returns:
        Настроенный логгер для модуля main
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    # Определяем корень проекта (main.py находится в корне)
    # Для единообразия с другими модулями используем parent, так как main.py в корне
    project_root = Path(__file__).parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "main.log"
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


def demo_views() -> None:
    """
    Демонстрирует работу функций веб-страниц.

    Вызывает функции home_page и events_page с тестовыми данными
    и выводит результаты в логи.
    """
    logger.info("=== Демонстрация веб-страниц ===")

    try:
        # Загрузка транзакций для веб-страниц
        logger.info(f"Загрузка транзакций из {DEFAULT_EXCEL_FILE}...")
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)

        if df.empty:
            logger.warning("Не удалось загрузить транзакции или файл пуст")
            return

        # Демонстрация главной страницы
        logger.info("Генерация данных для главной страницы...")
        home_data = home_page(DEFAULT_DATE_TIME, df)
        logger.info(f"Главная страница: приветствие = {home_data.get('greeting', 'N/A')}")
        logger.info(f"Количество карт: {len(home_data.get('cards', []))}")
        logger.info(f"Топ транзакций: {len(home_data.get('top_transactions', []))}")

        # Демонстрация страницы событий
        logger.info("Генерация данных для страницы событий...")
        events_data = events_page(DEFAULT_DATE, "M", df)
        logger.info(
            f"Страница событий: общая сумма расходов = {events_data.get('expenses', {}).get('total_amount', 0)}"
        )
        logger.info(f"Общая сумма поступлений = {events_data.get('income', {}).get('total_amount', 0)}")

        logger.info("Демонстрация веб-страниц завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка при демонстрации веб-страниц: {type(e).__name__} - {e}")


def demo_services() -> None:
    """
    Демонстрирует работу сервисов.

    Загружает транзакции и вызывает все функции сервисов с тестовыми данными.
    """
    logger.info("=== Демонстрация сервисов ===")

    try:
        # Загрузка транзакций
        logger.info(f"Загрузка транзакций из {DEFAULT_EXCEL_FILE}...")
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)

        if df.empty:
            logger.warning("Не удалось загрузить транзакции или файл пуст")
            return

        # Преобразование DataFrame в список словарей для сервисов
        # pandas возвращает dict[Hashable, Any], поэтому используем cast для типизации
        transactions = cast(List[Dict[str, Any]], df.to_dict(orient="records"))

        # Демонстрация выгодных категорий кешбэка
        logger.info("Анализ выгодных категорий кешбэка...")
        cashback_categories = profitable_cashback_categories(transactions, DEFAULT_YEAR, DEFAULT_MONTH)
        logger.info(f"Найдено категорий с кешбэком: {len(cashback_categories)}")

        # Демонстрация инвесткопилки
        logger.info("Расчет инвесткопилки...")
        month_str = f"{DEFAULT_YEAR}-{DEFAULT_MONTH:02d}"
        investment_amount = investment_bank(month_str, transactions, DEFAULT_LIMIT)
        logger.info(f"Сумма округлений для инвесткопилки: {investment_amount:.2f}")

        # Демонстрация простого поиска
        logger.info(f"Поиск транзакций по запросу '{DEFAULT_SEARCH_QUERY}'...")
        search_result = simple_search(DEFAULT_SEARCH_QUERY, transactions)
        logger.info(f"Найдено транзакций: {len(search_result.get('transactions', []))}")

        # Демонстрация поиска по телефонным номерам
        logger.info("Поиск транзакций с телефонными номерами...")
        phone_result = search_by_phone(transactions)
        logger.info(f"Найдено транзакций с номерами: {len(phone_result.get('transactions', []))}")

        # Демонстрация поиска переводов физическим лицам
        logger.info("Поиск переводов физическим лицам...")
        person_transfers = search_person_transfers(transactions)
        logger.info(f"Найдено переводов: {len(person_transfers.get('transactions', []))}")

        logger.info("Демонстрация сервисов завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка при демонстрации сервисов: {type(e).__name__} - {e}")


def demo_reports() -> None:
    """
    Демонстрирует работу отчетов.

    Загружает транзакции и вызывает все функции отчетов.
    """
    logger.info("=== Демонстрация отчетов ===")

    try:
        # Загрузка транзакций
        logger.info(f"Загрузка транзакций из {DEFAULT_EXCEL_FILE}...")
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)

        if df.empty:
            logger.warning("Не удалось загрузить транзакции или файл пуст")
            return

        # Демонстрация трат по категории
        logger.info(f"Анализ трат по категории '{DEFAULT_CATEGORY}'...")
        category_report = spending_by_category(df, DEFAULT_CATEGORY, DEFAULT_DATE)
        logger.info(f"Отчет по категории: {len(category_report)} записей")

        # Демонстрация трат по дням недели
        logger.info("Анализ трат по дням недели...")
        weekday_report = spending_by_weekday(df, DEFAULT_DATE)
        logger.info(f"Отчет по дням недели: {len(weekday_report)} записей")

        # Демонстрация трат в рабочий/выходной день
        logger.info("Анализ трат в рабочие и выходные дни...")
        workday_report = spending_by_workday(df, DEFAULT_DATE)
        logger.info(f"Отчет по типам дней: {len(workday_report)} записей")

        logger.info("Демонстрация отчетов завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка при демонстрации отчетов: {type(e).__name__} - {e}")


def main() -> None:
    """
    Главная функция для запуска всех демонстраций.

    Вызывает демонстрации веб-страниц, сервисов и отчетов.
    Обрабатывает ошибки и логирует результаты.
    """
    logger.info("=" * 50)
    logger.info("Запуск главного модуля приложения")
    logger.info("=" * 50)

    try:
        # Демонстрация веб-страниц
        demo_views()

        # Демонстрация сервисов
        demo_services()

        # Демонстрация отчетов
        demo_reports()

        logger.info("=" * 50)
        logger.info("Все демонстрации завершены успешно")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Критическая ошибка в главном модуле: {type(e).__name__} - {e}")
        raise


if __name__ == "__main__":
    main()
