"""Тесты для модуля utils.py.

Используются Mock и patch для изоляции внешних зависимостей,
фикстуры для тестовых данных и параметризация где это уместно.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
import requests

from src.utils import (
    format_date,
    get_currency_rates,
    get_month_range,
    get_month_start,
    get_stock_prices,
    get_three_months_back,
    load_transactions_from_excel,
    load_user_settings,
    parse_date,
    save_json,
)


# Фикстуры для тестовых данных
@pytest.fixture
def sample_transactions_df():
    """Фикстура с тестовыми данными транзакций."""
    data = {
        "Дата операции": ["15.03.2024 10:30:00", "16.03.2024 14:20:00"],
        "Дата платежа": ["15.03.2024", "16.03.2024"],
        "Номер карты": ["*7197", "*5814"],
        "Статус": ["OK", "OK"],
        "Сумма операции": [-1000.0, 5000.0],
        "Валюта операции": ["RUB", "RUB"],
        "Сумма платежа": [-1000.0, 5000.0],
        "Валюта платежа": ["RUB", "RUB"],
        "Кэшбэк": [10.0, 50.0],
        "Категория": ["Супермаркеты", "Пополнения"],
        "MCC": ["5411", "6012"],
        "Описание": ["Покупка в магазине", "Пополнение счета"],
        "Бонусы (включая кэшбэк)": [10.0, 50.0],
        "Округление на инвесткопилку": [0.0, 0.0],
        "Сумма операции с округлением": [-1000.0, 5000.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_user_settings():
    """Фикстура с тестовыми настройками пользователя."""
    return {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL"],
    }


# Тесты для load_transactions_from_excel
class TestLoadTransactionsFromExcel:
    """Тесты для функции load_transactions_from_excel."""

    @patch("src.utils.pd.read_excel")
    @patch("src.utils.os.path.exists")
    def test_load_transactions_from_excel_success(self, mock_exists, mock_read_excel, sample_transactions_df):
        """Тест успешной загрузки транзакций из Excel."""
        mock_exists.return_value = True
        mock_read_excel.return_value = sample_transactions_df

        result = load_transactions_from_excel("data/test.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        mock_read_excel.assert_called_once_with("data/test.xlsx", engine="openpyxl")

    @patch("src.utils.os.path.exists")
    def test_load_transactions_from_excel_file_not_found(self, mock_exists):
        """Тест обработки ошибки при отсутствии файла."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            load_transactions_from_excel("data/nonexistent.xlsx")

    @patch("src.utils.pd.read_excel")
    @patch("src.utils.os.path.exists")
    def test_load_transactions_from_excel_missing_columns(self, mock_exists, mock_read_excel):
        """Тест обработки ошибки при отсутствии необходимых колонок."""
        mock_exists.return_value = True
        # DataFrame без необходимых колонок
        mock_read_excel.return_value = pd.DataFrame({"col1": [1, 2]})

        with pytest.raises(ValueError, match="Отсутствуют необходимые колонки"):
            load_transactions_from_excel("data/test.xlsx")

    @patch("src.utils.pd.read_excel")
    @patch("src.utils.os.path.exists")
    def test_load_transactions_from_excel_empty_file(self, mock_exists, mock_read_excel):
        """Тест обработки пустого файла."""
        mock_exists.return_value = True
        # DataFrame с правильными колонками, но пустой
        empty_df = pd.DataFrame(
            columns=[
                "Дата операции",
                "Дата платежа",
                "Номер карты",
                "Статус",
                "Сумма операции",
                "Валюта операции",
                "Сумма платежа",
                "Валюта платежа",
                "Кэшбэк",
                "Категория",
                "MCC",
                "Описание",
                "Бонусы (включая кэшбэк)",
                "Округление на инвесткопилку",
                "Сумма операции с округлением",
            ]
        )
        mock_read_excel.return_value = empty_df

        result = load_transactions_from_excel("data/test.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch("src.utils.pd.read_excel")
    @patch("src.utils.os.path.exists")
    def test_load_transactions_from_excel_invalid_dates(self, mock_exists, mock_read_excel, sample_transactions_df):
        """Тест обработки некорректных дат в данных."""
        mock_exists.return_value = True
        # DataFrame с некорректными датами
        df_with_invalid_dates = sample_transactions_df.copy()
        df_with_invalid_dates.loc[0, "Дата операции"] = "invalid_date"
        df_with_invalid_dates.loc[1, "Дата платежа"] = "invalid_date"
        mock_read_excel.return_value = df_with_invalid_dates

        result = load_transactions_from_excel("data/test.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @patch("src.utils.pd.read_excel")
    @patch("src.utils.os.path.exists")
    def test_load_transactions_from_excel_general_exception(self, mock_exists, mock_read_excel):
        """Тест обработки общего исключения при загрузке."""
        mock_exists.return_value = True
        mock_read_excel.side_effect = Exception("Unexpected error")

        result = load_transactions_from_excel("data/test.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert result.empty


# Тесты для parse_date с параметризацией
@pytest.mark.parametrize(
    "date_string, expected_date",
    [
        ("15.03.2024", datetime(2024, 3, 15, 0, 0, 0)),
        ("01.01.2024", datetime(2024, 1, 1, 0, 0, 0)),
        ("31.12.2023", datetime(2023, 12, 31, 0, 0, 0)),
        ("29.02.2024", datetime(2024, 2, 29, 0, 0, 0)),  # Високосный год
    ],
)
def test_parse_date_success(date_string, expected_date):
    """Тест успешного парсинга даты с параметризацией."""
    result = parse_date(date_string)
    assert result == expected_date


@pytest.mark.parametrize(
    "invalid_date_string",
    [
        "2024-03-15",  # Неправильный формат
        "15/03/2024",  # Неправильный разделитель
        "32.01.2024",  # Некорректный день
        "15.13.2024",  # Некорректный месяц
        "invalid",  # Не дата
    ],
)
def test_parse_date_invalid_format(invalid_date_string):
    """Тест обработки некорректного формата даты с параметризацией."""
    with pytest.raises(ValueError, match="Некорректный формат даты"):
        parse_date(invalid_date_string)


# Тесты для format_date с параметризацией
@pytest.mark.parametrize(
    "date, expected_string",
    [
        (datetime(2024, 3, 15, 0, 0, 0), "15.03.2024"),
        (datetime(2024, 1, 1, 0, 0, 0), "01.01.2024"),
        (datetime(2023, 12, 31, 0, 0, 0), "31.12.2023"),
        (datetime(2024, 2, 29, 14, 30, 0), "29.02.2024"),  # Время игнорируется
    ],
)
def test_format_date(date, expected_string):
    """Тест форматирования даты с параметризацией."""
    result = format_date(date)
    assert result == expected_string


# Тесты для get_month_start с параметризацией
@pytest.mark.parametrize(
    "date, expected_start",
    [
        (datetime(2024, 3, 15, 14, 30, 0), datetime(2024, 3, 1, 0, 0, 0)),
        (datetime(2024, 1, 31, 23, 59, 59), datetime(2024, 1, 1, 0, 0, 0)),
        (datetime(2024, 12, 1, 0, 0, 0), datetime(2024, 12, 1, 0, 0, 0)),
        (datetime(2023, 2, 28, 12, 0, 0), datetime(2023, 2, 1, 0, 0, 0)),
    ],
)
def test_get_month_start(date, expected_start):
    """Тест получения начала месяца с параметризацией."""
    result = get_month_start(date)
    assert result == expected_start


# Тесты для get_month_range с параметризацией
@pytest.mark.parametrize(
    "date, expected_start, expected_end",
    [
        (
            datetime(2024, 3, 15),
            datetime(2024, 3, 1, 0, 0, 0),
            datetime(2024, 3, 31, 23, 59, 59),
        ),
        (
            datetime(2024, 1, 15),
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 1, 31, 23, 59, 59),
        ),
        (
            datetime(2024, 2, 15),
            datetime(2024, 2, 1, 0, 0, 0),
            datetime(2024, 2, 29, 23, 59, 59),  # Високосный год
        ),
        (
            datetime(2023, 2, 15),
            datetime(2023, 2, 1, 0, 0, 0),
            datetime(2023, 2, 28, 23, 59, 59),  # Не високосный год
        ),
    ],
)
def test_get_month_range(date, expected_start, expected_end):
    """Тест получения диапазона месяца с параметризацией."""
    start, end = get_month_range(date)
    assert start == expected_start
    assert end == expected_end


# Тесты для get_three_months_back с параметризацией
@pytest.mark.parametrize(
    "date, expected_start_month, expected_end_month",
    [
        (datetime(2024, 3, 15), 12, 3),  # Декабрь 2023 - Март 2024
        (datetime(2024, 1, 15), 10, 1),  # Октябрь 2023 - Январь 2024
        (datetime(2024, 6, 15), 3, 6),  # Март 2024 - Июнь 2024
        (datetime(2024, 12, 15), 9, 12),  # Сентябрь 2024 - Декабрь 2024
    ],
)
def test_get_three_months_back(date, expected_start_month, expected_end_month):
    """Тест получения диапазона последних 3 месяцев с параметризацией."""
    start, end = get_three_months_back(date)
    assert start.month == expected_start_month
    assert end.month == expected_end_month
    assert start.day == 1
    assert start.hour == 0
    assert start.minute == 0
    assert start.second == 0


# Тесты для load_user_settings
class TestLoadUserSettings:
    """Тесты для функции load_user_settings."""

    @patch("src.utils.os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user_currencies": ["USD", "EUR"]}')
    def test_load_user_settings_success(self, mock_file, mock_exists, sample_user_settings):
        """Тест успешной загрузки настроек."""
        mock_exists.return_value = True

        with patch("src.utils.json.load", return_value=sample_user_settings):
            result = load_user_settings()

        assert result == sample_user_settings

    @patch("src.utils.os.path.exists")
    def test_load_user_settings_file_not_found(self, mock_exists):
        """Тест обработки отсутствия файла."""
        mock_exists.return_value = False

        result = load_user_settings()

        assert result == {}

    @patch("src.utils.os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_load_user_settings_invalid_json(self, mock_file, mock_exists):
        """Тест обработки некорректного JSON."""
        mock_exists.return_value = True

        with patch("src.utils.json.load", side_effect=json.JSONDecodeError("", "", 0)):
            result = load_user_settings()

        assert result == {}

    @patch("src.utils.os.path.exists")
    @patch("builtins.open", side_effect=Exception("Unexpected error"))
    def test_load_user_settings_general_exception(self, mock_file, mock_exists):
        """Тест обработки общего исключения при загрузке настроек."""
        mock_exists.return_value = True

        result = load_user_settings()

        assert result == {}


# Тесты для save_json
class TestSaveJson:
    """Тесты для функции save_json."""

    @patch("builtins.open", new_callable=mock_open)
    def test_save_json_success(self, mock_file):
        """Тест успешного сохранения JSON."""
        test_data = {"key": "value", "number": 123}
        test_path = "test_output.json"

        save_json(test_data, test_path)

        mock_file.assert_called_once_with(test_path, "w", encoding="utf-8")
        # Проверяем, что json.dump был вызван
        handle = mock_file()
        assert handle.write.called

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_json_permission_error(self, mock_file):
        """Тест обработки ошибки доступа при сохранении."""
        test_data = {"key": "value"}

        with pytest.raises(OSError):
            save_json(test_data, "test_output.json")

    @patch("builtins.open", side_effect=Exception("Unexpected error"))
    def test_save_json_general_exception(self, mock_file):
        """Тест обработки общего исключения при сохранении."""
        test_data = {"key": "value"}

        with pytest.raises(Exception):
            save_json(test_data, "test_output.json")


# Тесты для get_currency_rates
class TestGetCurrencyRates:
    """Тесты для функции get_currency_rates."""

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_currency_rates_success(self, mock_get, mock_getenv):
        """Тест успешного получения курсов валют."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"USD": 73.21, "EUR": 87.08}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_currency_rates(["USD", "EUR"])

        assert len(result) == 2
        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 73.21
        assert result[1]["currency"] == "EUR"
        assert result[1]["rate"] == 87.08

    @patch("src.utils.os.getenv")
    def test_get_currency_rates_no_api_key(self, mock_getenv):
        """Тест обработки отсутствия API ключа."""
        mock_getenv.return_value = None

        result = get_currency_rates(["USD", "EUR"])

        assert result == []

    @patch("src.utils.os.getenv")
    def test_get_currency_rates_empty_list(self, mock_getenv):
        """Тест обработки пустого списка валют."""
        mock_getenv.return_value = "test_key"

        result = get_currency_rates([])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_currency_rates_api_error(self, mock_get, mock_getenv):
        """Тест обработки ошибки API."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = get_currency_rates(["USD", "EUR"])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_currency_rates_missing_currency(self, mock_get, mock_getenv):
        """Тест обработки отсутствия валюты в ответе API."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"USD": 73.21}}  # EUR отсутствует
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_currency_rates(["USD", "EUR"])

        assert len(result) == 1
        assert result[0]["currency"] == "USD"

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_currency_rates_no_rates_field(self, mock_get, mock_getenv):
        """Тест обработки отсутствия поля rates в ответе API."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "invalid"}  # Нет поля rates
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_currency_rates(["USD", "EUR"])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_currency_rates_json_decode_error(self, mock_get, mock_getenv):
        """Тест обработки ошибки парсинга JSON."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_get.return_value = mock_response

        result = get_currency_rates(["USD", "EUR"])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_currency_rates_general_exception(self, mock_get, mock_getenv):
        """Тест обработки общего исключения."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_get.side_effect = Exception("Unexpected error")

        result = get_currency_rates(["USD", "EUR"])

        assert result == []


# Тесты для get_stock_prices
class TestGetStockPrices:
    """Тесты для функции get_stock_prices."""

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_stock_prices_success_list_format(self, mock_get, mock_getenv):
        """Тест успешного получения цен акций (формат списка)."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"symbol": "AAPL", "price": 150.12},
            {"symbol": "AMZN", "price": 3173.18},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_stock_prices(["AAPL", "AMZN"])

        assert len(result) == 2
        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == 150.12
        assert result[1]["stock"] == "AMZN"
        assert result[1]["price"] == 3173.18

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_stock_prices_success_dict_format(self, mock_get, mock_getenv):
        """Тест успешного получения цен акций (формат словаря)."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.json.return_value = {"AAPL": 150.12, "AMZN": 3173.18}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_stock_prices(["AAPL", "AMZN"])

        assert len(result) == 2
        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == 150.12

    @patch("src.utils.os.getenv")
    def test_get_stock_prices_no_api_key(self, mock_getenv):
        """Тест обработки отсутствия API ключа."""
        mock_getenv.return_value = None

        result = get_stock_prices(["AAPL", "AMZN"])

        assert result == []

    @patch("src.utils.os.getenv")
    def test_get_stock_prices_empty_list(self, mock_getenv):
        """Тест обработки пустого списка акций."""
        mock_getenv.return_value = "test_key"

        result = get_stock_prices([])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_stock_prices_api_error(self, mock_get, mock_getenv):
        """Тест обработки ошибки API."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = get_stock_prices(["AAPL", "AMZN"])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_stock_prices_unexpected_format(self, mock_get, mock_getenv):
        """Тест обработки неожиданного формата ответа."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.json.return_value = "unexpected format"  # Не список и не словарь
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_stock_prices(["AAPL", "AMZN"])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_stock_prices_json_decode_error(self, mock_get, mock_getenv):
        """Тест обработки ошибки парсинга JSON."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_get.return_value = mock_response

        result = get_stock_prices(["AAPL", "AMZN"])

        assert result == []

    @patch("src.utils.os.getenv")
    @patch("src.utils.requests.get")
    def test_get_stock_prices_general_exception(self, mock_get, mock_getenv):
        """Тест обработки общего исключения."""
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_key",
            "API_URL": "https://api.test.com",
        }.get(key, default)

        mock_get.side_effect = Exception("Unexpected error")

        result = get_stock_prices(["AAPL", "AMZN"])

        assert result == []
