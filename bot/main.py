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
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta


from config import BOT_TOKEN, ADMIN_ID
from db import init_db, add_or_update_user, log_message, get_all_users, add_access_for_user, get_user_status, get_user_by_username, get_user_info, get_all_users_with_due_date, extend_payment_by_telegram_id
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
        caption="👋 Добро пожаловать в Интернет-сервис!\n Для оплаты вам необходимо перевести 110Р по номеру телефона <code>8-983-251-67-44</code> Сбербанк (Константин Андревич С), после чего предоставить скиншот оплаты в этот чат (только изображение). Администратор обработает ваше обращение  предоставит доступ",
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

@dp.message(Command("extend"))
async def handle_extend_by_username(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 У вас нет прав на выполнение этой команды.")
        return

    args = message.text.strip().split()
    if len(args) != 2 or not args[1].startswith("@"):
        await message.answer("❗ Использование: /extend @username")
        return

    username = args[1][1:]  # убираем "@"

    user = get_user_by_username(username)
    if not user:
        await message.answer(f"❌ Пользователь с именем @{username} не найден.")
        return

    try:
        extend_payment_by_telegram_id(user['telegram_id'])
        await message.answer(f"✅ Подписка пользователя @{username} продлена на месяц.")
        await bot.send_message(user['telegram_id'], "🎉 Ваш доступ к VPN продлён ещё на месяц!")
    except Exception as e:
        logging.error(f"Ошибка при продлении подписки @{username}: {e}")
        await message.answer("🚫 Произошла ошибка при продлении доступа.")

## Test build
@dp.message(Command("test_notify"))
async def test_notify(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer(f"У тебя нет прав для этой команды. \n{message.from_user.id}")
    await message.answer("🔔 Проверка уведомлений запущена.")
    await check_payment_reminders(bot)  # Функция рассылки

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

## Поддержка
@dp.callback_query(lambda c: c.data == "support")
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text("🛟 Выберите действие:", reply_markup=FAQ_button)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "faq")
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text("A. Это безопасный VPN? " \
    "\nБ. Абсолютно! Сервера находятся в Европе, а подключение происходит с использованием современных протоколов", reply_markup=home_page_button)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "connect_to_vpn")
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text("Используйте Outline или AmneziaVPN", reply_markup=home_page_button)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "speedtest")
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text("🛸 speedtest.net", reply_markup=home_page_button)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "troubleshooting")
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text("Сперва проверьте скорость соединения без подключенного VPN. Если скорость с включенным VPN в 2-2.5 раза меньше, чем без него, то всё в пределах нормы", reply_markup=home_page_button)
    await callback.answer()


## Обработчик чеков. Оставить последней функцией в этом файле
@dp.message(F.photo)
async def handle_photo_receipt(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    # Добавляем или обновляем пользователя в БД
    add_or_update_user(telegram_id, username)

    # Проверка активности
    is_active = get_user_status(telegram_id)

    # Логируем
    log_message(telegram_id, f"Photo: {message.photo[-1].file_id}")

    # Подготовка данных
    photo_file_id = message.photo[-1].file_id

    # Формируем подписи в зависимости от статуса
    if is_active:
        admin_caption = f"📤 Продление VPN от пользователя @{username} (id: {telegram_id})"
        user_response = "✅ Ваш чек на продление отправлен админу. Обычно это занимает немного времени."
    else:
        admin_caption = f"🆕 Первая оплата от пользователя @{username} (id: {telegram_id})"
        user_response = "✅ Ваш чек отправлен. Мы проверим его и активируем доступ."

    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=admin_caption
        )
        await message.answer(user_response)
    except Exception as e:
        logging.error(f"Ошибка при отправке фото админу: {e}")
        await message.answer("🚫 Произошла ошибка при отправке фото. Попробуйте позже.")


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


## Напоминалка
async def check_payment_reminders(bot: Bot):
    while True:
        users_to_notify = get_all_users_with_due_date(3)

        if not users_to_notify:
            await bot.send_message(
                ADMIN_ID,
                "✅ Сегодня нет пользователей, которым нужно напомнить о платеже."
            )
        else:
            report_lines = [f"🔔 Напоминания отправлены {len(users_to_notify)} пользователям:"]
            for user in users_to_notify:
                report_lines.append(f"➡️ ID: {user['telegram_id']} | До: {user['payment_due']}")

                await bot.send_message(
                    user['telegram_id'],
                    f"🔔 Напоминаем: срок действия вашей VPN-подписки заканчивается {user['payment_due']}.\nПожалуйста, оплатите, чтобы избежать отключения. Для оплаты переведите на номер <code>8-983-251-67-44</code> Сбербанк (Константин Андреевич С) и отправте скриншот оплаты в чат"
                )

            await bot.send_message(
                ADMIN_ID,
                "\n".join(report_lines)
            )

        await asyncio.sleep(86400)  # повтор каждые 24 часа

async def on_startup(bot: Bot):
    asyncio.create_task(check_payment_reminders(bot))

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())