import asyncio
import html
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BotCommand,
    ErrorEvent,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

from database import Database

# Загружаем переменные окружения из .env
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан. Укажите его в файле .env")

# Все сообщения бота отправляются в HTML-режиме, превью ссылок отключено.
# Нужен aiogram >= 3.7:  pip install -U aiogram
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    ),
)
dp = Dispatcher()
db = Database()

# Отзывы хранятся в той же таблице сообщений, с этим префиксом
FEEDBACK_PREFIX = "[feedback] "
MAX_FEEDBACK_LEN = 2000

# ID пользователей, от которых бот ждёт следующее сообщение как отзыв
AWAITING_FEEDBACK: set[int] = set()

# --- Оформление ---
LINE = "━━━━━━━━━━━━━━━━"

ABOUT_TEXT = (
    "◈ <b>РЕПЛИКАЦИЯ</b>  ·  <i>beta</i>\n"
    "<i>Воспроизведи в себе то, что работает.</i>\n"
    "\n"
    "Проект, где знания, дисциплина и ясность мышления собраны в одном "
    "месте: без шума, воды и лишних слов.\n"
    f"\n{LINE}\n"
    "<b>Четыре вектора роста</b>\n"
    "\n"
    "🌍  <b>История</b>\n"
    "<i>понять, как устроен мир</i>\n"
    "\n"
    "🧠  <b>Психология общения</b>\n"
    "<i>слышать и быть услышанным</i>\n"
    "\n"
    "💪  <b>Трансформация тела</b>\n"
    "<i>сила, энергия, форма</i>\n"
    "\n"
    "🏛  <b>Стоический образ жизни</b>\n"
    "<i>спокойствие, не зависящее от обстоятельств</i>\n"
    f"\n{LINE}\n"
    "🧪 <b>Бета-версия.</b> Бот развивается прямо сейчас. Нашли ошибку или "
    "есть идея? Нажмите «💬 Отзыв», это поможет сделать проект лучше.\n"
    "<i>В бета-режиме сообщения сохраняются для улучшения бота.</i>\n"
    "\n"
    "Выберите вектор ниже 👇"
)

HELP_TEXT = (
    "<b>Команды</b>\n\n"
    "/start: начать сначала\n"
    "/menu: главное меню\n"
    "/feedback: оставить отзыв\n"
    "/help: эта справка"
)

ADMIN_HELP_TEXT = (
    "\n\n<b>Для администратора</b>\n\n"
    "/stats: статистика\n"
    "/feedbacks: последние отзывы\n"
    "/broadcast &lt;текст&gt;: рассылка всем пользователям"
)

# --- Контент по векторам развития ---
CONTENT = {
    "history": {
        "title": "🌍 История",
        "items": [
            ("«Sapiens. Краткая история человечества» — Юваль Ной Харари", "https://www.litres.ru/uval-noy-harari/sapiens-kratkaya-istoriya-chelovechestva/"),
            ("«История цивилизаций» — Арнольд Тойнби", "https://www.litres.ru/arnold-toynbi/istoriya-civilizaciy/"),
            ("«Война и мир» — Лев Толстой (исторический контекст)", "https://www.litres.ru/lev-tolstoy/voyna-i-mir/"),
            ("Лекция «История мира» — курс на YouTube", "https://www.youtube.com/results?search_query=история+мира+лекция"),
        ],
    },
    "psychology": {
        "title": "🧠 Психология общения",
        "items": [
            ("«Как завоёвывать друзей и оказывать влияние на людей» — Дейл Карнеги", "https://www.litres.ru/deyl-karnegi/kak-zavoevyvat-druzey-i-okazyvat-vliyanie-na-ludey/"),
            ("«Язык телодвижений» — Аллан Пиз", "https://www.litres.ru/allan-piz/yazyk-telodvizheniy/"),
            ("«Тонкое искусство пофигизма» — Марк Мэнсон", "https://www.litres.ru/mark-menson/tonkoe-iskusstvo-pofigizma/"),
            ("Лекция «Психология общения» — курс на YouTube", "https://www.youtube.com/results?search_query=психология+общения+лекция"),
        ],
    },
    "body": {
        "title": "💪 Трансформация тела",
        "items": [
            ("«Анатомия силовых упражнений» — Фредерик Делавье", "https://www.litres.ru/frederik-delave/anatomiya-silovyh-uprazhneniy/"),
            ("«Стройность и сила» — руководство по фитнесу", "https://www.litres.ru/"),
            ("«Питание для набора мышечной массы» — гайд", "https://www.litres.ru/"),
            ("Лекция «Трансформация тела» — курс на YouTube", "https://www.youtube.com/results?search_query=трансформация+тела+лекция"),
        ],
    },
    "stoicism": {
        "title": "🏛️ Стоический образ жизни",
        "items": [
            ("«Размышления» — Марк Аврелий", "https://www.litres.ru/mark-avreliy/razmyshleniya/"),
            ("«Письма к Луцилию» — Сенека", "https://www.litres.ru/luciy-anney-seneka/pisma-k-luciliu/"),
            ("«Энхиридион» — Эпиктет", "https://www.litres.ru/epiktet/enhiridion/"),
            ("Лекция «Стоицизм» — курс на YouTube", "https://www.youtube.com/results?search_query=стоицизм+лекция"),
        ],
    },
}

# Название кнопки -> ключ раздела (кнопки строятся из CONTENT, поэтому всегда совпадают)
TITLE_TO_KEY = {data["title"]: key for key, data in CONTENT.items()}
FEEDBACK_BUTTON = "💬 Отзыв"

main_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=title)] for title in TITLE_TO_KEY]
    + [[KeyboardButton(text=FEEDBACK_BUTTON)]],
    resize_keyboard=True,
)


# --- Вспомогательные функции ---
def _is_admin(user_id: int) -> bool:
    return bool(ADMIN_ID) and str(user_id) == str(ADMIN_ID)


def _track(message: Message, text: str | None = None) -> None:
    """Сохраняет входящее сообщение и сбрасывает режим «жду отзыв»."""
    user = message.from_user
    db.save_message(user.id, user.username, text if text is not None else (message.text or ""))
    AWAITING_FEEDBACK.discard(user.id)


def _who(user_id, username) -> str:
    return f"@{html.escape(username)}" if username else str(user_id)


async def _send_long(message: Message, text: str) -> None:
    """Отправляет длинный текст частями (лимит Telegram: 4096 символов)."""
    chunk = ""
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > 3800:
            await message.answer(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk.strip():
        await message.answer(chunk)


async def _notify_admin(text: str) -> None:
    if not ADMIN_ID:
        return
    try:
        await bot.send_message(int(ADMIN_ID), text)
    except (TelegramAPIError, ValueError):
        logging.warning("Не удалось отправить уведомление администратору")


async def _save_feedback(message: Message, text: str) -> None:
    user = message.from_user
    text = text.strip()[:MAX_FEEDBACK_LEN]
    db.save_message(user.id, user.username, f"{FEEDBACK_PREFIX}{text}")
    AWAITING_FEEDBACK.discard(user.id)

    await message.answer("Спасибо! Отзыв получен 🙌\nВы помогаете сделать проект лучше.", reply_markup=main_menu)
    await _notify_admin(
        f"💬 <b>Новый отзыв</b> от {_who(user.id, user.username)}\n\n{html.escape(text)}"
    )


async def _ask_feedback(message: Message) -> None:
    AWAITING_FEEDBACK.add(message.from_user.id)
    await message.answer(
        "💬 <b>Отзыв</b>\n\n"
        "Напишите одним сообщением: что понравилось, что сломалось "
        "или чего не хватает.\n"
        "<i>Чтобы отменить, просто выберите любой пункт меню.</i>"
    )


# --- Команды ---
@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    db.register_user(user.id, user.username, user.first_name, user.last_name)
    _track(message, "/start")
    await message.answer(
        f"Привет, {html.escape(user.first_name or 'друг')}! 👋\n\n{ABOUT_TEXT}",
        reply_markup=main_menu,
    )


@dp.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    _track(message, "/menu")
    await message.answer(ABOUT_TEXT, reply_markup=main_menu)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    _track(message, "/help")
    text = HELP_TEXT + (ADMIN_HELP_TEXT if _is_admin(message.from_user.id) else "")
    await message.answer(text, reply_markup=main_menu)


@dp.message(Command("feedback"))
async def cmd_feedback(message: Message, command: CommandObject) -> None:
    if command.args:
        await _save_feedback(message, command.args)
    else:
        _track(message, "/feedback")
        await _ask_feedback(message)


@dp.message(F.text == FEEDBACK_BUTTON)
async def btn_feedback(message: Message) -> None:
    _track(message)
    await _ask_feedback(message)


# --- Команды администратора ---
@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    _track(message, "/stats")
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к статистике.")
        return

    users = db.get_all_users()
    messages = db.get_all_messages()
    unique_count = db.get_unique_users_count()
    feedback_count = sum(1 for m in messages if str(m["text"]).startswith(FEEDBACK_PREFIX))

    last_users = "\n".join(
        f"• {u['user_id']} | {_who(u['user_id'], u['username'])} | "
        f"{html.escape(u['first_name'] or '')}"
        for u in users[-10:]
    ) or "Нет пользователей"

    await _send_long(
        message,
        "📊 <b>Статистика</b>\n\n"
        f"👥 Уникальных пользователей: <b>{unique_count}</b>\n"
        f"✉️ Всего сообщений: <b>{len(messages)}</b>\n"
        f"💬 Отзывов: <b>{feedback_count}</b>\n\n"
        f"<b>Последние пользователи:</b>\n{last_users}",
    )


@dp.message(Command("feedbacks"))
async def cmd_feedbacks(message: Message) -> None:
    _track(message, "/feedbacks")
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа.")
        return

    items = [m for m in db.get_all_messages() if str(m["text"]).startswith(FEEDBACK_PREFIX)]
    if not items:
        await message.answer("Отзывов пока нет.")
        return

    lines = ["💬 <b>Последние отзывы</b>\n"]
    for m in items[-15:]:
        text = html.escape(str(m["text"])[len(FEEDBACK_PREFIX):])
        lines.append(f"• {_who(m['user_id'], m['username'])}: {text}\n")
    await _send_long(message, "\n".join(lines))


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject) -> None:
    _track(message, "/broadcast")
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа.")
        return
    if not command.args:
        await message.answer("Использование: /broadcast текст рассылки")
        return

    users = db.get_all_users()
    ok = fail = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], command.args)
            ok += 1
        except TelegramAPIError:
            fail += 1  # пользователь заблокировал бота или недоступен
        await asyncio.sleep(0.05)  # не упираемся в лимиты Telegram

    await message.answer(f"✅ Рассылка завершена\nДоставлено: {ok}\nНе доставлено: {fail}")


# --- Разделы ---
@dp.message(F.text.in_(TITLE_TO_KEY))
async def show_section(message: Message) -> None:
    _track(message)
    content = CONTENT[TITLE_TO_KEY[message.text]]

    lines = [f"<b>{content['title']}</b>", "", "<i>Рекомендуемые материалы:</i>", ""]
    for i, (title, url) in enumerate(content["items"], 1):
        lines.append(f'{i}. <a href="{html.escape(url, quote=True)}">{html.escape(title)}</a>')
    lines.append(f"\n{LINE}\nВыберите другой вектор или откройте /menu")

    await message.answer("\n".join(lines), reply_markup=main_menu)


# --- Всё остальное ---
@dp.message(F.text)
async def other_text(message: Message) -> None:
    user = message.from_user
    if user.id in AWAITING_FEEDBACK:
        await _save_feedback(message, message.text)
        return

    _track(message)
    await message.answer(
        "Я не понял сообщение 😊\nВоспользуйтесь кнопками меню ниже:",
        reply_markup=main_menu,
    )


# --- Глобальный обработчик ошибок ---
@dp.errors()
async def on_error(event: ErrorEvent) -> bool:
    logging.exception("Ошибка при обработке апдейта", exc_info=event.exception)
    await _notify_admin(
        f"⚠️ <b>Ошибка в боте</b>\n<code>{html.escape(repr(event.exception)[:500])}</code>"
    )
    return True


async def main() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Начать сначала"),
            BotCommand(command="menu", description="Главное меню"),
            BotCommand(command="feedback", description="Оставить отзыв"),
            BotCommand(command="help", description="Справка"),
        ]
    )
    logging.info("Бот запущен (beta)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())