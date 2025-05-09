from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

payment_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🛠 Связаться с администрацией")]],
    resize_keyboard=True
)

main_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Домашняя страница")],
        [KeyboardButton(text="🛠 Сообщить о проблеме")],
        [KeyboardButton(text="⏳ Изменить срок оплаты")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)
