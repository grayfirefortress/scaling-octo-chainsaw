import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан. Укажите его в файле .env")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Меню с кнопками ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎯 Цель бота")],
        [KeyboardButton(text="ℹ️ О боте")],
        [KeyboardButton(text="📞 Контакты")],
    ],
    resize_keyboard=True,
)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start: показывает главное меню."""
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я бот, созданный для помощи. Выберите пункт меню ниже:",
        reply_markup=main_menu,
    )


@dp.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обработчик команды /menu: показывает главное меню."""
    await message.answer("Главное меню:", reply_markup=main_menu)


@dp.message(F.text == "🎯 Цель бота")
async def show_goal(message: Message) -> None:
    """Кнопка «Цель бота»: рассказывает о цели бота."""
    await message.answer(
        "🎯 **Цель бота**\n\n"
        "Этот бот создан, чтобы помогать пользователям:\n"
        "• Отвечать на вопросы и давать полезную информацию\n"
        "• Ориентировать в возможностях и функциях\n"
        "• Быть удобным помощником в повседневных задачах\n\n"
        "Главная цель — сделать взаимодействие простым и полезным!",
        reply_markup=main_menu,
    )


@dp.message(F.text == "ℹ️ О боте")
async def show_about(message: Message) -> None:
    """Кнопка «О боте»: рассказывает о боте."""
    await message.answer(
        "ℹ️ **О боте**\n\n"
        "Я — Telegram-бот, написанный на Python с использованием "
        "фреймворка aiogram 3.\n"
        "Моя задача — помогать вам и отвечать на запросы.",
        reply_markup=main_menu,
    )


@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: Message) -> None:
    """Кнопка «Контакты»: показывает контакты."""
    await message.answer(
        "📞 **Контакты**\n\n"
        "Если у вас есть вопросы или предложения, "
        "свяжитесь с нами:\n"
        "• Email: support@example.com\n"
        "• Telegram: @support_bot",
        reply_markup=main_menu,
    )


@dp.message(F.text)
async def unknown_message(message: Message) -> None:
    """Обработчик любых других текстовых сообщений."""
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