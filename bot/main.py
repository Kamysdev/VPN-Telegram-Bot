# vpn-telegram-bot/bot/main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandObject
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.context import FSMContext


from config import BOT_TOKEN, ADMIN_ID
from db import init_db, add_or_update_user, log_message, get_all_users, add_access_for_user, get_user_status, get_user_by_username, get_user_info
from keyboards import main_button, home_page_button, undermenu_keyboard, FAQ_button
from states import ContactAdminStates

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
    keyboard = main_button if is_active else undermenu_keyboard

    photo = FSInputFile("media/welcome.jpg")
    await message.answer_photo(
        photo=photo,
        caption="👋 Добро пожаловать в VPN-сервис!\n Дальше идёт заглушка с объяснением оплаты и прочим. Пока текст я не придумал :(",
        reply_markup=undermenu_keyboard
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


## Домашняя страница (с ключом ВПН)
@dp.callback_query(lambda c: c.data == "home_page")
async def show_home_page(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    info = get_user_info(telegram_id)

    if info:
        msg = (
            f"🏠 *Домашняя страница*\n\n"
            f"🔑 Ваш VPN ключ: `{info['vpn_key']}`\n"
            f"📅 Оплачено до: *{info['payment_due'].strftime('%d.%m.%Y')}*"
        )
    else:
        msg = "Данные не найдены. Обратитесь к администратору."
    

    await callback.message.edit_text(msg, reply_markup=home_page_button, parse_mode="Markdown")
    await callback.answer()


## Быстрый репорт проблемы
@dp.callback_query(lambda c: c.data == "report_problem")
async def report_issue(callback: CallbackQuery):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"

    await bot.send_message(
        ADMIN_ID,
        f"⚠️ Пользователь {username} сообщил о проблеме с подключением."
    )

    await callback.message.edit_text("🛠 Спасибо, проблема передана. Мы постараемся исправить неполадки как можно скорее! 🤗", reply_markup=home_page_button, parse_mode="Markdown")
    await callback.answer()


## Возврат в меню
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    is_active = get_user_status(telegram_id)

    keyboard = main_button if is_active else undermenu_keyboard

    await callback.message.edit_text("👋 Добро пожаловать в VPN-сервис!\nВыберите действие из меню ниже:", reply_markup=keyboard)
    await callback.answer()


## Инлайн меню
@dp.message(F.text == "📋 Меню")
async def handle_reply_menu(message: Message):
    telegram_id = message.from_user.id
    is_active = get_user_status(telegram_id)
    keyboard = main_button if is_active else undermenu_keyboard

    if is_active:
        await message.answer("👋 Добро пожаловать в VPN-сервис!\nВыберите действие из меню ниже:", reply_markup=keyboard)


## Сообщение об ошибке
@dp.message(F.text == "🛠 Связаться с администрацией")
async def contact_admin_button_pressed(message: Message, state: FSMContext):
    await message.answer("✏️ Пожалуйста, опишите вашу проблему или вопрос. Мы передадим всё нашей технической подержке.")
    await state.set_state(ContactAdminStates.waiting_for_message)

@dp.message(ContactAdminStates.waiting_for_message)
async def handle_admin_message(message: Message, state: FSMContext):
    user = message.from_user
    text = (
        f"📨 Новое обращение от пользователя @{user.username or 'unknown'} (ID: {user.id}):\n\n"
        f"{message.text}"
    )
    await bot.send_message(ADMIN_ID, text)
    await message.answer("✅ Ваше сообщение отправлено администратору. Спасибо!")
    await state.clear()


## Обработчик чеков. Оставить последней функцией в этом файле
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

# @dp.message(F.text)
# async def handle_text_receipt(message: Message):
#     add_or_update_user(message.from_user.id, message.from_user.username)
#     log_message(message.from_user.id, message.text)
#     try:
#         await bot.send_message(
#             ADMIN_ID,
#             f"<b>Чек от пользователя:</b> @{message.from_user.username}\n<pre>{message.text}</pre>"
#         )
#         await message.answer("Чек отправлен админу. Ожидайте подтверждения.")
#     except Exception as e:
#         logging.error(f"Ошибка при отправке админу: {e}")
#         await message.answer("Произошла ошибка при отправке чека. Попробуйте позже.")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
