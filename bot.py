"""
Telegram-бот «Шурик: путь стажёра»
Запуск:
    pip install -r requirements.txt
    export BOT_TOKEN="токен_от_@BotFather"      # Windows: set BOT_TOKEN=...
    python bot.py
"""
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
ADMIN_ID = os.getenv("ADMIN_ID", "")
DB_PATH = Path(__file__).parent / "users.db"

# Картинки лежат в папке images рядом с bot.py
IMG_DIR = Path(__file__).parent / "images"
WELCOME_IMG = IMG_DIR / "welcome-msg.png"
NOT_FOUND_IMG = IMG_DIR / "not_found.png"

# ──────────────────────────── ТЕКСТЫ ────────────────────────────

START_TEXT = (
    "👋 Привет, {name}! Я Шурик, и я помогу тебе стать настоящим инженером!\n\n"
    "Я собрал пару полезных советов, которые помогут тебе начать карьеру "
    "со стажировки. Нажми кнопку ниже — расскажу, о чём этот бот."
)

ABOUT_TEXT = (
    "📖 <b>О боте</b>\n\n"
    "Я — Шурик, и я помогаю студентам и выпускникам пройти путь "
    "от «ничего не умею» до «меня взяли на стажировку».\n\n"
    "Здесь вы найдёте:\n"
    "• список навыков, которые нужны для первой стажировки;\n"
    "• ссылки на полезные ресурсы и площадки с вакансиями;\n"
    "• компании, которые берут стажёров;\n"
    "• а скоро — советы по росту, главные правила стажёра и "
    "карьерные консультации.\n\n"
    "Всё по-научному и без лишней воды. Выбирайте раздел 👇"
)

MENU_TEXT = "📚 <b>Главное меню</b>\nВыберите раздел, коллега:"

FIRST_INTERNSHIP_TEXT = (
    "🎯 <b>Как попасть на первую стажировку</b>\n\n"
    "Шурик рекомендует действовать по плану — как перед сессией.\n\n"
    "<b>🧠 Навыки, которые нужны</b>\n"
    "• <b>Базовая профессиональная база</b> — по выбранному направлению "
    "(программирование, аналитика, маркетинг, дизайн и т. д.)\n"
    "• <b>Excel / Google Таблицы</b> — формулы, сводные таблицы\n"
    "• <b>SQL и основы Python</b> — для аналитики и разработки\n"
    "• <b>Git и GitHub</b> — для технических направлений\n"
    "• <b>Английский</b> — хотя бы чтение документации (B1+)\n"
    "• <b>Резюме и сопроводительное письмо</b> — на 1 страницу, по делу\n"
    "• <b>Коммуникация</b> — умение задавать вопросы и признавать, "
    "что чего-то не знаешь\n"
    "• <b>Самообучение</b> — быстро разбираться в новом\n"
    "• <b>Портфолио / пет-проекты</b> — 2–3 работы лучше, чем 10 курсов\n\n"
    "<b>🔗 Где учиться и искать вакансии</b>\n"
    '• <a href="https://career.habr.com/">Хабр Карьера</a>\n'
    '• <a href="https://hh.ru/">hh.ru</a>\n'
    '• <a href="https://www.linkedin.com/jobs/">LinkedIn Jobs</a>\n'
    '• <a href="https://github.com/">GitHub</a> — для портфолио\n'
    '• <a href="https://www.coursera.org/">Coursera</a> и '
    '<a href="https://stepik.org/">Stepik</a> — для курсов\n\n'
    "<b>🏢 Компании со стажировками</b>\n"
    '• <a href="https://yandex.ru/yaintern/">Яндекс</a>\n'
    '• <a href="https://education.tbank.ru/start/">Т-Банк (Тинькофф)</a>\n'
    '• <a href="https://internship.vk.company/">VK</a>\n'
    '• <a href="https://job.ozon.ru/">Ozon</a>\n'
    '• <a href="https://careers.kaspersky.ru/">Лаборатория Касперского</a>\n'
    '• <a href="https://www.jetbrains.com/careers/internships/">JetBrains</a>\n'
    '• <a href="https://buildyourfuture.withgoogle.com/internships">Google</a>\n\n'
    "💡 <i>Совет от Шурика: откликайтесь сразу в 15–20 мест. "
    "Одного отказа — ещё не повод бросать науку.</i>"
)

GROW_TEXT = (
    "📈 <b>Как расти дальше?</b>\n\n"
    "⏳ Раздел ещё в разработке. Шурик пока дописывает конспект — "
    "скоро будет доступен!"
)

MAIN_TEXT = (
    "⭐ <b>Что самое главное в работе стажёра?</b>\n\n"
    "⏳ Раздел ещё в разработке. Шурик пока дописывает конспект — "
    "скоро будет доступен!"
)

CONSULT_TEXT = (
    "🗓 <b>Карьерная консультация</b>\n\n"
    "⏳ Запись пока не открыта. Шурик договаривается с наставниками — "
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
            [InlineKeyboardButton(text="🎯 Как попасть на первую стажировку", callback_data="first")],
            [InlineKeyboardButton(text="📈 Как расти дальше?", callback_data="grow")],
            [InlineKeyboardButton(text="⭐ Что самое главное в работе стажёра?", callback_data="main")],
            [InlineKeyboardButton(text="🗓 Карьерная консультация", callback_data="consult")],
        ]
    )


def about_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Перейти в меню", callback_data="menu")]
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
    await show(call, FIRST_INTERNSHIP_TEXT, back_kb())


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
    if message.from_user.id == ADMIN_ID:
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
    if not ADMIN_ID:
        logging.warning("ADMIN_IDS не задан — команда /stats никому не доступна")
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())