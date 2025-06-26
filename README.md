# Telegram-бот учёта трат

Бот для ведения общих расходов в группе через Telegram.

## Основные функции

* Добавление траты 
* Просмотр трат
* Удаление траты
* Помощь по командам 

## Структура

* **main.py** — обработка команд и запуск бота
* **DBManager.py** — работа с SQLite
* **recreate\_db.py** — создание схемы БД
* **config.py** — TELEGRAM\_TOKEN, путь к БД

## БД

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, telegram_id INTEGER UNIQUE);
CREATE TABLE spendings (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  price INTEGER,
  title TEXT,
  date TEXT
);
```

## Установка

```bash
git clone https://github.com/JimmyLaFleur/PythonProject.git
cd PythonProject
pip install -r requirements.txt
# Настройте config.py
python recreate_db.py
python main.py
```

## Лицензия

MIT
