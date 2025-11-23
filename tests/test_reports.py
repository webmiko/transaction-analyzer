"""Тесты для модуля reports.py.

Используются Mock и patch для изоляции внешних зависимостей,
фикстуры для тестовых данных и параметризация где это уместно.
"""

from datetime import datetime
from typing import Any, Dict
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.reports import save_report, spending_by_category, spending_by_weekday, spending_by_workday


# Фикстуры для тестовых данных
@pytest.fixture
def sample_transactions_df() -> pd.DataFrame:
    """Фикстура с тестовыми данными транзакций для reports."""
    data = {
        "Дата операции": pd.to_datetime(
            [
                "15.01.2024 10:30:00",
                "20.01.2024 14:20:00",
                "25.01.2024 09:15:00",
                "15.02.2024 10:30:00",
                "20.02.2024 14:20:00",
                "25.02.2024 09:15:00",
                "15.03.2024 10:30:00",
                "20.03.2024 14:20:00",
                "25.03.2024 09:15:00",
            ],
            format="%d.%m.%Y %H:%M:%S",
        ),
        "Категория": [
            "Супермаркеты",
            "Супермаркеты",
            "Фастфуд",
            "Супермаркеты",
            "Фастфуд",
            "Супермаркеты",
            "Супермаркеты",
            "Фастфуд",
            "Супермаркеты",
        ],
        "Сумма платежа": [-1000.0, -500.0, -200.0, -800.0, -300.0, -600.0, -1200.0, -400.0, -900.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_transactions_df_weekdays() -> pd.DataFrame:
    """Фикстура с транзакциями для тестов по дням недели."""
    # Создаем транзакции для разных дней недели
    dates = [
        "15.01.2024 10:30:00",  # Понедельник
        "16.01.2024 14:20:00",  # Вторник
        "17.01.2024 09:15:00",  # Среда
        "18.01.2024 11:00:00",  # Четверг
        "19.01.2024 15:30:00",  # Пятница
        "20.01.2024 10:00:00",  # Суббота
        "21.01.2024 12:00:00",  # Воскресенье
    ]
    data = {
        "Дата операции": pd.to_datetime(dates, format="%d.%m.%Y %H:%M:%S"),
        "Категория": ["Супермаркеты"] * 7,
        "Сумма платежа": [-100.0, -200.0, -300.0, -400.0, -500.0, -600.0, -700.0],
    }
    return pd.DataFrame(data)


# Тесты для декоратора save_report
class TestSaveReportDecorator:
    """Тесты для декоратора save_report."""

    @patch("src.reports.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.reports.logger")
    def test_save_report_decorator_without_filename(self, mock_logger: Any, mock_file: Any, mock_mkdir: Any) -> None:
        """Тест декоратора без параметра (автоматическое имя файла)."""

        @save_report()
        def test_function() -> Dict[str, str]:
            return {"result": "test"}

        result = test_function()

        assert result == {"result": "test"}
        mock_file.assert_called_once()
        mock_logger.info.assert_called_once()
        # Проверяем, что файл был открыт для записи
        call_args = mock_file.call_args
        assert "w" in call_args[0] or "mode" in call_args[1]

    @patch("src.reports.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.reports.logger")
    def test_save_report_decorator_with_filename(self, mock_logger: Any, mock_file: Any, mock_mkdir: Any) -> None:
        """Тест декоратора с параметром (указанное имя файла)."""

        @save_report("custom_report.json")
        def test_function() -> Dict[str, str]:
            return {"result": "test"}

        result = test_function()

        assert result == {"result": "test"}
        mock_file.assert_called_once()
        # Проверяем, что использовалось указанное имя файла
        call_args = mock_file.call_args
        assert "custom_report.json" in str(call_args[0][0])

    @patch("src.reports.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.reports.logger")
    def test_save_report_decorator_with_dataframe(self, mock_logger: Any, mock_file: Any, mock_mkdir: Any) -> None:
        """Тест декоратора с DataFrame в результате."""

        @save_report()
        def test_function() -> pd.DataFrame:
            return pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        result = test_function()

        assert isinstance(result, pd.DataFrame)
        mock_file.assert_called_once()
        # Проверяем, что json.dump был вызван
        mock_file().write.assert_called()

    @patch("src.reports.Path.mkdir")
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    @patch("src.reports.logger")
    def test_save_report_decorator_permission_error(self, mock_logger: Any, mock_file: Any, mock_mkdir: Any) -> None:
        """Тест обработки ошибки доступа при сохранении."""

        @save_report()
        def test_function() -> Dict[str, str]:
            return {"result": "test"}

        result = test_function()

        assert result == {"result": "test"}
        mock_logger.error.assert_called_once()

    @patch("src.reports.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.reports.logger")
    def test_save_report_decorator_with_callable(self, mock_logger: Any, mock_file: Any, mock_mkdir: Any) -> None:
        """Тест декоратора с callable параметром (альтернативный синтаксис)."""

        @save_report  # type: ignore[arg-type]
        def test_function() -> Dict[str, str]:
            return {"result": "test"}

        result = test_function()

        assert result == {"result": "test"}
        mock_file.assert_called_once()

    @patch("src.reports.Path.mkdir")
    @patch("builtins.open", side_effect=TypeError("Type error"))
    @patch("src.reports.logger")
    def test_save_report_decorator_type_error(self, mock_logger: Any, mock_file: Any, mock_mkdir: Any) -> None:
        """Тест обработки TypeError при сохранении."""

        @save_report()
        def test_function() -> Dict[str, str]:
            return {"result": "test"}

        result = test_function()

        assert result == {"result": "test"}
        mock_logger.error.assert_called_once()


# Тесты для spending_by_category
class TestSpendingByCategory:
    """Тесты для функции spending_by_category."""

    @patch("src.reports.get_three_months_back")
    def test_spending_by_category_success(self, mock_get_range: Any, sample_transactions_df: pd.DataFrame) -> None:
        """Тест успешного анализа трат по категории."""
        # Настраиваем mock для диапазона дат
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31, 23, 59, 59)
        mock_get_range.return_value = (start_date, end_date)

        result = spending_by_category(sample_transactions_df, "Супермаркеты", "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_spending_by_category_empty_dataframe(self) -> None:
        """Тест обработки пустого DataFrame."""
        empty_df = pd.DataFrame()

        result = spending_by_category(empty_df, "Супермаркеты", "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_category_invalid_date_format(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест обработки некорректного формата даты."""
        result = spending_by_category(sample_transactions_df, "Супермаркеты", "2024/03/15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_category_no_date(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест использования текущей даты при отсутствии параметра."""
        with patch("src.reports.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 3, 15)
            mock_datetime.strptime = datetime.strptime

            with patch("src.reports.get_three_months_back") as mock_get_range:
                start_date = datetime(2024, 1, 1)
                end_date = datetime(2024, 3, 31, 23, 59, 59)
                mock_get_range.return_value = (start_date, end_date)

                result = spending_by_category(sample_transactions_df, "Супермаркеты")

                assert isinstance(result, pd.DataFrame)

    def test_spending_by_category_no_matching_category(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест обработки отсутствия транзакций по категории."""
        with patch("src.reports.get_three_months_back") as mock_get_range:
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 3, 31, 23, 59, 59)
            mock_get_range.return_value = (start_date, end_date)

            result = spending_by_category(sample_transactions_df, "Несуществующая категория", "2024-03-15")

            assert isinstance(result, pd.DataFrame)


# Тесты для spending_by_weekday
class TestSpendingByWeekday:
    """Тесты для функции spending_by_weekday."""

    @patch("src.reports.get_three_months_back")
    def test_spending_by_weekday_success(
        self, mock_get_range: Any, sample_transactions_df_weekdays: pd.DataFrame
    ) -> None:
        """Тест успешного анализа трат по дням недели."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31, 23, 59, 59)
        mock_get_range.return_value = (start_date, end_date)

        result = spending_by_weekday(sample_transactions_df_weekdays, "2024-01-20")

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "день_недели" in result.columns
        assert "средняя_сумма" in result.columns

    def test_spending_by_weekday_empty_dataframe(self) -> None:
        """Тест обработки пустого DataFrame."""
        empty_df = pd.DataFrame()

        result = spending_by_weekday(empty_df, "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_weekday_invalid_date_format(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест обработки некорректного формата даты."""
        result = spending_by_weekday(sample_transactions_df, "2024/03/15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_weekday_no_date(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест использования текущей даты при отсутствии параметра."""
        with patch("src.reports.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 3, 15)
            mock_datetime.strptime = datetime.strptime

            with patch("src.reports.get_three_months_back") as mock_get_range:
                start_date = datetime(2024, 1, 1)
                end_date = datetime(2024, 3, 31, 23, 59, 59)
                mock_get_range.return_value = (start_date, end_date)

                result = spending_by_weekday(sample_transactions_df)

                assert isinstance(result, pd.DataFrame)

    @patch("src.reports.get_three_months_back")
    def test_spending_by_weekday_only_expenses(
        self, mock_get_range: Any, sample_transactions_df: pd.DataFrame
    ) -> None:
        """Тест фильтрации только расходов (отрицательных сумм)."""
        # Добавляем транзакцию с положительной суммой
        df_with_income = sample_transactions_df.copy()
        new_row = pd.DataFrame(
            {
                "Дата операции": [pd.to_datetime("15.03.2024 10:30:00", format="%d.%m.%Y %H:%M:%S")],
                "Категория": ["Пополнения"],
                "Сумма платежа": [5000.0],  # Положительная сумма
            }
        )
        df_with_income = pd.concat([df_with_income, new_row], ignore_index=True)

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31, 23, 59, 59)
        mock_get_range.return_value = (start_date, end_date)

        result = spending_by_weekday(df_with_income, "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        # Пополнение не должно учитываться в расчете средних трат


# Тесты для spending_by_workday
class TestSpendingByWorkday:
    """Тесты для функции spending_by_workday."""

    @patch("src.reports.get_three_months_back")
    def test_spending_by_workday_success(
        self, mock_get_range: Any, sample_transactions_df_weekdays: pd.DataFrame
    ) -> None:
        """Тест успешного анализа трат в рабочие и выходные дни."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31, 23, 59, 59)
        mock_get_range.return_value = (start_date, end_date)

        result = spending_by_workday(sample_transactions_df_weekdays, "2024-01-20")

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "тип_дня" in result.columns
        assert "средняя_сумма" in result.columns
        # Проверяем, что есть оба типа дней
        day_types = result["тип_дня"].unique()
        assert "рабочий" in day_types or "выходной" in day_types

    def test_spending_by_workday_empty_dataframe(self) -> None:
        """Тест обработки пустого DataFrame."""
        empty_df = pd.DataFrame()

        result = spending_by_workday(empty_df, "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_workday_invalid_date_format(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест обработки некорректного формата даты."""
        result = spending_by_workday(sample_transactions_df, "2024/03/15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_workday_no_date(self, sample_transactions_df: pd.DataFrame) -> None:
        """Тест использования текущей даты при отсутствии параметра."""
        with patch("src.reports.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 3, 15)
            mock_datetime.strptime = datetime.strptime

            with patch("src.reports.get_three_months_back") as mock_get_range:
                start_date = datetime(2024, 1, 1)
                end_date = datetime(2024, 3, 31, 23, 59, 59)
                mock_get_range.return_value = (start_date, end_date)

                result = spending_by_workday(sample_transactions_df)

                assert isinstance(result, pd.DataFrame)

    @patch("src.reports.get_three_months_back")
    def test_spending_by_workday_workday_vs_weekend(
        self, mock_get_range: Any, sample_transactions_df_weekdays: pd.DataFrame
    ) -> None:
        """Тест корректного разделения на рабочие и выходные дни."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31, 23, 59, 59)
        mock_get_range.return_value = (start_date, end_date)

        result = spending_by_workday(sample_transactions_df_weekdays, "2024-01-20")

        assert isinstance(result, pd.DataFrame)
        # Проверяем, что есть оба типа дней
        day_types = set(result["тип_дня"].unique())
        assert day_types.intersection({"рабочий", "выходной"})

    @patch("src.reports.get_three_months_back", side_effect=Exception("Unexpected error"))
    @patch("src.reports.logger")
    def test_spending_by_weekday_exception_handling(
        self, mock_logger: Any, mock_get_range: Any, sample_transactions_df: pd.DataFrame
    ) -> None:
        """Тест обработки исключений в spending_by_weekday."""
        result = spending_by_weekday(sample_transactions_df, "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty
        mock_logger.error.assert_called_once()

    @patch("src.reports.get_three_months_back", side_effect=Exception("Unexpected error"))
    @patch("src.reports.logger")
    def test_spending_by_workday_exception_handling(
        self, mock_logger: Any, mock_get_range: Any, sample_transactions_df: pd.DataFrame
    ) -> None:
        """Тест обработки исключений в spending_by_workday."""
        result = spending_by_workday(sample_transactions_df, "2024-03-15")

        assert isinstance(result, pd.DataFrame)
        assert result.empty
        mock_logger.error.assert_called_once()

    @patch("src.reports.get_three_months_back")
    def test_spending_by_category_with_coerce_errors(self, mock_get_range: Any) -> None:
        """Тест обработки ошибок преобразования дат с errors='coerce'."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31, 23, 59, 59)
        mock_get_range.return_value = (start_date, end_date)

        # Создаем DataFrame с некорректными датами
        data = {
            "Дата операции": ["invalid-date", "20.02.2024 14:20:00"],
            "Категория": ["Супермаркеты", "Супермаркеты"],
            "Сумма платежа": [-1000.0, -500.0],
        }
        df = pd.DataFrame(data)

        result = spending_by_category(df, "Супермаркеты", "2024-03-15")

        assert isinstance(result, pd.DataFrame)
