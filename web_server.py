"""Простой веб-сервер для демонстрации работы проекта.

Запускает Flask сервер для отображения данных транзакций в браузере.
"""

import logging
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template, request

from src.utils import load_transactions_from_excel
from src.views import _get_greeting, events_page, home_page

# Константы модуля
DEFAULT_EXCEL_FILE = "data/operations.xlsx"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_DATE = "2024-03-15"
DEFAULT_PERIOD = "M"
DEFAULT_PORT = 5001  # Используем 5001 вместо 5000 (5000 часто занят AirPlay на macOS)

# Создаем Flask приложение
app = Flask(__name__, template_folder="templates")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.after_request
def after_request(response: Any) -> Any:
    """Добавляет заголовки CORS для всех ответов."""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response


def _load_data() -> Any:
    """
    Загружает данные транзакций из Excel файла.

    Returns:
        DataFrame с транзакциями или None при ошибке
    """
    try:
        df = load_transactions_from_excel(DEFAULT_EXCEL_FILE)
        logger.info(f"Загружено транзакций: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {type(e).__name__} - {e}")
        return None


def _get_max_date_from_data(df: Any) -> str:
    """
    Получает максимальную дату из данных транзакций.

    Используется для отображения данных, так как файл может содержать
    исторические данные, а не текущие.

    Args:
        df: DataFrame с транзакциями

    Returns:
        Строка с датой и временем в формате YYYY-MM-DD HH:MM:SS
    """
    if df is None or df.empty:
        # Если данных нет, используем текущее время
        return datetime.now().strftime(DATE_TIME_FORMAT)

    try:
        # Получаем максимальную дату операции
        max_date = df["Дата операции"].max()

        # Если это pandas Timestamp, преобразуем в datetime
        if hasattr(max_date, 'to_pydatetime'):
            max_datetime = max_date.to_pydatetime()
        elif isinstance(max_date, datetime):
            max_datetime = max_date
        else:
            # Если это строка или другой тип, используем текущее время
            logger.warning(f"Неожиданный тип даты: {type(max_date)}")
            return datetime.now().strftime(DATE_TIME_FORMAT)

        # Устанавливаем время на конец дня для включения всех транзакций
        max_datetime = max_datetime.replace(hour=23, minute=59, second=59)
        result: str = max_datetime.strftime(DATE_TIME_FORMAT)
        return result
    except Exception as e:
        error_msg = (
            f"Ошибка при получении максимальной даты: {type(e).__name__} - {e}. "
            "Используется текущее время."
        )
        logger.warning(error_msg)
        return datetime.now().strftime(DATE_TIME_FORMAT)


@app.route("/")
def index() -> Any:
    """Главная страница с HTML интерфейсом."""
    return render_template("index.html")


@app.route("/api/home")
def api_home() -> Any:
    """API endpoint для данных главной страницы."""
    try:
        df = _load_data()
        if df is None or df.empty:
            error_msg = "Не удалось загрузить данные или файл пуст"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

        # Используем максимальную дату из данных для отображения всех доступных транзакций
        # Приветствие будет основано на текущем времени
        max_date = _get_max_date_from_data(df)
        logger.info(f"Используется дата для фильтрации: {max_date}")

        # Для приветствия используем текущее время
        current_hour = datetime.now().hour

        logger.info("Генерация данных для главной страницы...")
        data = home_page(max_date, df)

        # Обновляем приветствие на основе текущего времени
        data["greeting"] = _get_greeting(current_hour)

        logger.info("Данные для главной страницы успешно сгенерированы")
        return jsonify(data)
    except Exception as e:
        error_msg = f"Ошибка генерации данных главной страницы: {type(e).__name__} - {e}"
        logger.error(error_msg)
        return jsonify({"error": str(e)}), 500


@app.route("/api/events")
@app.route("/api/events/<period>")
def api_events(period: str = DEFAULT_PERIOD) -> Any:
    """API endpoint для данных страницы событий."""
    try:
        df = _load_data()
        if df is None or df.empty:
            error_msg = "Не удалось загрузить данные или файл пуст"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

        # Проверяем наличие параметров кастомного диапазона дат и фильтра по карте
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        card_filter = request.args.get("card")

        if start_date and end_date:
            # Используем кастомный диапазон дат
            logger.info(f"Используется кастомный диапазон дат: {start_date} - {end_date}")
            if card_filter:
                logger.info(f"Применяется фильтр по карте: ****{card_filter}")
            data = events_page("", "CUSTOM", df, start_date=start_date, end_date=end_date, card_filter=card_filter)
        else:
            # Используем стандартный период
            max_date_str = _get_max_date_from_data(df)
            # Извлекаем только дату (без времени) для events_page
            max_date_only = max_date_str.split()[0]
            logger.info(f"Используется дата для фильтрации: {max_date_only} (период: {period})")
            if card_filter:
                logger.info(f"Применяется фильтр по карте: ****{card_filter}")
            data = events_page(max_date_only, period, df, card_filter=card_filter)

        logger.info("Данные для страницы событий успешно сгенерированы")
        return jsonify(data)
    except Exception as e:
        error_msg = f"Ошибка генерации данных страницы событий: {type(e).__name__} - {e}"
        logger.error(error_msg)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = DEFAULT_PORT
    logger.info(f"Запуск веб-сервера на http://localhost:{port}")
    logger.info(f"Откройте браузер и перейдите по адресу: http://localhost:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
