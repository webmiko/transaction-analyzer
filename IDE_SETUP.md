# Настройка IDE для работы с Poetry

Этот документ содержит инструкции по настройке различных IDE для работы с проектом, использующим Poetry.

## Получение пути к виртуальному окружению

Сначала получите путь к виртуальному окружению Poetry:

```bash
poetry env info --path
```

Текущий путь:
```
/Users/guoliang/Library/Caches/pypoetry/virtualenvs/transaction-analyzer-7RabYJx--py3.13
```

Python интерпретатор:
```
/Users/guoliang/Library/Caches/pypoetry/virtualenvs/transaction-analyzer-7RabYJx--py3.13/bin/python
```

---

## VS Code

### Автоматическая настройка

Файл `.vscode/settings.json` уже настроен. Просто перезагрузите VS Code.

### Ручная настройка

1. Откройте VS Code
2. Нажмите `Cmd+Shift+P` (macOS) или `Ctrl+Shift+P` (Windows/Linux)
3. Введите "Python: Select Interpreter"
4. Выберите интерпретатор из виртуального окружения Poetry

Или выберите "Enter interpreter path..." и введите:
```
/Users/guoliang/Library/Caches/pypoetry/virtualenvs/transaction-analyzer-7RabYJx--py3.13/bin/python
```

### Проверка

После настройки предупреждение "Невозможно разрешить импорт pytest" должно исчезнуть.

---

## PyCharm

1. Откройте PyCharm
2. Перейдите в `PyCharm` → `Settings` (или `Preferences` на macOS)
3. Выберите `Project: course_work_1` → `Python Interpreter`
4. Нажмите на шестеренку ⚙️ → `Add...`
5. Выберите `Existing environment`
6. В поле `Interpreter` введите путь:
   ```
   /Users/guoliang/Library/Caches/pypoetry/virtualenvs/transaction-analyzer-7RabYJx--py3.13/bin/python
   ```
7. Нажмите `OK`

---

## Cursor (VS Code fork)

Настройка аналогична VS Code. Файл `.vscode/settings.json` будет использован автоматически.

---

## Обновление пути (если виртуальное окружение пересоздано)

Если вы пересоздали виртуальное окружение Poetry, обновите путь:

```bash
# Получите новый путь
poetry env info --path

# Обновите .vscode/settings.json с новым путем
```

---

## Проверка работы

После настройки IDE:

1. Откройте файл `tests/test_logger_config.py`
2. Убедитесь, что предупреждение об импорте `pytest` исчезло
3. Запустите тесты через IDE или терминал:
   ```bash
   poetry run pytest tests/test_logger_config.py -v
   ```

---

## Дополнительные настройки

### VS Code расширения (рекомендуемые)

- Python (Microsoft)
- Pylance (Microsoft)
- Black Formatter
- Flake8
- MyPy Type Checker

### PyCharm плагины

- Python (встроен)
- Poetry (для управления зависимостями)



