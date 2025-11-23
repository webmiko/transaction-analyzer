"""Демонстрационный модуль для показа работы функций проекта.

Этот модуль демонстрирует работу всех реализованных функций:
- views.py: home_page и events_page
- utils.py: вспомогательные функции
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from src.views import events_page, home_page

# Константы модуля
ENCODING = "utf-8"
FILE_WRITE_MODE = "w"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
SEPARATOR_LENGTH = 80
SEPARATOR_CHAR = "="
DEFAULT_DATE_TIME = "2024-03-15 14:30:00"
DEFAULT_DATE = "2024-03-15"
DEFAULT_PERIOD = "M"
PERIOD_WEEK = "W"
PERIOD_MONTH = "M"
PERIOD_YEAR = "Y"
PERIOD_ALL = "ALL"
PERIOD_NAMES = {
    PERIOD_WEEK: "Неделя",
    PERIOD_MONTH: "Месяц",
    PERIOD_YEAR: "Год",
    PERIOD_ALL: "Все данные",
}


def _setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля demo.

    Returns:
        Настроенный логгер для модуля demo
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "demo.log"
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


def demo_home_page() -> None:
    """Демонстрация работы функции home_page."""
    separator = SEPARATOR_CHAR * SEPARATOR_LENGTH
    print(separator)
    print("ДЕМОНСТРАЦИЯ: Главная страница (home_page)")
    print(separator)

    # Пример даты и времени
    date_time = DEFAULT_DATE_TIME
    print(f"\n📅 Дата и время: {date_time}")
    print("\nВызов функции home_page...")

    try:
        result = home_page(date_time)

        print("\n✅ Результат:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print("\n📊 Краткая статистика:")
        print(f"  - Приветствие: {result.get('greeting', 'N/A')}")
        print(f"  - Количество карт: {len(result.get('cards', []))}")
        print(f"  - Топ транзакций: {len(result.get('top_transactions', []))}")
        print(f"  - Курсов валют: {len(result.get('currency_rates', []))}")
        print(f"  - Цен акций: {len(result.get('stock_prices', []))}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logger.error(f"Ошибка при демонстрации home_page: {type(e).__name__} - {e}")


def demo_events_page() -> None:
    """Демонстрация работы функции events_page."""
    separator = SEPARATOR_CHAR * SEPARATOR_LENGTH
    print("\n" + separator)
    print("ДЕМОНСТРАЦИЯ: Страница событий (events_page)")
    print(separator)

    # Пример даты и периода
    date = DEFAULT_DATE
    period = DEFAULT_PERIOD
    period_name = PERIOD_NAMES.get(period, "Месяц")
    print(f"\n📅 Дата: {date}, Период: {period} ({period_name})")
    print("\nВызов функции events_page...")

    try:
        result = events_page(date, period)

        print("\n✅ Результат:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print("\n📊 Краткая статистика:")
        expenses = result.get("expenses", {})
        income = result.get("income", {})
        print(f"  - Общая сумма расходов: {expenses.get('total_amount', 0)} руб.")
        print(f"  - Основных категорий расходов: {len(expenses.get('main', []))}")
        print(f"  - Переводы и наличные: {len(expenses.get('transfers_and_cash', []))}")
        print(f"  - Общая сумма поступлений: {income.get('total_amount', 0)} руб.")
        print(f"  - Категорий поступлений: {len(income.get('main', []))}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logger.error(f"Ошибка при демонстрации events_page: {type(e).__name__} - {e}")


def demo_all_periods() -> None:
    """Демонстрация работы events_page для всех периодов."""
    separator = SEPARATOR_CHAR * SEPARATOR_LENGTH
    print("\n" + separator)
    print("ДЕМОНСТРАЦИЯ: Страница событий для разных периодов")
    print(separator)

    date = DEFAULT_DATE
    periods = [PERIOD_WEEK, PERIOD_MONTH, PERIOD_YEAR, PERIOD_ALL]

    for period in periods:
        period_name = PERIOD_NAMES.get(period, period)
        print(f"\n📅 Период: {period} ({period_name})")

        try:
            result = events_page(date, period)
            expenses_total = result.get("expenses", {}).get("total_amount", 0)
            income_total = result.get("income", {}).get("total_amount", 0)
            print(f"  ✅ Расходы: {expenses_total} руб., Поступления: {income_total} руб.")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            logger.error(f"Ошибка при демонстрации периода {period}: {type(e).__name__} - {e}")


def main() -> None:
    """Главная функция для запуска всех демонстраций."""
    separator = SEPARATOR_CHAR * SEPARATOR_LENGTH
    print("\n" + separator)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ПРОЕКТА TRANSACTION ANALYZER")
    print(separator)
    print(f"\n🕐 Время запуска: {datetime.now().strftime(TIMESTAMP_FORMAT)}")

    try:
        # Демонстрация главной страницы
        demo_home_page()

        # Демонстрация страницы событий
        demo_events_page()

        # Демонстрация разных периодов
        demo_all_periods()

        print("\n" + separator)
        print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print(separator)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка при демонстрации: {type(e).__name__} - {e}")


if __name__ == "__main__":
    main()
