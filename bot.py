import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
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


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я эхо-бот. Просто напиши мне что-нибудь, и я повторю."
    )


@dp.message(F.text)
async def echo(message: Message) -> None:
    """Эхо-ответ на любое текстовое сообщение."""
    await message.answer(message.text)


async def main() -> None:
    """Точка входа: запуск поллинга."""
    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())