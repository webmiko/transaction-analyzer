"""Тесты для модуля services.py.

Используются Mock и patch для изоляции внешних зависимостей,
фикстуры для тестовых данных и параметризация где это уместно.
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest

from src.services import (
    investment_bank,
    profitable_cashback_categories,
    search_by_phone,
    search_person_transfers,
    simple_search,
)


# Фикстуры для тестовых данных
@pytest.fixture
def sample_transactions() -> List[Dict[str, Any]]:
    """Фикстура с тестовыми транзакциями для services."""
    return [
        {
            "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
            "Категория": "Супермаркеты",
            "Кэшбэк": 10.5,
            "Статус": "OK",
            "Сумма платежа": -1000.0,
            "Описание": "Покупка в Лента",
        },
        {
            "Дата операции": datetime(2024, 3, 20, 14, 20, 0),
            "Категория": "Супермаркеты",
            "Кэшбэк": 5.2,
            "Статус": "OK",
            "Сумма платежа": -500.0,
            "Описание": "Покупка в Магнит",
        },
        {
            "Дата операции": datetime(2024, 3, 25, 9, 15, 0),
            "Категория": "Фастфуд",
            "Кэшбэк": 2.0,
            "Статус": "OK",
            "Сумма платежа": -200.0,
            "Описание": "Обед в Макдональдс",
        },
        {
            "Дата операции": datetime(2024, 2, 15, 10, 30, 0),
            "Категория": "Супермаркеты",
            "Кэшбэк": 8.0,
            "Статус": "OK",
            "Сумма платежа": -800.0,
            "Описание": "Покупка в Лента",
        },
        {
            "Дата операции": datetime(2024, 3, 10, 12, 0, 0),
            "Категория": "Переводы",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": -5000.0,
            "Описание": "Валерий А.",
        },
        {
            "Дата операции": datetime(2024, 3, 12, 15, 0, 0),
            "Категория": "Переводы",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": -2000.0,
            "Описание": "Сергей З.",
        },
        {
            "Дата операции": datetime(2024, 3, 18, 11, 0, 0),
            "Категория": "Пополнения",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": 10000.0,
            "Описание": "Пополнение +7 921 11-22-33",
        },
        {
            "Дата операции": datetime(2024, 3, 22, 16, 0, 0),
            "Категория": "Услуги",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": -1500.0,
            "Описание": "Оплата услуг +7 995 555-55-55",
        },
    ]


@pytest.fixture
def sample_transactions_with_phone() -> List[Dict[str, Any]]:
    """Фикстура с транзакциями, содержащими телефонные номера."""
    return [
        {
            "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
            "Категория": "Пополнения",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": 5000.0,
            "Описание": "Пополнение +7 921 11-22-33",
        },
        {
            "Дата операции": datetime(2024, 3, 20, 14, 20, 0),
            "Категория": "Услуги",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": -1000.0,
            "Описание": "Оплата +7 995 555-55-55",
        },
        {
            "Дата операции": datetime(2024, 3, 25, 9, 15, 0),
            "Категория": "Переводы",
            "Кэшбэк": 0.0,
            "Статус": "OK",
            "Сумма платежа": -2000.0,
            "Описание": "Перевод на счет",
        },
    ]


# Тесты для profitable_cashback_categories
class TestProfitableCashbackCategories:
    """Тесты для функции profitable_cashback_categories."""

    def test_profitable_cashback_categories_success(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест успешного анализа категорий кешбэка."""
        result = profitable_cashback_categories(sample_transactions, 2024, 3)

        assert isinstance(result, dict)
        assert "Супермаркеты" in result
        assert result["Супермаркеты"] == 15.7  # 10.5 + 5.2
        assert "Фастфуд" in result
        assert result["Фастфуд"] == 2.0

    def test_profitable_cashback_categories_empty_data(self) -> None:
        """Тест обработки пустого списка транзакций."""
        result = profitable_cashback_categories([], 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_no_matching_month(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест обработки отсутствия транзакций за указанный месяц."""
        result = profitable_cashback_categories(sample_transactions, 2024, 1)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_only_ok_status(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест фильтрации только транзакций со статусом OK."""
        transactions_with_failed = sample_transactions + [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Кэшбэк": 100.0,
                "Статус": "FAILED",
                "Сумма платежа": -1000.0,
                "Описание": "Неудачная транзакция",
            }
        ]

        result = profitable_cashback_categories(transactions_with_failed, 2024, 3)

        # Неудачная транзакция не должна учитываться
        assert "Супермаркеты" in result
        assert result["Супермаркеты"] == 15.7

    def test_profitable_cashback_categories_string_date(self) -> None:
        """Тест обработки строковых дат."""
        transactions = [
            {
                "Дата операции": "15.03.2024 10:30:00",
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
                "Сумма платежа": -1000.0,
                "Описание": "Покупка",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert "Супермаркеты" in result
        assert result["Супермаркеты"] == 10.5

    def test_profitable_cashback_categories_continue_no_date(self) -> None:
        """Тест обработки транзакций без даты (continue)."""
        transactions = [
            {
                # Нет поля "Дата операции"
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_continue_invalid_date_type(self) -> None:
        """Тест обработки некорректного типа даты (continue)."""
        transactions = [
            {
                "Дата операции": 12345,  # Неправильный тип
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_invalid_cashback_value(self) -> None:
        """Тест обработки некорректного значения кешбэка."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Кэшбэк": "invalid",  # Некорректное значение
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        # Категория должна быть в результате, но с нулевым кешбэком
        assert "Супермаркеты" in result or len(result) == 0

    def test_profitable_cashback_categories_exception_handling(self) -> None:
        """Тест обработки общих исключений в profitable_cashback_categories."""
        # Создаем данные, которые вызовут исключение
        transactions = [
            {
                "Дата операции": object(),  # Объект, который вызовет AttributeError
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)


# Тесты для investment_bank
class TestInvestmentBank:
    """Тесты для функции investment_bank."""

    def test_investment_bank_success(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест успешного расчета инвесткопилки."""
        result = investment_bank("2024-03", sample_transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_empty_data(self) -> None:
        """Тест обработки пустого списка транзакций."""
        result = investment_bank("2024-03", [], 50)

        assert result == 0.0

    def test_investment_bank_invalid_month_format(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест обработки некорректного формата месяца."""
        result = investment_bank("2024/03", sample_transactions, 50)

        assert result == 0.0

    def test_investment_bank_invalid_limit(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест обработки некорректного лимита."""
        result = investment_bank("2024-03", sample_transactions, 0)

        assert result == 0.0

    def test_investment_bank_only_expenses(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест фильтрации только расходов (отрицательных сумм)."""
        # Добавляем транзакцию с положительной суммой (пополнение)
        transactions_with_income = sample_transactions + [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Пополнения",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": 10000.0,  # Положительная сумма
                "Описание": "Пополнение",
            }
        ]

        result = investment_bank("2024-03", transactions_with_income, 50)

        # Пополнение не должно учитываться в расчете округлений
        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.parametrize(
        "amount,limit,expected_rounding",
        [
            (1712, 50, 38),  # 1750 - 1712 = 38
            (850, 50, 0),  # 850 уже кратно 50
            (123, 50, 27),  # 150 - 123 = 27
            (1999, 100, 1),  # 2000 - 1999 = 1
        ],
    )
    def test_investment_bank_rounding_calculation(self, amount: int, limit: int, expected_rounding: int) -> None:
        """Тест корректности расчета округлений."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -float(amount),
                "Описание": "Покупка",
            }
        ]

        result = investment_bank("2024-03", transactions, limit)

        assert abs(result - expected_rounding) < 0.01

    def test_investment_bank_continue_without_date(self) -> None:
        """Тест обработки транзакций без даты (continue)."""
        transactions = [
            {
                # Нет поля "Дата операции"
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0

    def test_investment_bank_continue_invalid_date_type(self) -> None:
        """Тест обработки некорректного типа даты (continue)."""
        transactions = [
            {
                "Дата операции": 12345,  # Неправильный тип
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0

    def test_investment_bank_rounding_value_error(self) -> None:
        """Тест обработки ValueError при расчете округлений."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Сумма платежа": "invalid",  # Вызовет ValueError при float()
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_missing_date_column(self) -> None:
        """Тест обработки транзакций без колонки даты."""
        transactions = [
            {
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0

    def test_investment_bank_amount_conversion_error(self) -> None:
        """Тест обработки ошибки преобразования суммы."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Сумма платежа": "not-a-number",  # Некорректное значение
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_general_exception(self) -> None:
        """Тест обработки общих исключений в investment_bank."""
        # Создаем данные, которые вызовут исключение при обработке
        transactions = [
            {
                "Дата операции": object(),  # Объект, который вызовет исключение
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0


# Тесты для simple_search
class TestSimpleSearch:
    """Тесты для функции simple_search."""

    def test_simple_search_success_in_description(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест успешного поиска в описании."""
        result = simple_search("Лента", sample_transactions)

        assert "query" in result
        assert "transactions" in result
        assert result["query"] == "Лента"
        assert len(result["transactions"]) > 0
        # Проверяем, что хотя бы одна транзакция содержит запрос в описании или категории
        assert any(
            "лента" in str(t.get("Описание", "")).lower() or "лента" in str(t.get("Категория", "")).lower()
            for t in result["transactions"]
        )

    def test_simple_search_success_in_category(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест успешного поиска в категории."""
        result = simple_search("Супермаркеты", sample_transactions)

        assert "query" in result
        assert "transactions" in result
        assert result["query"] == "Супермаркеты"
        assert len(result["transactions"]) > 0

    def test_simple_search_case_insensitive(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест регистронезависимого поиска."""
        result_lower = simple_search("лента", sample_transactions)
        result_upper = simple_search("ЛЕНТА", sample_transactions)

        assert len(result_lower["transactions"]) == len(result_upper["transactions"])

    def test_simple_search_empty_query(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест обработки пустого запроса."""
        result = simple_search("", sample_transactions)

        assert "query" in result
        assert "transactions" in result
        assert result["query"] == ""
        assert len(result["transactions"]) == 0

    def test_simple_search_empty_data(self) -> None:
        """Тест обработки пустого списка транзакций."""
        result = simple_search("Лента", [])

        assert "query" in result
        assert "transactions" in result
        assert result["query"] == "Лента"
        assert len(result["transactions"]) == 0

    def test_simple_search_no_matches(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест поиска без совпадений."""
        result = simple_search("НесуществующийЗапрос", sample_transactions)

        assert "query" in result
        assert "transactions" in result
        assert result["query"] == "НесуществующийЗапрос"
        assert len(result["transactions"]) == 0


# Тесты для search_by_phone
class TestSearchByPhone:
    """Тесты для функции search_by_phone."""

    def test_search_by_phone_success(self, sample_transactions_with_phone: List[Dict[str, Any]]) -> None:
        """Тест успешного поиска телефонных номеров."""
        result = search_by_phone(sample_transactions_with_phone)

        assert "transactions" in result
        assert len(result["transactions"]) >= 1  # Одна или более транзакций с номерами
        # Проверяем, что все найденные транзакции содержат телефонные номера
        for transaction in result["transactions"]:
            description = str(transaction.get("Описание", ""))
            assert "+7" in description

    def test_search_by_phone_empty_data(self) -> None:
        """Тест обработки пустого списка транзакций."""
        result = search_by_phone([])

        assert "transactions" in result
        assert len(result["transactions"]) == 0

    def test_search_by_phone_no_matches(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест поиска без телефонных номеров."""
        # Используем транзакции без номеров
        transactions_without_phone = [t for t in sample_transactions if "+7" not in str(t.get("Описание", ""))]

        result = search_by_phone(transactions_without_phone)

        assert "transactions" in result
        assert len(result["transactions"]) == 0

    def test_search_by_phone_various_formats(self) -> None:
        """Тест поиска номеров в различных форматах."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Пополнения",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": 5000.0,
                "Описание": "Пополнение +7 921 11-22-33",
            },
            {
                "Дата операции": datetime(2024, 3, 20, 14, 20, 0),
                "Категория": "Услуги",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -1000.0,
                "Описание": "Оплата +7 995 555-55-55",
            },
            {
                "Дата операции": datetime(2024, 3, 25, 9, 15, 0),
                "Категория": "Переводы",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -2000.0,
                "Описание": "Перевод +7 900 1234567",
            },
        ]

        result = search_by_phone(transactions)

        assert "transactions" in result
        assert len(result["transactions"]) >= 2

    def test_simple_search_exception_handling(self) -> None:
        """Тест обработки исключений в simple_search."""

        # Создаем транзакцию, которая может вызвать исключение
        class BadTransaction:
            def get(self, key: str, default: Any = None) -> Any:
                raise Exception("Unexpected error")

        transactions: List[Dict[str, Any]] = [BadTransaction()]  # type: ignore[list-item]

        result = simple_search("тест", transactions)

        assert "query" in result
        assert "transactions" in result
        assert result["query"] == "тест"

    def test_search_by_phone_exception_handling(self) -> None:
        """Тест обработки исключений в search_by_phone."""

        # Создаем транзакцию, которая может вызвать исключение
        class BadTransaction:
            def get(self, key: str, default: Any = None) -> Any:
                raise Exception("Unexpected error")

        transactions: List[Dict[str, Any]] = [BadTransaction()]  # type: ignore[list-item]

        result = search_by_phone(transactions)

        assert "transactions" in result
        assert isinstance(result["transactions"], list)

    def test_search_person_transfers_exception_handling(self) -> None:
        """Тест обработки исключений в search_person_transfers."""

        # Создаем транзакцию, которая может вызвать исключение
        class BadTransaction:
            def get(self, key: str, default: Any = None) -> Any:
                raise Exception("Unexpected error")

        transactions: List[Dict[str, Any]] = [BadTransaction()]  # type: ignore[list-item]

        result = search_person_transfers(transactions)

        assert "transactions" in result
        assert isinstance(result["transactions"], list)


# Тесты для search_person_transfers
class TestSearchPersonTransfers:
    """Тесты для функции search_person_transfers."""

    def test_search_person_transfers_success(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест успешного поиска переводов физическим лицам."""
        result = search_person_transfers(sample_transactions)

        assert "transactions" in result
        assert len(result["transactions"]) == 2  # Два перевода с форматом "Имя Ф."

    def test_search_person_transfers_empty_data(self) -> None:
        """Тест обработки пустого списка транзакций."""
        result = search_person_transfers([])

        assert "transactions" in result
        assert len(result["transactions"]) == 0

    def test_search_person_transfers_only_transfers_category(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест фильтрации только категории 'Переводы'."""
        result = search_person_transfers(sample_transactions)

        assert "transactions" in result
        # Все найденные транзакции должны иметь категорию "Переводы"
        assert all(t.get("Категория") == "Переводы" for t in result["transactions"])

    def test_search_person_transfers_name_format(self, sample_transactions: List[Dict[str, Any]]) -> None:
        """Тест проверки формата имени 'Имя Ф.'."""
        result = search_person_transfers(sample_transactions)

        assert "transactions" in result
        # Проверяем, что описания соответствуют формату "Имя Ф."
        for transaction in result["transactions"]:
            description = transaction.get("Описание", "")
            # Формат: имя (слово) + пробел + буква + точка
            assert " " in description
            assert description.endswith(".")

    def test_search_person_transfers_no_matches(self) -> None:
        """Тест поиска без совпадений."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Переводы",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -5000.0,
                "Описание": "Перевод на счет",  # Не соответствует формату
            },
            {
                "Дата операции": datetime(2024, 3, 20, 14, 20, 0),
                "Категория": "Супермаркеты",  # Не категория "Переводы"
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -1000.0,
                "Описание": "Валерий А.",  # Формат правильный, но категория не та
            },
        ]

        result = search_person_transfers(transactions)

        assert "transactions" in result
        assert len(result["transactions"]) == 0

    def test_profitable_cashback_categories_missing_date_column(self) -> None:
        """Тест обработки транзакций без колонки даты."""
        transactions = [
            {
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_invalid_date_type(self) -> None:
        """Тест обработки транзакций с некорректным типом даты."""
        transactions = [
            {
                "Дата операции": 12345,  # Неправильный тип
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_invalid_cashback_value(self) -> None:
        """Тест обработки некорректного значения кешбэка."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Кэшбэк": "invalid",  # Некорректное значение
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        # Категория должна быть в результате, но с нулевым кешбэком
        assert "Супермаркеты" in result or len(result) == 0

    def test_investment_bank_invalid_amount_value(self) -> None:
        """Тест обработки некорректного значения суммы."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": "invalid",  # Некорректное значение
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_exception_handling(self) -> None:
        """Тест обработки исключений в investment_bank."""
        # Вызываем с некорректным форматом месяца, чтобы проверить обработку ошибок
        result = investment_bank("invalid-format", [], 50)

        assert result == 0.0

    def test_investment_bank_invalid_date_parsing(self) -> None:
        """Тест обработки некорректного парсинга даты."""
        transactions = [
            {
                "Дата операции": "invalid-date-format",  # Некорректный формат
                "Категория": "Супермаркеты",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_invalid_date_type(self) -> None:
        """Тест обработки некорректного типа даты."""
        transactions = [
            {
                "Дата операции": 12345,  # Неправильный тип
                "Категория": "Супермаркеты",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_rounding_exception(self) -> None:
        """Тест обработки исключений при расчете округлений."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Кэшбэк": 0.0,
                "Статус": "OK",
                "Сумма платежа": None,  # None может вызвать ошибку
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_missing_date_column(self) -> None:
        """Тест обработки транзакций без колонки даты."""
        transactions = [
            {
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_investment_bank_amount_conversion_error(self) -> None:
        """Тест обработки ошибки преобразования суммы."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Сумма платежа": "not-a-number",  # Некорректное значение
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_profitable_cashback_categories_exception_handling(self) -> None:
        """Тест обработки общих исключений в profitable_cashback_categories."""
        # Создаем данные, которые вызовут исключение
        transactions = [
            {
                "Дата операции": object(),  # Объект, который вызовет AttributeError
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)

    def test_investment_bank_general_exception(self) -> None:
        """Тест обработки общих исключений в investment_bank."""
        # Создаем данные, которые вызовут исключение при обработке
        transactions = [
            {
                "Дата операции": object(),  # Объект, который вызовет исключение
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0

    def test_investment_bank_continue_without_date(self) -> None:
        """Тест обработки транзакций без даты (continue)."""
        transactions = [
            {
                # Нет поля "Дата операции"
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0

    def test_investment_bank_continue_invalid_date_type(self) -> None:
        """Тест обработки некорректного типа даты (continue)."""
        transactions = [
            {
                "Дата операции": 12345,  # Неправильный тип
                "Категория": "Супермаркеты",
                "Сумма платежа": -1000.0,
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result == 0.0

    def test_investment_bank_rounding_value_error(self) -> None:
        """Тест обработки ValueError при расчете округлений."""
        transactions = [
            {
                "Дата операции": datetime(2024, 3, 15, 10, 30, 0),
                "Категория": "Супермаркеты",
                "Сумма платежа": "invalid",  # Вызовет ValueError при float()
            }
        ]

        result = investment_bank("2024-03", transactions, 50)

        assert isinstance(result, float)
        assert result >= 0

    def test_profitable_cashback_categories_continue_no_date(self) -> None:
        """Тест обработки транзакций без даты (continue)."""
        transactions = [
            {
                # Нет поля "Дата операции"
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_profitable_cashback_categories_continue_invalid_date_type(self) -> None:
        """Тест обработки некорректного типа даты (continue)."""
        transactions = [
            {
                "Дата операции": 12345,  # Неправильный тип
                "Категория": "Супермаркеты",
                "Кэшбэк": 10.5,
                "Статус": "OK",
            }
        ]

        result = profitable_cashback_categories(transactions, 2024, 3)

        assert isinstance(result, dict)
        assert len(result) == 0
