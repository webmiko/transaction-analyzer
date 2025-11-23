"""Тесты для модуля logger_config.py.

Используются Mock и patch для изоляции внешних зависимостей.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.logger_config import _get_log_level, setup_logger


# Тесты для _get_log_level с параметризацией
@pytest.mark.parametrize(
    "level_name, expected_level",
    [
        ("DEBUG", 10),
        ("INFO", 20),
        ("WARNING", 30),
        ("ERROR", 40),
        ("CRITICAL", 50),
        ("debug", 10),  # Проверка регистронезависимости
        ("Info", 20),
        ("unknown", 20),  # Неизвестный уровень -> INFO по умолчанию
    ],
)
def test_get_log_level(level_name: str, expected_level: int) -> None:
    """Тест преобразования уровня логирования с параметризацией."""
    result = _get_log_level(level_name)
    assert result == expected_level


# Тесты для setup_logger
class TestSetupLogger:
    """Тесты для функции setup_logger."""

    @patch("src.logger_config.logging.FileHandler")
    @patch("src.logger_config.logging.StreamHandler")
    @patch("src.logger_config.logging.Formatter")
    @patch("src.logger_config.logging.getLogger")
    def test_setup_logger_success(
        self, mock_get_logger: MagicMock, mock_formatter: MagicMock, mock_stream: MagicMock, mock_file: MagicMock
    ) -> None:
        """Тест успешной настройки логгера."""
        mock_logger = MagicMock()
        mock_logger.handlers = []  # Нет обработчиков
        mock_get_logger.return_value = mock_logger

        result = setup_logger("test_module")

        assert result == mock_logger
        mock_logger.setLevel.assert_called_once()
        assert mock_file.called
        assert mock_stream.called
        assert mock_logger.addHandler.call_count == 2  # Файл + консоль

    @patch("src.logger_config.logging.getLogger")
    def test_setup_logger_existing_handlers(self, mock_get_logger: MagicMock) -> None:
        """Тест обработки случая, когда у логгера уже есть обработчики."""
        mock_logger = MagicMock()
        mock_logger.handlers = [MagicMock()]  # Уже есть обработчик
        mock_get_logger.return_value = mock_logger

        result = setup_logger("test_module")

        assert result == mock_logger
        # Не должны добавлять новые обработчики
        mock_logger.addHandler.assert_not_called()

    @patch("src.logger_config.logging.FileHandler")
    @patch("src.logger_config.logging.StreamHandler")
    @patch("src.logger_config.logging.Formatter")
    @patch("src.logger_config.logging.getLogger")
    def test_setup_logger_file_error(
        self, mock_get_logger: MagicMock, mock_formatter: MagicMock, mock_stream: MagicMock, mock_file: MagicMock
    ) -> None:
        """Тест обработки ошибки при создании файла логов."""
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        # Имитируем ошибку при создании FileHandler
        mock_file.side_effect = OSError("Permission denied")

        result = setup_logger("test_module")

        assert result == mock_logger
        # Должен быть добавлен только один консольный обработчик (в блоке except)
        # Второй консольный обработчик не добавляется, так как file_handler_created = False
        assert mock_logger.addHandler.call_count == 1
        # Проверяем, что было вызвано предупреждение
        mock_logger.warning.assert_called_once()

    @patch("src.logger_config.logging.FileHandler")
    @patch("src.logger_config.logging.StreamHandler")
    @patch("src.logger_config.logging.Formatter")
    @patch("src.logger_config.logging.getLogger")
    def test_setup_logger_permission_error(
        self, mock_get_logger: MagicMock, mock_formatter: MagicMock, mock_stream: MagicMock, mock_file: MagicMock
    ) -> None:
        """Тест обработки ошибки доступа при создании файла логов."""
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        # Имитируем ошибку доступа
        mock_file.side_effect = PermissionError("Permission denied")

        result = setup_logger("test_module")

        assert result == mock_logger
        # Должен быть добавлен только один консольный обработчик (в блоке except)
        # Второй консольный обработчик не добавляется, так как file_handler_created = False
        assert mock_logger.addHandler.call_count == 1
        mock_logger.warning.assert_called_once()
