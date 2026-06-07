# Senior Tarot Bot

Telegram-бот с картой дня, раскладами, донатами, дневными лимитами, утренними напоминаниями, обращениями к админу и админской статистикой.

## Локальный запуск

1. Создать виртуальное окружение:

```powershell
python -m venv venv
```

2. Активировать окружение:

```powershell
venv\Scripts\Activate.ps1
```

3. Установить зависимости:

```powershell
python -m pip install -r requirements.txt
```

4. Создать `.env` в корне проекта и заполнить переменные.

5. Запустить бота:

```powershell
python main.py
```

База SQLite создаётся автоматически через `init_db()` при старте.

## Возможности

- карта дня;
- общий, карьерный и проектный расклады;
- дневной лимит: 1 карта дня или 1 расклад в сутки;
- админы из `ADMIN_IDS` работают без дневного лимита;
- донат 99 ₽ через Telegram Payments;
- после успешного доната пользователь получает 7 дней без лимитов;
- утренняя рассылка с напоминанием вытянуть карту дня;
- кнопки подписки и отписки от утренних уведомлений;
- кнопка “Сообщить о проблеме” отправляет обращение админам;
- кнопка “Поделиться ботом” ведёт на `https://t.me/BugOracleBot`;
- `/stats` и `/donations_stats` для админов.

## .env

Минимальный набор:

```env
BOT_TOKEN=telegram_bot_token
PAYMENT_PROVIDER_TOKEN=telegram_payment_provider_token
ADMIN_IDS=123456789
SERVER_MONTHLY_GOAL_MINOR=90000
SERVER_MONTHLY_GOAL_CURRENCY=RUB
BOT_USERNAME=BugOracleBot
```

Переменные:

- `BOT_TOKEN` - токен Telegram-бота.
- `PAYMENT_PROVIDER_TOKEN` - токен платёжного провайдера для Telegram Payments.
- `ADMIN_IDS` - Telegram user id админов через пробел, запятую или `;`.
  Обязателен для `/stats`, `/donations_stats` и кнопки “Сообщить о проблеме”.
  Также снимает дневной лимит с админов.
  Если на сервере не указан актуальный Telegram ID админа, обращения пользователей не смогут быть доставлены.
- `SERVER_MONTHLY_GOAL_MINOR` - месячная цель в minor units, например `90000` для 900.00 RUB.
- `SERVER_MONTHLY_GOAL_CURRENCY` - валюта цели, по умолчанию `RUB`.
- `BOT_USERNAME` - username бота без `@`, используется для кнопки “Поделиться ботом”.
  Для этого проекта: `BugOracleBot`, ссылка `https://t.me/BugOracleBot`.

Не коммитить `.env`, токены, дампы БД и платежные секреты.

## Тесты

Запуск всех тестов:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests
```

Что покрыто:

- дневные лимиты и unlimited-доступ;
- обход дневного лимита для админов;
- повторная обработка одного `payment_id`;
- статистика readings и `/stats`;
- донаты и месячный прогресс;
- подписка/отписка от утренних уведомлений;
- отправка обращений админу через “Сообщить о проблеме”;
- раскладка клавиатур и ссылка на `BugOracleBot`;
- временные картинки;
- московская timezone для лимитов и уведомлений.

## Уведомления

Планировщик запускается при старте бота и каждый день в 10:00 по `Europe/Moscow` отправляет утреннее напоминание пользователям, которые:

- не заблокировали бота;
- подписаны на утренние уведомления;
- ещё не делали карту дня или расклад сегодня.

Пользователь может переключать подписку кнопкой `Отписаться от уведомлений` / `Подписаться на уведомления`.

## Сообщить о проблеме

Кнопка `Сообщить о проблеме` переводит пользователя в режим ожидания одного текстового сообщения. Следующее сообщение отправляется всем админам из `ADMIN_IDS` и содержит:

- текст обращения;
- `user_id`;
- `username`, если есть;
- `first_name`, если есть;
- дату и время получения обращения.

Ввод можно отменить кнопкой `Отмена` или командой `/cancel`. Если во время ввода пользователь нажмёт команду или кнопку меню, режим обращения отменится, чтобы команда не ушла админу как текст проблемы.

## Запуск на сервере

Пример для Linux-сервера:

```bash
sudo mkdir -p /opt/Senior_Tarot_bot
sudo chown "$USER":"$USER" /opt/Senior_Tarot_bot
cd /opt/Senior_Tarot_bot
git clone <repo-url> .
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
nano .env
venv/bin/python main.py
```

Для production лучше запускать через systemd.

## systemd

Создать unit-файл:

```bash
sudo nano /etc/systemd/system/senior-tarot-bot.service
```

Пример:

```ini
[Unit]
Description=Senior Tarot Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/Senior_Tarot_bot
EnvironmentFile=/opt/Senior_Tarot_bot/.env
ExecStart=/opt/Senior_Tarot_bot/venv/bin/python /opt/Senior_Tarot_bot/main.py
Restart=always
RestartSec=5
User=botuser
Group=botuser

[Install]
WantedBy=multi-user.target
```

Команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable senior-tarot-bot
sudo systemctl start senior-tarot-bot
sudo systemctl status senior-tarot-bot
sudo journalctl -u senior-tarot-bot -f
sudo systemctl restart senior-tarot-bot
sudo systemctl stop senior-tarot-bot
```

После обновления кода:

```bash
cd /opt/Senior_Tarot_bot
git pull
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m unittest discover -s tests
sudo systemctl restart senior-tarot-bot
```

## Как тестировать платежи

1. Использовать тестовый платёжный токен провайдера, не production-токен.
2. Указать тестовый `PAYMENT_PROVIDER_TOKEN` в `.env`.
3. Запустить бота локально или на тестовом сервере.
4. В Telegram открыть бота и нажать кнопку поддержки проекта.
5. Провести тестовый платёж.
6. Проверить логи:

```bash
sudo journalctl -u senior-tarot-bot -f
```

Ожидаемые события:

- `Payment processed successfully` для нового платежа;
- `Duplicate payment ignored` при повторном `payment_id`;
- `Payment pre-checkout rejected: invalid payload` при неверном payload;
- traceback через `logger.exception`, если запись доната или выдача unlimited упали.

Проверить БД можно локально через sqlite:

```bash
sqlite3 senior_tarot.db "SELECT user_id, amount_minor, currency, payment_id, created_at FROM donations ORDER BY id DESC LIMIT 5;"
sqlite3 senior_tarot.db "SELECT user_id, unlimited_until FROM users WHERE unlimited_until IS NOT NULL ORDER BY id DESC LIMIT 5;"
```

В логах нельзя писать токены, `.env`, данные карты, YooKassa-секреты или полные данные пользователя. Нормально логировать `payment_id`, `telegram_user_id`, amount, status, duplicate и traceback.

## Полезные команды бота

- `/start` - старт и меню.
- `/menu` - показать меню.
- `/help` - помощь.
- `/card` - карта дня.
- `/spread` - общий расклад.
- `/career` - карьерный расклад.
- `/project` - проектный расклад.
- `/stats` - админская статистика, только для `ADMIN_IDS`.
- `/donations_stats` - подробная статистика донатов, только для `ADMIN_IDS`.
- `/cancel` - отменить ввод обращения о проблеме, если бот ждёт описание проблемы.
