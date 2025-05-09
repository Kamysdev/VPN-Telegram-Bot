from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

payment_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🛠 Связаться с администрацией")]],
    resize_keyboard=True
)

main_button = ReplyKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Домашняя страница", callback_data="home_page")],
        [InlineKeyboardButton(text="📩 Сообщить о проблеме", callback_data="report_problem")],
        [InlineKeyboardButton(text="📅 Изменить срок оплаты", callback_data="change_payment")],
        [InlineKeyboardButton(text="🛟 Поддержка", callback_data="support")],
    ]
)
