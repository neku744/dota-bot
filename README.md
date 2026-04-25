# Dota 2 Аналізатор — Telegram Бот

Telegram бот який аналізує матчі Dota 2 через OpenDota API та Google Gemini AI.

## Що вміє бот

- Аналіз конкретного матчу по Match ID
- Порівняння GPM/XPM з середнім по герою
- Аналіз інвентарю — чи правильний білд
- Графік золота по хвилинах
- Збереження матчів в базу даних
- /profile — статистика по всіх зіграних матчах
- /hero — поради по конкретному герою
- /compare — порівняння двох матчів
- /history — список останніх матчів

## Встановлення

### 1. Клонуй або скачай файли в папку dota_bot

### 2. Встанови залежності
pip install -r requirements.txt

### 3. Створи .env файл
Скопіюй .env.example і перейменуй в .env:
- TELEGRAM_TOKEN — від @BotFather в Telegram
- GEMINI_API_KEY — з aistudio.google.com

### 4. Запусти бота
python bot.py

## Деплой на Railway (безкоштовно 24/7)

1. Зареєструйся на railway.app через GitHub
2. New Project -> Deploy from GitHub repo
3. Завантаж всі файли в GitHub репозиторій
4. В Railway: Variables -> додай TELEGRAM_TOKEN і GEMINI_API_KEY
5. Бот запуститься автоматично

## Файлова структура

- bot.py — головний файл, всі команди і handlers
- opendota.py — запити до OpenDota API
- analyzer.py — аналіз через Gemini AI
- database.py — збереження матчів в SQLite
- requirements.txt — залежності
- .env — токени (не завантажувати на GitHub!)
- .env.example — приклад .env файлу
- Procfile — для деплою на Railway
