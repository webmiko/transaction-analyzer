# API Reference

Полный справочник по API и функциям проекта Transaction Analyzer.

## 📡 REST API

### GET /api/home

Возвращает данные для главной страницы.

**Endpoint:** `/api/home`

**Метод:** `GET`

**Параметры:** Нет

**Ответ:**
```json
{
  "greeting": "Добрый день",
  "cards": [
    {
      "last_digits": "7197",
      "total_spent": 24576.63,
      "cashback": 245.77
    }
  ],
  "top_transactions": [
    {
      "date": "30.12.2021",
      "amount": 174000.00,
      "category": "Пополнения",
      "description": "Пополнение через Газпромбанк"
    }
  ],
  "currency_rates": [
    {
      "currency": "USD",
      "rate": 79.37
    },
    {
      "currency": "EUR",
      "rate": 87.08
    }
  ],
  "stock_prices": [
    {
      "stock": "AAPL",
      "price": 150.12
    }
  ]
}
```

**Описание полей:**
- `greeting` (str): Приветствие по времени суток
- `cards` (array): Список карт с расходами и кешбэком
- `top_transactions` (array): Топ-5 транзакций по сумме
- `currency_rates` (array): Курсы валют
- `stock_prices` (array): Цены акций

### GET /api/events

Возвращает данные для страницы событий.

**Endpoint:** `/api/events` или `/api/events/<period>`

**Метод:** `GET`

**Параметры запроса:**
- `period` (str, optional): Период данных
  - `W` - Неделя (последние 7 дней)
  - `M` - Месяц (с начала месяца) - по умолчанию
  - `Y` - Год (с начала года)
  - `ALL` - Все данные
  - `CUSTOM` - Кастомный диапазон
- `start_date` (str, optional): Начальная дата для CUSTOM (формат: `YYYY-MM-DD`)
- `end_date` (str, optional): Конечная дата для CUSTOM (формат: `YYYY-MM-DD`)
- `card` (str, optional): Последние 4 цифры карты для фильтрации

**Примеры запросов:**
```http
GET /api/events?period=M
GET /api/events?period=CUSTOM&start_date=2024-01-01&end_date=2024-03-31
GET /api/events?period=M&card=7197
GET /api/events?period=CUSTOM&start_date=2024-01-01&end_date=2024-03-31&card=7197
```

**Ответ:**
```json
{
  "expenses": {
    "total_amount": 12345,
    "main": [
      {
        "category": "Супермаркеты",
        "amount": 5000
      },
      {
        "category": "Транспорт",
        "amount": 3000
      }
    ],
    "transfers_and_cash": [
      {
        "category": "Переводы",
        "amount": 2000
      },
      {
        "category": "Наличные",
        "amount": 1000
      }
    ]
  },
  "income": {
    "total_amount": 50000,
    "main": [
      {
        "category": "Пополнения",
        "amount": 50000
      }
    ]
  },
  "currency_rates": [...],
  "stock_prices": [...]
}
```

**Описание полей:**
- `expenses.total_amount` (int): Общая сумма расходов
- `expenses.main` (array): Основные категории расходов (топ-7)
- `expenses.transfers_and_cash` (array): Переводы и наличные отдельно
- `income.total_amount` (int): Общая сумма поступлений
- `income.main` (array): Категории поступлений
- `currency_rates` (array): Курсы валют
- `stock_prices` (array): Цены акций

## 🐍 Python API

### Модуль views.py

#### home_page()

Генерирует JSON-данные для главной страницы.

```python
def home_page(
    date_time: str,
    transactions: pd.DataFrame
) -> Dict[str, Any]
```

**Параметры:**
- `date_time` (str): Дата и время в формате `YYYY-MM-DD HH:MM:SS`
- `transactions` (pd.DataFrame): DataFrame с транзакциями

**Возвращает:**
- `Dict[str, Any]`: Словарь с данными для главной страницы

**Пример:**
```python
from src.views import home_page
from src.utils import load_transactions_from_excel

df = load_transactions_from_excel("data/operations.xlsx")
data = home_page("2024-03-15 14:30:00", df)
```

#### events_page()

Генерирует JSON-данные для страницы событий.

```python
def events_page(
    date: str,
    period: str,
    transactions: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    card_filter: Optional[str] = None
) -> Dict[str, Any]
```

**Параметры:**
- `date` (str): Дата в формате `YYYY-MM-DD` (для стандартных периодов)
- `period` (str): Период данных (W, M, Y, ALL, CUSTOM)
- `transactions` (pd.DataFrame): DataFrame с транзакциями
- `start_date` (str, optional): Начальная дата для CUSTOM
- `end_date` (str, optional): Конечная дата для CUSTOM
- `card_filter` (str, optional): Последние 4 цифры карты

**Возвращает:**
- `Dict[str, Any]`: Словарь с данными для страницы событий

**Пример:**
```python
from src.views import events_page

# Стандартный период
data = events_page("2024-03-15", "M", df)

# Кастомный диапазон
data = events_page("", "CUSTOM", df, start_date="2024-01-01", end_date="2024-03-31")

# С фильтром по карте
data = events_page("2024-03-15", "M", df, card_filter="7197")
```

### Модуль services.py

#### profitable_cashback_categories()

Находит категории с наибольшим кешбэком.

```python
def profitable_cashback_categories(
    data: List[Dict[str, Any]],
    year: int,
    month: int
) -> Dict[str, float]
```

**Параметры:**
- `data` (List[Dict]): Список транзакций
- `year` (int): Год для анализа
- `month` (int): Месяц для анализа (1-12)

**Возвращает:**
- `Dict[str, float]`: Словарь {категория: сумма_кешбэка}

#### investment_bank()

Рассчитывает сумму округлений для инвесткопилки.

```python
def investment_bank(
    month: str,
    transactions: List[Dict[str, Any]],
    limit: int
) -> float
```

**Параметры:**
- `month` (str): Месяц в формате `YYYY-MM`
- `transactions` (List[Dict]): Список транзакций
- `limit` (int): Лимит округления

**Возвращает:**
- `float`: Сумма округлений

#### simple_search()

Поиск транзакций по запросу.

```python
def simple_search(
    query: str,
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]
```

**Параметры:**
- `query` (str): Поисковый запрос
- `transactions` (List[Dict]): Список транзакций

**Возвращает:**
- `Dict[str, Any]`: `{"query": str, "transactions": List[Dict]}`

#### search_by_phone()

Поиск транзакций с телефонными номерами.

```python
def search_by_phone(
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]
```

**Параметры:**
- `transactions` (List[Dict]): Список транзакций

**Возвращает:**
- `Dict[str, Any]`: `{"transactions": List[Dict]}`

#### search_person_transfers()

Поиск переводов физическим лицам.

```python
def search_person_transfers(
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]
```

**Параметры:**
- `transactions` (List[Dict]): Список транзакций

**Возвращает:**
- `Dict[str, Any]`: `{"transactions": List[Dict]}`

### Модуль reports.py

#### spending_by_category()

Анализирует траты по категории за последние 3 месяца.

```python
@save_report()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> pd.DataFrame
```

**Параметры:**
- `transactions` (pd.DataFrame): DataFrame с транзакциями
- `category` (str): Категория для анализа
- `date` (str, optional): Дата отсчета (по умолчанию текущая)

**Возвращает:**
- `pd.DataFrame`: DataFrame с тратами по месяцам

**Примечание:** Отчет автоматически сохраняется в `reports/`

#### spending_by_weekday()

Анализирует средние траты по дням недели.

```python
@save_report()
def spending_by_weekday(
    transactions: pd.DataFrame,
    date: Optional[str] = None
) -> pd.DataFrame
```

**Параметры:**
- `transactions` (pd.DataFrame): DataFrame с транзакциями
- `date` (str, optional): Дата отсчета

**Возвращает:**
- `pd.DataFrame`: DataFrame со средними тратами по дням недели

#### spending_by_workday()

Анализирует средние траты в рабочие и выходные дни.

```python
@save_report()
def spending_by_workday(
    transactions: pd.DataFrame,
    date: Optional[str] = None
) -> pd.DataFrame
```

**Параметры:**
- `transactions` (pd.DataFrame): DataFrame с транзакциями
- `date` (str, optional): Дата отсчета

**Возвращает:**
- `pd.DataFrame`: DataFrame со средними тратами по типам дней

### Модуль utils.py

#### load_transactions_from_excel()

Загружает транзакции из Excel файла.

```python
def load_transactions_from_excel(
    file_path: str
) -> pd.DataFrame
```

**Параметры:**
- `file_path` (str): Путь к Excel файлу

**Возвращает:**
- `pd.DataFrame`: DataFrame с транзакциями

#### get_currency_rates()

Получает курсы валют через API.

```python
def get_currency_rates(
    currencies: List[str]
) -> List[Dict[str, Any]]
```

**Параметры:**
- `currencies` (List[str]): Список кодов валют

**Возвращает:**
- `List[Dict[str, Any]]`: Список словарей `[{"currency": str, "rate": float}]`

#### get_stock_prices()

Получает цены акций через API.

```python
def get_stock_prices(
    stocks: List[str]
) -> List[Dict[str, Any]]
```

**Параметры:**
- `stocks` (List[str]): Список тикеров акций

**Возвращает:**
- `List[Dict[str, Any]]`: Список словарей `[{"stock": str, "price": float}]`

## 📚 Дополнительная информация

- [Использование](Usage) - Примеры использования API
- [Веб-интерфейс](Web-Interface) - Использование REST API
- [Решение проблем](Troubleshooting) - Решение проблем с API

---

**Следующий шаг:** [Решение проблем](Troubleshooting)


