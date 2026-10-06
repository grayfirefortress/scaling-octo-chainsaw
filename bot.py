"""
Telegram-бот «Шурик: путь стажёра»
Запуск:
    pip install -r requirements.txt
    export BOT_TOKEN="токен_от_@BotFather"      # Windows: set BOT_TOKEN=...
    python bot.py
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ──────────────────────────── ТЕКСТЫ ────────────────────────────

START_TEXT = (
    "👋 Здравствуйте! Меня зовут <b>Шурик</b>. Я студент, комсомолец и, "
    "между прочим, просто красавец.\n\n"
    "Я собрал конспект для тех, кто хочет начать карьеру со стажировки. "
    "Нажмите кнопку ниже — расскажу, о чём этот бот."
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


# ──────────────────────────── ХЕНДЛЕРЫ ────────────────────────────

dp = Dispatcher()


async def show(call: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    """Редактирует текущее сообщение (без спама новыми)."""
    await call.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    await call.answer()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(START_TEXT, reply_markup=start_kb())


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
    await show(call, GROW_TEXT, back_kb())


@dp.callback_query(F.data == "main")
async def cb_main(call: CallbackQuery) -> None:
    await show(call, MAIN_TEXT, back_kb())


@dp.callback_query(F.data == "consult")
async def cb_consult(call: CallbackQuery) -> None:
    await show(call, CONSULT_TEXT, back_kb())


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Задайте переменную окружения BOT_TOKEN")
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())