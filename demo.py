"""Демонстрационный модуль для показа работы функций проекта.

Этот модуль демонстрирует работу всех реализованных функций:
- views.py: home_page и events_page
- utils.py: вспомогательные функции
"""

import json
from datetime import datetime

from src.logger_config import setup_logger
from src.views import events_page, home_page

# Настройка логгера
logger = setup_logger(__name__)


def demo_home_page() -> None:
    """Демонстрация работы функции home_page."""
    print("=" * 80)
    print("ДЕМОНСТРАЦИЯ: Главная страница (home_page)")
    print("=" * 80)

    # Пример даты и времени
    date_time = "2024-03-15 14:30:00"
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
        logger.error(f"Ошибка при демонстрации home_page: {e}", exc_info=True)


def demo_events_page() -> None:
    """Демонстрация работы функции events_page."""
    print("\n" + "=" * 80)
    print("ДЕМОНСТРАЦИЯ: Страница событий (events_page)")
    print("=" * 80)

    # Пример даты и периода
    date = "2024-03-15"
    period = "M"  # Месяц
    print(f"\n📅 Дата: {date}, Период: {period} (M - месяц)")
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
        logger.error(f"Ошибка при демонстрации events_page: {e}", exc_info=True)


def demo_all_periods() -> None:
    """Демонстрация работы events_page для всех периодов."""
    print("\n" + "=" * 80)
    print("ДЕМОНСТРАЦИЯ: Страница событий для разных периодов")
    print("=" * 80)

    date = "2024-03-15"
    periods = ["W", "M", "Y", "ALL"]

    for period in periods:
        period_names = {
            "W": "Неделя",
            "M": "Месяц",
            "Y": "Год",
            "ALL": "Все данные",
        }
        print(f"\n📅 Период: {period} ({period_names[period]})")

        try:
            result = events_page(date, period)
            expenses_total = result.get("expenses", {}).get("total_amount", 0)
            income_total = result.get("income", {}).get("total_amount", 0)
            print(f"  ✅ Расходы: {expenses_total} руб., Поступления: {income_total} руб.")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")


def main() -> None:
    """Главная функция для запуска всех демонстраций."""
    print("\n" + "=" * 80)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ПРОЕКТА TRANSACTION ANALYZER")
    print("=" * 80)
    print(f"\n🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Демонстрация главной страницы
        demo_home_page()

        # Демонстрация страницы событий
        demo_events_page()

        # Демонстрация разных периодов
        demo_all_periods()

        print("\n" + "=" * 80)
        print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка при демонстрации: {e}", exc_info=True)


if __name__ == "__main__":
    main()
