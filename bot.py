import asyncio
import html
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Telegram ID админов через запятую: export ADMIN_IDS="123456789,987654321"
# (свой ID можно узнать у бота @userinfobot)
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()
}
DB_PATH = Path(__file__).parent / "users.db"

# Картинки лежат в папке images рядом с bot.py
IMG_DIR = Path(__file__).parent / "images"
WELCOME_IMG = IMG_DIR / "livsey.png"
NOT_FOUND_IMG = IMG_DIR / "not_found.png"

# ──────────────────────────── ТЕКСТЫ ────────────────────────────

START_TEXT = (
    "👋 Привет, {name}! Я помогу тебе стать настоящим инженером в крупной айти компании!\n\n"
    "Я собрал пару полезных советов, которые помогут тебе начать карьеру "
    "со стажировки. Нажми кнопку ниже — расскажу."
)

ABOUT_TEXT = (
    "📖 <b>О проекте 'как пройти в библиотеку?'</b>\n\n"
    "Мы помогаем студентам и выпускникам попасть на первую it стажировку."
    "Проект растет с каждым днем и будет дополняться новыми материалами.\n\n"
    "Здесь вы найдёте:\n"
    "• список навыков, которые нужны для первой стажировки;\n"
    "• ссылки на полезные ресурсы и площадки с вакансиями;\n"
    "• компании, которые берут стажёров;\n"
    "• карьерные консультации.\n\n"
    "Без лишней воды и <b>БЕСПЛАТНО</b>. Выбирайте раздел 👇"
)

MENU_TEXT = "📚 <b>Главное меню</b>\nВыбери раздел студент:"

DIRECTIONS_TEXT = (
    "🎯 <b>как попасть на первую стажировку</b>\n\n"
    "Набор навыков зависит от направления. Выбери, куда хочешь пойти 👇"
)

# ── Общие блоки, которые повторяются во всех направлениях ──

COMMON_SKILLS = (
    "• <b>Английский</b> — хотя бы чтение документации (B1+)\n"
    "• <b>Резюме и сопроводительное письмо</b> — на 1 страницу, по делу\n"
    "• <b>Коммуникация</b> — умение задавать вопросы и признавать, "
    "что чего-то не знаешь\n"
    "• <b>Самообучение</b> — быстро разбираться в новом\n"
    "• <b>Портфолио / пет-проекты</b> — 2–3 работы лучше, чем 10 курсов\n\n"
)

COMMON_JOBS = (
    "<b>🔍 Где искать вакансии</b>\n"
    '• <a href="https://career.habr.com/">Хабр Карьера</a>\n'
    '• <a href="https://hh.ru/">hh.ru</a>\n'
    '• <a href="https://www.linkedin.com/jobs/">LinkedIn Jobs</a>\n'
    '• <a href="https://github.com/">GitHub</a> — для портфолио\n\n'
)

COMMON_COMPANIES = (
    "<b>🏢 Компании со стажировками</b>\n"
    '• <a href="https://yandex.ru/yaintern/">Яндекс</a>\n'
    '• <a href="https://education.tbank.ru/start/">Т-Банк (Тинькофф)</a>\n'
    '• <a href="https://internship.vk.company/">VK</a>\n'
    '• <a href="https://job.ozon.ru/">Ozon</a>\n'
    '• <a href="https://careers.kaspersky.ru/">Лаборатория Касперского</a>\n'
    '• <a href="https://www.jetbrains.com/careers/internships/">JetBrains</a>\n'
    '• <a href="https://buildyourfuture.withgoogle.com/internships">Google</a>\n\n'
)

COMMON_TIP = (
    "💡 <i>Совет: откликайтесь сразу в 15–20 мест. "
    "Один отказ — ещё не повод бросать.</i>"
)

# ── Видео, которые уже были в гайде (переиспользуются в нескольких направлениях) ──

VIDEO_PYTHON = (
    "<i>Python</i>\n"
    '• <a href="https://www.youtube.com/playlist?list=PL0lO_mIqDDFXgfuxOEDTCwsWmKezOaDTu">Плейлист: Python для начинающих</a>\n'
    '• <a href="https://www.youtube.com/watch?v=P2Spqz_CXM8">Полный курс Python в одном видео</a>\n'
)
VIDEO_LINUX = (
    "<i>Linux</i>\n"
    '• <a href="https://www.youtube.com/playlist?list=PLg5SS_4L6LYuE4z-3BgLYGkZrs-cF4Tep">Плейлист: Linux для начинающих</a>\n'
    '• <a href="https://www.youtube.com/playlist?list=PL0lO_mIqDDFUwVWvVitxG2oXA6a-Nq-Qq">Linux Ubuntu и Bash с нуля</a>\n'
)
VIDEO_SQL = (
    "<i>Базы данных</i>\n"
    '• <a href="https://www.youtube.com/watch?v=IK6e1SFCdow">SQL для начинающих: SELECT, JOIN, GROUP BY (MySQL)</a>\n'
    '• <a href="https://www.youtube.com/watch?v=HVQNxdI6fqY">Практический курс SQL: PostgreSQL</a>\n'
)

# ── Тексты направлений ──

PYTHON_TEXT = (
    "🐍 <b>Python-разработчик: первая стажировка</b>\n\n"
    "Я рекомендую действовать по плану — как перед сессией.\n\n"
    "<b>🧠 Навыки, которые нужны</b>\n"
    "• <b>Python</b> — синтаксис, ООП, функции, исключения, типизация, async\n"
    "• <b>Веб-фреймворк</b> — FastAPI, Django или Flask (хватит одного)\n"
    "• <b>Базы данных</b> — реляционная модель, SQL, JOIN, индексы, PostgreSQL\n"
    "• <b>REST API</b> — HTTP, коды ответов, JSON, авторизация\n"
    "• <b>Git и GitHub</b> — ветки, pull request'ы, разрешение конфликтов\n"
    "• <b>Linux</b> — терминал, файловая система, права доступа\n"
    "• <b>Тесты</b> — pytest на базовом уровне\n"
    "• <b>Docker</b> — собрать образ и поднять приложение с БД\n"
    "• <b>Алгоритмы</b> — массивы, словари, сортировки, сложность\n"
    + COMMON_SKILLS
    + "<b>📚 Где учиться</b>\n"
    '• <a href="https://docs.python.org/3/tutorial/">Официальный туториал Python</a>\n'
    '• <a href="https://fastapi.tiangolo.com/tutorial/">Туториал FastAPI</a>\n'
    '• <a href="https://docs.djangoproject.com/en/stable/intro/tutorial01/">Туториал Django</a>\n'
    '• <a href="https://roadmap.sh/python">Roadmap: Python</a>\n'
    '• <a href="https://www.coursera.org/">Coursera</a> и '
    '<a href="https://stepik.org/">Stepik</a> — для курсов\n\n'
    "<b>🎥 Видео по темам</b>\n"
    + VIDEO_PYTHON
    + VIDEO_LINUX
    + VIDEO_SQL
    + "\n"
    + COMMON_JOBS
    + COMMON_COMPANIES
    + COMMON_TIP
)

DEVOPS_TEXT = (
    "⚙️ <b>DevOps: первая стажировка</b>\n\n"
    "DevOps — не стартовая позиция «с нуля», но на стажировку или junior "
    "попасть реально, если уверенно держишь базу.\n\n"
    "<b>🧠 Навыки, которые нужны</b>\n"
    "• <b>Linux</b> — терминал, процессы, systemd, права доступа, логи\n"
    "• <b>Сети</b> — TCP/IP, DNS, HTTP/HTTPS, порты, NAT, firewall\n"
    "• <b>Bash и Python</b> — автоматизация рутины скриптами\n"
    "• <b>Git</b> — ветки, merge/rebase, рабочие процессы команды\n"
    "• <b>Docker</b> — образы, контейнеры, volumes, docker compose\n"
    "• <b>CI/CD</b> — GitHub Actions или GitLab CI: сборка, тесты, деплой\n"
    "• <b>Kubernetes</b> — pod, deployment, service (на уровне основ)\n"
    "• <b>IaC</b> — Terraform и/или Ansible\n"
    "• <b>Мониторинг</b> — Prometheus, Grafana, логирование\n"
    "• <b>Облака</b> — базовые сервисы любого провайдера\n"
    + COMMON_SKILLS
    + "<b>📚 Где учиться</b>\n"
    '• <a href="https://roadmap.sh/devops">Roadmap: DevOps</a>\n'
    '• <a href="https://docs.docker.com/get-started/">Docker: Get Started</a>\n'
    '• <a href="https://kubernetes.io/docs/tutorials/">Kubernetes: туториалы</a>\n'
    '• <a href="https://docs.github.com/en/actions">GitHub Actions: документация</a>\n'
    '• <a href="https://developer.hashicorp.com/terraform/tutorials">Terraform: туториалы</a>\n\n'
    "<b>🎥 Видео по темам</b>\n"
    + VIDEO_LINUX
    + VIDEO_PYTHON
    + "\n"
    "💪 <i>Пет-проект: подними своё приложение в Docker, настрой CI/CD "
    "и мониторинг, выложи конфиги на GitHub.</i>\n\n"
    + COMMON_JOBS
    + COMMON_COMPANIES
    + COMMON_TIP
)

GO_TEXT = (
    "🐹 <b>Go-разработчик: первая стажировка</b>\n\n"
    "Go любят за простоту и скорость, его активно используют в бэкенде "
    "и инфраструктуре.\n\n"
    "<b>🧠 Навыки, которые нужны</b>\n"
    "• <b>Go</b> — синтаксис, структуры, интерфейсы, обработка ошибок\n"
    "• <b>Конкурентность</b> — горутины, каналы, sync, context\n"
    "• <b>net/http</b> — написать REST API без фреймворка, затем с chi/gin\n"
    "• <b>Базы данных</b> — SQL, PostgreSQL, database/sql или pgx\n"
    "• <b>Тесты</b> — пакет testing, табличные тесты\n"
    "• <b>Git и GitHub</b> — ветки, pull request'ы\n"
    "• <b>Linux</b> — терминал, сборка и запуск сервисов\n"
    "• <b>Docker</b> — упаковать сервис и БД в контейнеры\n"
    "• <b>gRPC и очереди</b> — знакомство (плюс при отборе)\n"
    "• <b>Алгоритмы</b> — структуры данных и сложность\n"
    + COMMON_SKILLS
    + "<b>📚 Где учиться</b>\n"
    '• <a href="https://go.dev/tour/">A Tour of Go</a> — официальный интерактивный тур\n'
    '• <a href="https://gobyexample.com/">Go by Example</a>\n'
    '• <a href="https://go.dev/doc/effective_go">Effective Go</a>\n'
    '• <a href="https://roadmap.sh/golang">Roadmap: Go</a>\n'
    '• <a href="https://stepik.org/">Stepik</a> — курсы на русском\n\n'
    "<b>🎥 Видео по темам</b>\n"
    + VIDEO_LINUX
    + VIDEO_SQL
    + "\n"
    "💪 <i>Пет-проект: сервис-сокращатель ссылок или TODO API на Go "
    "с PostgreSQL, тестами и Dockerfile.</i>\n\n"
    + COMMON_JOBS
    + COMMON_COMPANIES
    + COMMON_TIP
)

FRONTEND_TEXT = (
    "🎨 <b>Frontend: первая стажировка</b>\n\n"
    "Во фронтенде портфолио решает почти всё — его можно показать "
    "в одну ссылку.\n\n"
    "<b>🧠 Навыки, которые нужны</b>\n"
    "• <b>HTML и CSS</b> — семантика, flexbox, grid, адаптивная вёрстка\n"
    "• <b>JavaScript</b> — ES6+, DOM, события, замыкания, промисы, async/await\n"
    "• <b>TypeScript</b> — базовые типы, интерфейсы, дженерики\n"
    "• <b>React</b> — компоненты, хуки, состояние, роутинг (или Vue)\n"
    "• <b>Работа с API</b> — fetch, JSON, обработка ошибок и загрузки\n"
    "• <b>Инструменты</b> — npm, Vite, ESLint, DevTools в браузере\n"
    "• <b>Git и GitHub</b> — ветки, pull request'ы\n"
    "• <b>Основы UX</b> — доступность (a11y), производительность\n"
    + COMMON_SKILLS
    + "<b>📚 Где учиться</b>\n"
    '• <a href="https://roadmap.sh/frontend">Roadmap: Frontend</a>\n'
    '• <a href="https://developer.mozilla.org/ru/docs/Learn">MDN: учебные материалы</a>\n'
    '• <a href="https://learn.javascript.ru/">Современный учебник JavaScript</a>\n'
    '• <a href="https://react.dev/learn">React: официальное обучение</a>\n'
    '• <a href="https://www.typescriptlang.org/docs/">TypeScript: документация</a>\n'
    '• <a href="https://www.frontendmentor.io/">Frontend Mentor</a> — задачи для практики\n\n'
    "💪 <i>Портфолио: 3 проекта — адаптивный лендинг, приложение "
    "с запросами к API и один проект на React + TypeScript. "
    "Выложи на GitHub Pages или Vercel.</i>\n\n"
    + COMMON_JOBS
    + COMMON_COMPANIES
    + COMMON_TIP
)

# callback_data -> (текст экрана)
DIRECTION_TEXTS = {
    "dir_python": PYTHON_TEXT,
    "dir_devops": DEVOPS_TEXT,
    "dir_go": GO_TEXT,
    "dir_frontend": FRONTEND_TEXT,
}

GROW_TEXT = (
    "📈 <b>как расти дальше?</b>\n\n"
    "⏳ Раздел ещё в разработке. Шурик пока дописывает конспект — "
    "скоро будет доступен!"
)

MAIN_TEXT = (
    "⭐ <b>что самое главное в работе стажёра?</b>\n\n"
    "⏳ Раздел ещё в разработке. Шурик пока дописывает конспект — "
    "скоро будет доступен!"
)

CONSULT_TEXT = (
    "🗓 <b>карьерная консультация</b>\n\n"
    "⏳ Запись пока не открыта. Доктор ливси договаривается с наставниками — "
    "скоро запись будет доступна!"
)

# ──────────────────────────── КЛАВИАТУРЫ ────────────────────────────


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Что это за бот?", callback_data="about")]
        ]
    )


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="как попасть на первую стажировку", callback_data="first")],
            [InlineKeyboardButton(text="как расти по грейду?", callback_data="grow")],
            [InlineKeyboardButton(text="полный гайд по трудоустройству в big-tech", callback_data="main")],
            [InlineKeyboardButton(text="карьерная консультация", callback_data="consult")],
        ]
    )


def directions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐍 Python-разработчик", callback_data="dir_python")],
            [InlineKeyboardButton(text="⚙️ DevOps", callback_data="dir_devops")],
            [InlineKeyboardButton(text="🐹 Go-разработчик", callback_data="dir_go")],
            [InlineKeyboardButton(text="🎨 Frontend", callback_data="dir_frontend")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu")],
        ]
    )


def direction_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К выбору направления", callback_data="first")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu")],
        ]
    )


def about_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти в меню", callback_data="menu")]
        ]
    )


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu")]
        ]
    )


# ──────────────────────────── БАЗА ПОЛЬЗОВАТЕЛЕЙ ────────────────────────────


def db_connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def db_init() -> None:
    with db_connect() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   user_id    INTEGER PRIMARY KEY,
                   username   TEXT,
                   full_name  TEXT,
                   first_seen TEXT NOT NULL,
                   last_seen  TEXT NOT NULL,
                   actions    INTEGER NOT NULL DEFAULT 1
               )"""
        )


def touch_user(user_id: int, username: str | None, full_name: str) -> None:
    """Записывает нового пользователя или обновляет существующего."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db_connect() as con:
        con.execute(
            """INSERT INTO users (user_id, username, full_name, first_seen, last_seen)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   username  = excluded.username,
                   full_name = excluded.full_name,
                   last_seen = excluded.last_seen,
                   actions   = actions + 1""",
            (user_id, username, full_name, now, now),
        )


def get_stats() -> dict:
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(days=1)).isoformat(timespec="seconds")
    week_ago = (now - timedelta(days=7)).isoformat(timespec="seconds")
    with db_connect() as con:
        total = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        new_24h = con.execute(
            "SELECT COUNT(*) FROM users WHERE first_seen >= ?", (day_ago,)
        ).fetchone()[0]
        active_7d = con.execute(
            "SELECT COUNT(*) FROM users WHERE last_seen >= ?", (week_ago,)
        ).fetchone()[0]
        rows = con.execute(
            "SELECT user_id, username, full_name, last_seen FROM users "
            "ORDER BY last_seen DESC"
        ).fetchall()
    return {"total": total, "new_24h": new_24h, "active_7d": active_7d, "rows": rows}


class TrackUsersMiddleware(BaseMiddleware):
    """Запоминает каждого, кто взаимодействует с ботом."""

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user and not user.is_bot:
            touch_user(user.id, user.username, user.full_name)
        return await handler(event, data)


# ──────────────────────────── ХЕНДЛЕРЫ ────────────────────────────

dp = Dispatcher()


async def show(
    call: CallbackQuery,
    text: str,
    kb: InlineKeyboardMarkup,
    photo: Path | None = None,
) -> None:
    """
    Показывает экран. Если картинки нет и текущее сообщение текстовое —
    просто редактирует его. Если нужна картинка (или текущее сообщение
    с картинкой) — Telegram не умеет превращать текст в фото и обратно,
    поэтому старое сообщение удаляется и отправляется новое.
    """
    msg = call.message
    if photo is None and not msg.photo:
        await msg.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await msg.delete()
        if photo:
            await msg.answer_photo(FSInputFile(photo), caption=text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await call.answer()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer_photo(
        FSInputFile(WELCOME_IMG),
        caption=START_TEXT.format(name=html.escape(message.from_user.first_name or "друг")),
        reply_markup=start_kb(),
    )


@dp.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery) -> None:
    await show(call, ABOUT_TEXT, about_kb())


@dp.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    await show(call, MENU_TEXT, menu_kb())


@dp.callback_query(F.data == "first")
async def cb_first(call: CallbackQuery) -> None:
    """Экран выбора направления."""
    await show(call, DIRECTIONS_TEXT, directions_kb())


@dp.callback_query(F.data.in_(DIRECTION_TEXTS.keys()))
async def cb_direction(call: CallbackQuery) -> None:
    """Гайд для выбранного направления."""
    await show(call, DIRECTION_TEXTS[call.data], direction_back_kb())


@dp.callback_query(F.data == "grow")
async def cb_grow(call: CallbackQuery) -> None:
    await show(call, GROW_TEXT, back_kb(), photo=NOT_FOUND_IMG)


@dp.callback_query(F.data == "main")
async def cb_main(call: CallbackQuery) -> None:
    await show(call, MAIN_TEXT, back_kb(), photo=NOT_FOUND_IMG)


@dp.callback_query(F.data == "consult")
async def cb_consult(call: CallbackQuery) -> None:
    await show(call, CONSULT_TEXT, back_kb(), photo=NOT_FOUND_IMG)


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Статистика для админа: кто заходил в бота."""
    if message.from_user.id not in ADMIN_IDS:
        return  # для обычных пользователей команды как будто нет

    st = get_stats()
    header = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{st['total']}</b>\n"
        f"🆕 Новых за 24 часа: <b>{st['new_24h']}</b>\n"
        f"🔥 Активных за 7 дней: <b>{st['active_7d']}</b>\n\n"
        "<b>Кто заходил</b> (по последнему визиту, время UTC):\n"
    )

    lines = []
    for i, (uid, username, full_name, last_seen) in enumerate(st["rows"], 1):
        if username:
            who = f"@{html.escape(username)}"
        else:
            who = f"без ника, {html.escape(full_name or '—')} (id {uid})"
        lines.append(f"{i}. {who} — {last_seen[:16].replace('T', ' ')}")

    if not lines:
        await message.answer(header + "пока никого.")
        return

    # Лимит Telegram — 4096 символов, поэтому режем список на части
    chunks, current = [], header
    for line in lines:
        if len(current) + len(line) + 1 > 3800:
            chunks.append(current)
            current = ""
        current += line + "\n"
    chunks.append(current)

    for chunk in chunks:
        await message.answer(chunk)


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Задайте переменную окружения BOT_TOKEN")
    logging.basicConfig(level=logging.INFO)
    db_init()
    dp.message.outer_middleware(TrackUsersMiddleware())
    dp.callback_query.outer_middleware(TrackUsersMiddleware())
    if not ADMIN_IDS:
        logging.warning("ADMIN_IDS не задан — команда /stats никому не доступна")
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())