# vpn-telegram-bot/bot/main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandObject
from aiogram.types.input_file import FSInputFile

from config import BOT_TOKEN, ADMIN_ID
from db import init_db, add_or_update_user, log_message, get_all_users, add_access_for_user, get_user_status, get_user_by_username, get_user_info
from keyboards import main_button, payment_button


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

init_db()

@dp.message(Command("start"))
async def start_handler(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or "unknown"
    add_or_update_user(telegram_id, username)

    is_active = get_user_status(telegram_id)  # True/False
    keyboard = main_button if is_active else payment_button

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

@dp.message(Command("addaccess"))
async def cmd_add_access(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("У тебя нет прав на эту команду.")

    if not command.args:
        return await message.answer("Используй: /addaccess @username ключ")

    try:
        parts = command.args.split()
        if len(parts) < 2:
            return await message.answer("Формат: /addaccess @username ключ")

        username_part = parts[0]
        key = " ".join(parts[1:])

        username = username_part.lstrip('@')
        user = get_user_by_username(username)

        if not user:
            return await message.answer(f"Пользователь @{username} не найден в базе.")

        telegram_id = user["telegram_id"]

        add_access_for_user(telegram_id, key)

        await bot.send_message(
            chat_id=telegram_id,
            text=f"✅ Оплата подтверждена!\nВот твой ключ от VPN:\n\n<code>{key}</code>",
            parse_mode=ParseMode.HTML,
        )

        await bot.send_message(
            chat_id=telegram_id,
            text="Выбери нужный раздел:",
            reply_markup=main_button
        )

        await message.answer(f"Доступ выдан пользователю @{username}")

    except Exception as e:
        await message.answer(f"Ошибка: {e}")


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
