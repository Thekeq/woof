import asyncio
import random
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from db import DataBase  # Подключение к вашей базе данных
import os
from dotenv import load_dotenv

load_dotenv()
# Замените на ваш токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Замените на ваш URL
WEB_APP_URL = os.getenv("WEB_APP_URL")

# Настройка бота и маршрутов
bot = Bot(BOT_TOKEN, parse_mode="HTML")
router = Router()
# Получаем абсолютный путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")

# Инициализируем базу данных
db = DataBase(DB_PATH)


def webapp_builder():
    """Создаем клавиатуру с Web App."""
    web_app_info = InlineKeyboardButton(text="WOOFS", web_app={"url": WEB_APP_URL})
    markup = InlineKeyboardMarkup(inline_keyboard=[[web_app_info]])
    return markup


@router.message(CommandStart())
async def start(message: Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.full_name
    markup = webapp_builder()

    if not db.user_exists(user_id):  # Регистрация пользователя
        start_command = message.text
        referrer_id = str(start_command[7:])

        if str(referrer_id) != "":
            if str(referrer_id) != str(user_id):
                db.add_user(user_id, username, referrer_id)
                # Вычисляем бонус
                amount = (
                    random.randint(15000, 20000) if user_id < 100000000 else
                    random.randint(10000, 15000) if user_id < 1000000000 else
                    random.randint(5000, 10000) if user_id < 8000000000 else
                    random.randint(2500, 5000)
                )
                db.add_balance(user_id, amount)

                # Обновляем rewards
                rewards = db.get_rewards(user_id)  # Получаем текущие rewards как словарь
                rewards["Age"] = amount  # Добавляем или обновляем запись "Age"
                db.update_rewards(user_id, rewards)

                # Добавляем приветственный бонус
                db.add_balance(user_id, 5000)
                rewards["Welcome"] = 5000  # Добавляем или обновляем запись "Welcome"
                db.update_rewards(user_id, rewards)

                # Обновляем данные реферера
                try:
                    db.add_balance(referrer_id, round(amount * 0.15))
                    db.add_frens_count(referrer_id)
                    db.add_friend(referrer_id, username)
                    db.add_friend_id(referrer_id, user_id)
                except Exception as e:
                    print(e)
            else:
                await bot.send_message(user_id, "You cannot register with your referral link.")
        else:
            db.add_user(user_id, username)
            # Вычисляем бонус
            amount = (
                random.randint(15000, 20000) if user_id < 100000000 else
                random.randint(10000, 15000) if user_id < 1000000000 else
                random.randint(5000, 10000) if user_id < 8000000000 else
                random.randint(2500, 5000)
            )
            db.add_balance(user_id, amount)

            # Обновляем rewards
            rewards = db.get_rewards(user_id)  # Получаем текущие rewards как словарь
            rewards["Age"] = amount  # Добавляем или обновляем запись "Age"
            db.update_rewards(user_id, rewards)

            # Добавляем приветственный бонус
            db.add_balance(user_id, 5000)
            rewards["Welcome"] = 5000  # Добавляем или обновляем запись "Welcome"
            db.update_rewards(user_id, rewards)

    await message.answer(
        "Welcome to the WOOFS!",
        reply_markup=markup
    )


@router.message(Command("ad"))
async def ad(message: Message):
    user_id = message.from_user.id
    markup = webapp_builder()
    if user_id == 1076078800:
        chat_ids = db.get_all_users()
        tasks = [
            bot.send_message(
                chat_id=chat_id,
                text="Welcome to the WOOFS!",
                reply_markup=markup
            )
            for chat_id in chat_ids
        ]
        await asyncio.gather(*tasks)


async def main():
    """Основной метод запуска бота."""
    dp = Dispatcher()
    dp.include_router(router)
    print("Telegram Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
