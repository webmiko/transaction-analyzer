"""Модуль для настройки логирования в приложении.

Этот модуль предоставляет функцию для настройки логгеров с учетом
переменных окружения и требований безопасности.
"""

import logging
import os

# Константы для логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _get_log_level(level_name: str) -> int:
    """
    Преобразует строковое название уровня логирования в числовое значение.

    Args:
        level_name: Название уровня (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Числовое значение уровня логирования
    """
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_mapping.get(level_name.upper(), logging.INFO)


def setup_logger(name: str) -> logging.Logger:
    """
    Настраивает и возвращает логгер для модуля.

    Логгер настраивается с учетом переменных окружения:
    - LOG_LEVEL: уровень логирования (по умолчанию INFO)
    - LOG_FILE: путь к файлу логов (по умолчанию app.log)

    Логгер выводит сообщения в файл и в консоль.

    Args:
        name: Имя логгера (обычно имя модуля, например __name__)

    Returns:
        Настроенный логгер

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Модуль загружен")
    """
    logger = logging.getLogger(name)
    logger.setLevel(_get_log_level(LOG_LEVEL))

    # Предотвращаем дублирование обработчиков
    if logger.handlers:
        return logger

    # Форматтер для сообщений
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Обработчик для файла
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(_get_log_level(LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # Если не удалось создать файл, логируем только в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(_get_log_level(LOG_LEVEL))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.warning(f"Не удалось создать файл логов: {e}. Логирование только в консоль.")

    # Обработчик для консоли (только WARNING и выше)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
