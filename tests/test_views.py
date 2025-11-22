"""Тесты для модуля views.py.

Используются Mock и patch для изоляции внешних зависимостей,
фикстуры для тестовых данных и параметризация где это уместно.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from src.views import events_page, home_page


# Фикстуры для тестовых данных
@pytest.fixture
def sample_transactions_df():
    """Фикстура с тестовыми данными транзакций для views."""
    data = {
        "Дата операции": pd.to_datetime(
            ["15.03.2024 10:30:00", "16.03.2024 14:20:00", "20.03.2024 09:15:00"],
            format="%d.%m.%Y %H:%M:%S",
        ),
        "Дата платежа": pd.to_datetime(["15.03.2024", "16.03.2024", "20.03.2024"], format="%d.%m.%Y"),
        "Номер карты": ["*7197", "*5814", "*7197"],
        "Статус": ["OK", "OK", "OK"],
        "Сумма операции": [-1000.0, 5000.0, -500.0],
        "Валюта операции": ["RUB", "RUB", "RUB"],
        "Сумма платежа": [-1000.0, 5000.0, -500.0],
        "Валюта платежа": ["RUB", "RUB", "RUB"],
        "Кэшбэк": [10.0, 50.0, 5.0],
        "Категория": ["Супермаркеты", "Пополнения", "Фастфуд"],
        "MCC": ["5411", "6012", "5814"],
        "Описание": ["Покупка в магазине", "Пополнение счета", "Обед"],
        "Бонусы (включая кэшбэк)": [10.0, 50.0, 5.0],
        "Округление на инвесткопилку": [0.0, 0.0, 0.0],
        "Сумма операции с округлением": [-1000.0, 5000.0, -500.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_user_settings():
    """Фикстура с тестовыми настройками пользователя."""
    return {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN"],
    }


@pytest.fixture
def sample_currency_rates():
    """Фикстура с тестовыми курсами валют."""
    return [
        {"currency": "USD", "rate": 73.21},
        {"currency": "EUR", "rate": 87.08},
    ]


@pytest.fixture
def sample_stock_prices():
    """Фикстура с тестовыми ценами акций."""
    return [
        {"stock": "AAPL", "price": 150.12},
        {"stock": "AMZN", "price": 3173.18},
    ]


# Тесты для home_page
class TestHomePage:
    """Тесты для функции home_page."""

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_home_page_success(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
        sample_currency_rates,
        sample_stock_prices,
    ):
        """Тест успешной генерации данных для главной страницы."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = sample_currency_rates
        mock_get_stocks.return_value = sample_stock_prices

        result = home_page("2024-03-20 14:30:00")

        assert "greeting" in result
        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result
        assert result["greeting"] == "Добрый день"
        assert len(result["cards"]) > 0
        assert len(result["top_transactions"]) <= 5

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_home_page_empty_data(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_user_settings,
    ):
        """Тест обработки пустых данных."""
        mock_load_excel.return_value = pd.DataFrame()
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = home_page("2024-03-15 14:30:00")

        assert result["greeting"] == "Добрый день"
        assert result["cards"] == []
        assert result["top_transactions"] == []
        assert result["currency_rates"] == []
        assert result["stock_prices"] == []

    @pytest.mark.parametrize(
        "date_time, expected_greeting",
        [
            ("2024-03-15 06:00:00", "Доброе утро"),
            ("2024-03-15 12:00:00", "Добрый день"),
            ("2024-03-15 18:00:00", "Добрый вечер"),
            ("2024-03-15 23:00:00", "Доброй ночи"),
            ("2024-03-15 04:00:00", "Доброй ночи"),
        ],
    )
    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_home_page_greeting(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        date_time,
        expected_greeting,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест определения приветствия по времени суток с параметризацией."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = home_page(date_time)

        assert result["greeting"] == expected_greeting

    @patch("src.views.load_transactions_from_excel")
    def test_home_page_invalid_date_format(self, mock_load_excel):
        """Тест обработки некорректного формата даты."""
        mock_load_excel.return_value = pd.DataFrame()

        # Функция обрабатывает ошибку и возвращает базовую структуру
        result = home_page("2024-03-15")  # Неправильный формат

        assert "greeting" in result
        assert result["cards"] == []
        assert result["top_transactions"] == []

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_home_page_cards_calculation(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест расчета данных по картам."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = home_page("2024-03-20 14:30:00")

        assert len(result["cards"]) > 0
        for card in result["cards"]:
            assert "last_digits" in card
            assert "total_spent" in card
            assert "cashback" in card
            assert card["total_spent"] >= 0
            assert card["cashback"] >= 0

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_home_page_top_transactions(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест формирования топ-5 транзакций."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = home_page("2024-03-20 14:30:00")

        assert len(result["top_transactions"]) <= 5
        for transaction in result["top_transactions"]:
            assert "date" in transaction
            assert "amount" in transaction
            assert "category" in transaction
            assert "description" in transaction

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_home_page_exception_handling(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
    ):
        """Тест обработки исключений."""
        mock_load_excel.side_effect = Exception("Unexpected error")
        mock_load_settings.return_value = {}
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = home_page("2024-03-15 14:30:00")

        # Должен вернуть базовую структуру
        assert "greeting" in result
        assert result["cards"] == []
        assert result["top_transactions"] == []


# Тесты для events_page
class TestEventsPage:
    """Тесты для функции events_page."""

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_success_month(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
        sample_currency_rates,
        sample_stock_prices,
    ):
        """Тест успешной генерации данных для страницы событий (месяц)."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = sample_currency_rates
        mock_get_stocks.return_value = sample_stock_prices

        result = events_page("2024-03-20", "M")

        assert "expenses" in result
        assert "income" in result
        assert "currency_rates" in result
        assert "stock_prices" in result
        assert "total_amount" in result["expenses"]
        assert "main" in result["expenses"]
        assert "transfers_and_cash" in result["expenses"]
        assert "total_amount" in result["income"]
        assert "main" in result["income"]

    @pytest.mark.parametrize(
        "period, period_name",
        [
            ("W", "неделя"),
            ("M", "месяц"),
            ("Y", "год"),
            ("ALL", "все данные"),
        ],
    )
    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_all_periods(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        period,
        period_name,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест работы events_page для всех периодов с параметризацией."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = events_page("2024-03-15", period)

        assert "expenses" in result
        assert "income" in result
        assert isinstance(result["expenses"]["total_amount"], int)
        assert isinstance(result["income"]["total_amount"], int)

    @patch("src.views.load_transactions_from_excel")
    def test_events_page_invalid_date_format(self, mock_load_excel):
        """Тест обработки некорректного формата даты."""
        mock_load_excel.return_value = pd.DataFrame()

        # Функция обрабатывает ошибку и возвращает базовую структуру
        result = events_page("2024/03/15", "M")  # Неправильный формат

        assert "expenses" in result
        assert "income" in result
        assert result["expenses"]["total_amount"] == 0
        assert result["income"]["total_amount"] == 0

    @patch("src.views.load_transactions_from_excel")
    def test_events_page_invalid_period(self, mock_load_excel):
        """Тест обработки некорректного периода."""
        mock_load_excel.return_value = pd.DataFrame()

        # Функция обрабатывает ошибку и возвращает базовую структуру
        result = events_page("2024-03-15", "INVALID")

        assert "expenses" in result
        assert "income" in result
        assert result["expenses"]["total_amount"] == 0
        assert result["income"]["total_amount"] == 0

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_empty_data(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_user_settings,
    ):
        """Тест обработки пустых данных."""
        mock_load_excel.return_value = pd.DataFrame()
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = events_page("2024-03-15", "M")

        assert result["expenses"]["total_amount"] == 0
        assert result["expenses"]["main"] == []
        assert result["expenses"]["transfers_and_cash"] == []
        assert result["income"]["total_amount"] == 0
        assert result["income"]["main"] == []

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_expenses_categories(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест обработки категорий расходов."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = events_page("2024-03-20", "M")

        assert "main" in result["expenses"]
        assert isinstance(result["expenses"]["main"], list)
        for category in result["expenses"]["main"]:
            assert "category" in category
            assert "amount" in category
            assert isinstance(category["amount"], int)

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_income_categories(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест обработки категорий поступлений."""
        mock_load_excel.return_value = sample_transactions_df
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = events_page("2024-03-20", "M")

        assert "main" in result["income"]
        assert isinstance(result["income"]["main"], list)
        for category in result["income"]["main"]:
            assert "category" in category
            assert "amount" in category
            assert isinstance(category["amount"], int)

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_transfers_and_cash(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
        sample_transactions_df,
        sample_user_settings,
    ):
        """Тест обработки переводов и наличных."""
        # Добавляем транзакции с категориями "Переводы" и "Наличные"
        df_with_transfers = sample_transactions_df.copy()
        new_row = {
            "Дата операции": pd.to_datetime("25.03.2024 12:00:00", format="%d.%m.%Y %H:%M:%S"),
            "Дата платежа": pd.to_datetime("25.03.2024", format="%d.%m.%Y"),
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -200.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -200.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.0,
            "Категория": "Переводы",
            "MCC": "6012",
            "Описание": "Перевод",
            "Бонусы (включая кэшбэк)": 0.0,
            "Округление на инвесткопилку": 0.0,
            "Сумма операции с округлением": -200.0,
        }
        df_with_transfers = pd.concat([df_with_transfers, pd.DataFrame([new_row])], ignore_index=True)

        mock_load_excel.return_value = df_with_transfers
        mock_load_settings.return_value = sample_user_settings
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = events_page("2024-03-25", "M")

        assert "transfers_and_cash" in result["expenses"]
        assert isinstance(result["expenses"]["transfers_and_cash"], list)

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions_from_excel")
    def test_events_page_exception_handling(
        self,
        mock_load_excel,
        mock_load_settings,
        mock_get_currency,
        mock_get_stocks,
    ):
        """Тест обработки исключений."""
        mock_load_excel.side_effect = Exception("Unexpected error")
        mock_load_settings.return_value = {}
        mock_get_currency.return_value = []
        mock_get_stocks.return_value = []

        result = events_page("2024-03-15", "M")

        # Должен вернуть базовую структуру
        assert "expenses" in result
        assert "income" in result
        assert result["expenses"]["total_amount"] == 0
        assert result["income"]["total_amount"] == 0
