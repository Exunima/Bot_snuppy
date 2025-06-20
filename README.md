# Discord Music Bot - Snuppy

**Snuppy** — это Discord-бот, который позволяет воспроизводить музыку из Яндекс Музыки прямо в голосовом канале Discord. С помощью этого бота можно легко управлять очередью воспроизведения, приостанавливать, возобновлять и пропускать треки.

---

## 🚀 Возможности

- Воспроизведение треков по ссылке с Яндекс Музыки
- Управление очередью воспроизведения
- Приостановка / возобновление / пропуск трека
- Полная остановка и очистка очереди

---

## Команды бота

Вот список доступных команд для управления ботом:

- `!play <URL>` — Воспроизведение трека из Яндекс Музыки по переданному URL.
- `!pause` — Приостановить воспроизведение текущего трека.
- `!resume` — Возобновить воспроизведение текущего трека.
- `!stop` — Остановить воспроизведение, очистить очередь и отключить бота от голосового канала.
- `!skip` — Пропустить текущий трек и начать воспроизведение следующего в очереди.
- `!queue` — Показать текущую очередь воспроизведения.

---

## Требования

- Python 3.11+
- Установленные библиотеки:
  - `discord.py`
  - `yandex-music`
  - `aiohttp`
  - `python-dotenv`
- Установленный [FFmpeg](https://ffmpeg.org/download.html) (должен быть доступен через PATH)

---

## 📥 Установка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Exunima/Bot_snuppy.git
cd Bot_snuppy
```

### 2. Создайте и активируйте виртуальное окружение

```bash
python -m venv .venv
```
#### Для Windows:

```bash
.venv\Scripts\activate
```
#### Для Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

```env
YANDEX_MUSIC_TOKEN=ваш_токен_от_Яндек_музыки
DISCORD_BOT_TOKEN=ваш_токен_бота
FFMPEG_PATH=ваш_путь_к_ffmpeg
```

---

## ▶️ Запуск бота

```bash
python bot.py
```

---

## 📁 Структура проекта

```bash
Bot_snuppy/
│
├── music/                # Модуль с логикой загрузки и воспроизведения
│   ├── __init__.py
│   ├── downloader.py
│   ├── player.py
│   └── utils.py
│
├── config.py             # Конфигурация и загрузка токенов
├── bot.py                # Основной файл запуска бота
├── requirements.txt      # Список зависимостей
└── .env                  # Ваши токены (не добавляйте в git!)

```

---

## 🧪 Примечания

- Поддержка ссылок только с Яндекс Музыки.
- Бот работает в одном голосовом канале за раз.
- Убедитесь, что вы добавили бота на сервер с правами на подключение к голосовым каналам.
