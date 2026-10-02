import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

from database import Database

# Загружаем переменные окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота и ID администратора из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан. Укажите его в файле .env")

# Инициализация бота, диспетчера и базы данных
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# --- Главное меню ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Психология общения")],
        [KeyboardButton(text="📚 Интеллектуал")],
        [KeyboardButton(text="🌍 История мира")],
    ],
    resize_keyboard=True,
)

# --- Контент по векторам развития ---
CONTENT = {
    "psychology": {
        "title": "🧠 Психология общения",
        "items": [
            ("«Как завоёвывать друзей и оказывать влияние на людей» — Дейл Карнеги", "https://www.litres.ru/deyl-karnegi/kak-zavoevyvat-druzey-i-okazyvat-vliyanie-na-ludey/"),
            ("«Язык телодвижений» — Аллан Пиз", "https://www.litres.ru/allan-piz/yazyk-telodvizheniy/"),
            ("«Тонкое искусство пофигизма» — Марк Мэнсон", "https://www.litres.ru/mark-menson/tonkoe-iskusstvo-pofigizma/"),
            ("Лекция «Психология общения» — Курс на YouTube", "https://www.youtube.com/results?search_query=психология+общения+лекция"),
        ],
    },
    "intellectual": {
        "title": "📚 Интеллектуал",
        "items": [
            ("«Думай медленно... решай быстро» — Даниэль Канеман", "https://www.litres.ru/deniel-kaneman/dumay-medlenno-reshay-bystro/"),
            ("«Атомные привычки» — Джеймс Клир", "https://www.litres.ru/dzheyms-kli-r/atomnye-privychki/"),
            ("«Гении и аутсайдеры» — Малкольм Гладуэлл", "https://www.litres.ru/malkolm-gladuell/genii-i-autsaydery/"),
            ("Лекция «Как развить интеллект» — Курс на YouTube", "https://www.youtube.com/results?search_query=как+развить+интеллект+лекция"),
        ],
    },
    "history": {
        "title": "🌍 История мира",
        "items": [
            ("«Sapiens. Краткая история человечества» — Юваль Ной Харари", "https://www.litres.ru/uval-noy-harari/sapiens-kratkaya-istoriya-chelovechestva/"),
            ("«История цивилизаций» — Арнольд Тойнби", "https://www.litres.ru/arnold-toynbi/istoriya-civilizaciy/"),
            ("«Война и мир» — Лев Толстой (исторический контекст)", "https://www.litres.ru/lev-tolstoy/voyna-i-mir/"),
            ("Лекция «История мира» — Курс на YouTube", "https://www.youtube.com/results?search_query=история+мира+лекция"),
        ],
    },
}


def _is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    if not ADMIN_ID:
        return False
    try:
        return str(user_id) == ADMIN_ID
    except (ValueError, TypeError):
        return False


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start: регистрирует пользователя и показывает меню."""
    user = message.from_user
    db.register_user(user.id, user.username, user.first_name, user.last_name)
    db.save_message(user.id, user.username, "/start")

    await message.answer(
        f"Привет, {user.first_name}! 👋\n"
        "Этот бот поможет вам развиваться и становиться умнее и успешнее.\n\n"
        "Выберите вектор развития навыков:",
        reply_markup=main_menu,
    )


@dp.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обработчик команды /menu: показывает главное меню."""
    user = message.from_user
    db.save_message(user.id, user.username, "/menu")
    await message.answer("Главное меню:", reply_markup=main_menu)


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Обработчик команды /stats: статистика для администратора."""
    user = message.from_user
    db.save_message(user.id, user.username, "/stats")

    if not _is_admin(user.id):
        await message.answer("⛔ У вас нет доступа к статистике.")
        return

    users = db.get_all_users()
    messages = db.get_all_messages()
    unique_count = db.get_unique_users_count()

    # Список пользователей
    users_text = "\n".join(
        f"• {u['user_id']} | @{u['username'] or 'нет'} | {u['first_name'] or ''} {u['last_name'] or ''}"
        for u in users
    ) or "Нет пользователей"

    # Список сообщений
    messages_text = "\n".join(
        f"• @{m['username'] or m['user_id']}: {m['text']}"
        for m in messages
    ) or "Нет сообщений"

    await message.answer(
        f"📊 **Статистика**\n\n"
        f"👥 Уникальных пользователей: **{unique_count}**\n\n"
        f"**Пользователи:**\n{users_text}\n\n"
        f"**Сообщения:**\n{messages_text}"
    )


@dp.message(F.text == "🧠 Психология общения")
async def show_psychology(message: Message) -> None:
    """Кнопка «Психология общения»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "psychology")


@dp.message(F.text == "📚 Интеллектуал")
async def show_intellectual(message: Message) -> None:
    """Кнопка «Интеллектуал»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "intellectual")


@dp.message(F.text == "🌍 История мира")
async def show_history(message: Message) -> None:
    """Кнопка «История мира»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "history")


async def _show_content(message: Message, key: str) -> None:
    """Показывает список ссылок для выбранного вектора развития."""
    content = CONTENT[key]
    lines = [f"**{content['title']}**\n", "Рекомендуемые материалы:"]
    for i, (title, url) in enumerate(content["items"], 1):
        lines.append(f"{i}. {title}\n   {url}")
    lines.append("\nВыберите другой вектор или вернитесь в меню:")
    await message.answer("\n".join(lines), reply_markup=main_menu)


@dp.message(F.text)
async def unknown_message(message: Message) -> None:
    """Обработчик любых других текстовых сообщений."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await message.answer(
        "Я не понял ваше сообщение. 😊\n"
        "Воспользуйтесь кнопками меню ниже:",
        reply_markup=main_menu,
    )


async def main() -> None:
    """Точка входа: запуск поллинга."""
    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())