from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

undermenu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Связаться с администрацией")],
        [KeyboardButton(text="📋 Меню")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

main_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Домашняя страница", callback_data="home_page")],
        [InlineKeyboardButton(text="📩 Сообщить о проблеме", callback_data="report_problem")],
        [InlineKeyboardButton(text="🛟 Поддержка", callback_data="support")],
    ]
)

home_page_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
)

FAQ_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="faq")],
        [InlineKeyboardButton(text="🛜 Как подключиться к VPN", callback_data="connect_to_vpn")],
        [InlineKeyboardButton(text="🚀 Измерение скорости", callback_data="speedtest")],
        [InlineKeyboardButton(text="🚧 Обнаружение проблем", callback_data="troubleshooting")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
)