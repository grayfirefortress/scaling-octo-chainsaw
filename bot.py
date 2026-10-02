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

# --- Информация о боте ---
ABOUT_TEXT = (
    "🌟 Репликация\n\n"
    "Это проект, который соединяет в себе всё, что нужно современному человеку.\n\n"
    "🎁 Что тебе может дать этот бот:\n"
    "• 📚 Подборку книг и лекций по разным направлениям развития\n"
    "• 🧠 Развитие интеллекта и навыков общения\n"
    "• 💪 Инструменты для трансформации тела и здоровья\n"
    "• 🏛️ Философию стоицизма для устойчивости и спокойствия\n"
    "• 🌍 Глубокое понимание истории мира\n\n"
    "Выберите, что вы хотите изучить:"
)

# --- Главное меню ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌍 История")],
        [KeyboardButton(text="🧠 Психология общения")],
        [KeyboardButton(text="💪 Трансформация тела")],
        [KeyboardButton(text="🏛️ Стоический образ жизни")],
    ],
    resize_keyboard=True,
)

# --- Контент по векторам развития ---
CONTENT = {
    "history": {
        "title": "🌍 История",
        "items": [
            ("«Sapiens. Краткая история человечества» — Юваль Ной Харари", "https://www.litres.ru/uval-noy-harari/sapiens-kratkaya-istoriya-chelovechestva/"),
            ("«История цивилизаций» — Арнольд Тойнби", "https://www.litres.ru/arnold-toynbi/istoriya-civilizaciy/"),
            ("«Война и мир» — Лев Толстой (исторический контекст)", "https://www.litres.ru/lev-tolstoy/voyna-i-mir/"),
            ("Лекция «История мира» — Курс на YouTube", "https://www.youtube.com/results?search_query=история+мира+лекция"),
        ],
    },
    "psychology": {
        "title": "🧠 Психология общения",
        "items": [
            ("«Как завоёвывать друзей и оказывать влияние на людей» — Дейл Карнеги", "https://www.litres.ru/deyl-karnegi/kak-zavoevyvat-druzey-i-okazyvat-vliyanie-na-ludey/"),
            ("«Язык телодвижений» — Аллан Пиз", "https://www.litres.ru/allan-piz/yazyk-telodvizheniy/"),
            ("«Тонкое искусство пофигизма» — Марк Мэнсон", "https://www.litres.ru/mark-menson/tonkoe-iskusstvo-pofigizma/"),
            ("Лекция «Психология общения» — Курс на YouTube", "https://www.youtube.com/results?search_query=психология+общения+лекция"),
        ],
    },
    "body": {
        "title": "💪 Трансформация тела",
        "items": [
            ("«Анатомия силовых упражнений» — Фредерик Делавье", "https://www.litres.ru/frederik-delave/anatomiya-silovyh-uprazhneniy/"),
            ("«Стройность и сила» — руководство по фитнесу", "https://www.litres.ru/"),
            ("«Питание для набора мышечной массы» — гайд", "https://www.litres.ru/"),
            ("Лекция «Трансформация тела» — Курс на YouTube", "https://www.youtube.com/results?search_query=трансформация+тела+лекция"),
        ],
    },
    "stoicism": {
        "title": "🏛️ Стоический образ жизни",
        "items": [
            ("«Размышления» — Марк Аврелий", "https://www.litres.ru/mark-avreliy/razmyshleniya/"),
            ("«Письма к Луцилию» — Сенека", "https://www.litres.ru/luciy-anney-seneka/pisma-k-luciliu/"),
            ("«Энхиридион» — Эпиктет", "https://www.litres.ru/epiktet/enhiridion/"),
            ("Лекция «Стоицизм» — Курс на YouTube", "https://www.youtube.com/results?search_query=стоицизм+лекция"),
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
    """Обработчик команды /start: регистрирует пользователя, показывает инфо и меню."""
    user = message.from_user
    db.register_user(user.id, user.username, user.first_name, user.last_name)
    db.save_message(user.id, user.username, "/start")

    await message.answer(
        f"Привет, {user.first_name}! 👋\n\n{ABOUT_TEXT}",
        reply_markup=main_menu,
    )


@dp.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обработчик команды /menu: показывает главное меню."""
    user = message.from_user
    db.save_message(user.id, user.username, "/menu")
    await message.answer(ABOUT_TEXT, reply_markup=main_menu)


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

    users_text = "\n".join(
        f"• {u['user_id']} | @{u['username'] or 'нет'} | {u['first_name'] or ''} {u['last_name'] or ''}"
        for u in users
    ) or "Нет пользователей"

    messages_text = "\n".join(
        f"• @{m['username'] or m['user_id']}: {m['text']}"
        for m in messages
    ) or "Нет сообщений"

    await message.answer(
        f"📊 Статистика\n\n"
        f"👥 Уникальных пользователей: {unique_count}\n\n"
        f"Пользователи:\n{users_text}\n\n"
        f"Сообщения:\n{messages_text}"
    )


@dp.message(F.text == "🌍 История")
async def show_history(message: Message) -> None:
    """Кнопка «История»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "history")


@dp.message(F.text == "🧠 Психология общения")
async def show_psychology(message: Message) -> None:
    """Кнопка «Психология общения»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "psychology")


@dp.message(F.text == "💪 Трансформация тела")
async def show_body(message: Message) -> None:
    """Кнопка «Трансформация тела»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "body")


@dp.message(F.text == "🏛️ Стоический образ жизни")
async def show_stoicism(message: Message) -> None:
    """Кнопка «Стоический образ жизни»."""
    user = message.from_user
    db.save_message(user.id, user.username, message.text)
    await _show_content(message, "stoicism")


async def _show_content(message: Message, key: str) -> None:
    """Показывает список ссылок для выбранного вектора развития."""
    content = CONTENT[key]
    lines = [f"{content['title']}\n", "Рекомендуемые материалы:"]
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
