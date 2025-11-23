"""Модуль для настройки логирования в приложении.

Этот модуль предоставляет функцию для настройки логгеров с учетом
переменных окружения и требований безопасности.
"""

import logging
import os
from pathlib import Path

# Константы модуля
DEFAULT_LOG_LEVEL = "INFO"
ENCODING = "utf-8"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
CONSOLE_LOG_LEVEL: int = logging.WARNING
FILE_WRITE_MODE = "w"


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

    Каждый модуль пишет логи в отдельный файл с именем модуля в папке logs/.
    Например: src.utils → logs/utils.log, src.views → logs/views.log

    Логгер настраивается с учетом переменных окружения:
    - LOG_LEVEL: уровень логирования (по умолчанию INFO)

    Логгер выводит сообщения в файл и в консоль.

    Args:
        name: Имя логгера (обычно имя модуля, например __name__)

    Returns:
        Настроенный логгер

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Модуль загружен")
    """
    log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)

    logger = logging.getLogger(name)
    logger.setLevel(_get_log_level(log_level))

    # Предотвращаем дублирование обработчиков
    if logger.handlers:
        return logger

    # Форматтер для сообщений
    formatter = logging.Formatter(LOG_FORMAT, datefmt=TIMESTAMP_FORMAT)

    # Обработчик для файла
    file_handler_created = False
    try:
        # Каждый модуль пишет логи в отдельный файл с именем модуля
        # Извлекаем имя модуля из полного пути (например, "src.utils" -> "utils")
        module_name = name.split(".")[-1] if "." in name else name
        log_file = f"{module_name}.log"

        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_path = logs_dir / log_file

        file_handler = logging.FileHandler(log_path, mode=FILE_WRITE_MODE, encoding=ENCODING)
        file_handler.setLevel(_get_log_level(log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        file_handler_created = True
    except (OSError, PermissionError) as e:
        # Если не удалось создать файл, логируем только в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(_get_log_level(log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.warning(f"Не удалось создать файл логов: {type(e).__name__} - {e}. Логирование только в консоль.")

    # Обработчик для консоли (только WARNING и выше)
    # Добавляем только если файловый обработчик был успешно создан
    # Если файловый обработчик не создан, консольный уже добавлен выше
    if file_handler_created:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(CONSOLE_LOG_LEVEL)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
