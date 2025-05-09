# vpn-telegram-bot/bot/main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties
from aiogram.types.input_file import FSInputFile

from config import BOT_TOKEN, ADMIN_ID
from db import init_db, add_or_update_user, log_message, get_all_users, add_access_for_user, get_user_status
from keyboards import main_button, payment_button


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

init_db()

@dp.message(Command("start"))
async def start_handler(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or "unknown"
    # добавим в БД, если ещё нет
    add_or_update_user(telegram_id, username)

    is_active = get_user_status(telegram_id)  # True/False

    # Выбор клавиатуры
    keyboard = main_button if is_active else payment_button

    # Картинка
    photo = FSInputFile("media/welcome.jpg")

    await message.answer_photo(
        photo=photo,
        caption="👋 Добро пожаловать в VPN-сервис!\n Дальше идёт заглушка с объяснением оплаты и прочим. Пока текст я не придумал :(",
        reply_markup=keyboard
    )


@dp.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer(f"У тебя нет прав для этой команды. \n{message.from_user.id}")

    text = message.text.removeprefix("/broadcast").strip()
    if not text:
        return await message.answer("Укажи текст рассылки после команды.")

    users = get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, f"<b>Объявление:</b>\n{text}")
            count += 1
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение {user_id}: {e}")
    await message.answer(f"Сообщение отправлено {count} пользователям.")

@dp.message(F.text.startswith("/addaccess"))
async def add_access_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для этой команды.")
        return

    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /addaccess @username vpn_ключ")
        return

    username = parts[1].lstrip("@")
    vpn_key = parts[2]

    try:
        telegram_id = add_access_for_user(username)

        if telegram_id is None:
            await message.answer(f"⚠️ Пользователь @{username} ещё не писал боту. Попроси его сначала отправить любое сообщение.")
            return

        await bot.send_message(telegram_id, f"✅ Вам выдан доступ к VPN!\nВот ваш ключ: <code>{vpn_key}</code>", parse_mode="HTML")
        await message.answer(f"Пользователь @{username} получил доступ.")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

@dp.message(F.photo)
async def handle_photo_receipt(message: Message):
    add_or_update_user(message.from_user.id, message.from_user.username)
    log_message(message.from_user.id, f"Photo: {message.photo[-1].file_id}")
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo=message.photo[-1].file_id,
            caption=f"<b>Фото-чек от пользователя:</b> @{message.from_user.username}"
        )
        await message.answer("Фото чека отправлено админу. Ожидайте подтверждения.")
    except Exception as e:
        logging.error(f"Ошибка при отправке фото админу: {e}")
        await message.answer("Произошла ошибка при отправке фото. Попробуйте позже.")

@dp.message(F.text)
async def handle_text_receipt(message: Message):
    add_or_update_user(message.from_user.id, message.from_user.username)
    log_message(message.from_user.id, message.text)
    try:
        await bot.send_message(
            ADMIN_ID,
            f"<b>Чек от пользователя:</b> @{message.from_user.username}\n<pre>{message.text}</pre>"
        )
        await message.answer("Чек отправлен админу. Ожидайте подтверждения.")
    except Exception as e:
        logging.error(f"Ошибка при отправке админу: {e}")
        await message.answer("Произошла ошибка при отправке чека. Попробуйте позже.")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
