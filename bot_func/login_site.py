import requests
from bs4 import BeautifulSoup as BS
from .database import create_connect
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
import asyncio
from datetime import datetime

ADMIN_ID = [1686807479, 6194484795]

# Xabarlarni bo'lib yuborish funksiyasi
async def send_large_message(context, chat_id, text, max_length=4096):
    for i in range(0, len(text), max_length):
        await context.bot.send_message(chat_id=chat_id, text=text[i:i+max_length], parse_mode="HTML")



# Barcha jadvallar ro'yxatini inline tugmalar bilan ko'rsatish
async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_connection = create_connect()
    cursor = db_connection.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    keyboard = []
    for table in tables:
        table_name = table[0]
        keyboard.append([InlineKeyboardButton(text=table_name, callback_data=table_name)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Iltimos, jadvalni tanlang:", reply_markup=reply_markup)



# Inline tugmalar uchun funktsiya
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("Hozir login qilish", callback_data='login_now')],
        [InlineKeyboardButton("haftalik loginni boshlash", callback_data='start_daily_login')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Foydalanuvchilarga eMaktab loginini tekshirish funksiyasi
def login_site(login, password):
    data = {"login": login, "password": password}
    req = requests.post("https://login.emaktab.uz", data=data)
    soup = BS(req.text, "html.parser")
    print(soup.title.text)
    return soup.title.text

# Kirish turini tanlash
async def table_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    table_name = query.data
    context.user_data['table_name'] = table_name
        
    await query.edit_message_text(f"{table_name} jadvalini tanladingiz. Kirish turini tanlang:", reply_markup=get_admin_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(text="Haftalik loginni boshlaymiz. Haftasiga necha marta tekshirishni xohlaysiz?")
    return "ASK_INTERVAL"

# Admin tomonidan kiritilgan miqdorni olish
async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        checks_per_day = int(update.message.text)  # Admin kiritgan miqdor
        if checks_per_day <= 0:
            await update.message.reply_text("Son noldan katta bo'lishi kerak.")
            return "ASK_INTERVAL"

        interval_hours = 168 // checks_per_day  # 24 soatni kiritilgan soniga bo'lib, intervalni topamiz
        await update.message.reply_text(f"Har {interval_hours} soatda foydalanuvchilar tekshiriladi.\nHozir ham tekshirish boshlangan")
        context.application.create_task(schedule_checks(context, interval_hours))
        
        return ConversationHandler.END  # Conversatsiyani yakunlaymiz
    except ValueError:
        await update.message.reply_text("Iltimos, son kiriting.")
        return "ASK_INTERVAL"


# Kunlik tekshiruv funksiyasi
async def schedule_checks(context: ContextTypes.DEFAULT_TYPE, interval_hours: int) -> None:
    while True:
        table_name = context.user_data['table_name']
        await check_logins(context, table_name)
        await asyncio.sleep(interval_hours * 3600)


async def check_logins(context: ContextTypes.DEFAULT_TYPE, table_name):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute(f"SELECT login, parol FROM {table_name}")
    users = cursor.fetchall()   
    total_user = 0
    error_messages = []

    for user in users:
        login, password = user
        result = login_site(login, password)
        if "Yangiliklar tasmasi" in result or "Лента новостей" in result or "Янгиликлар тасмаси" in result:
            print("Muvaffaqiyatli")
        else:
            total_user += 1
            error_messages.append(f"{total_user}) login: {login}, parol: {password}")

    if error_messages:
        error_text = "XATOLIKLAR:\n\n" + "\n".join(error_messages)
        for admin_id in ADMIN_ID:
            try:
                await send_large_message(context, admin_id, error_text)  # Xabarni bo'lib yuborish
            except Exception as e:
                print(e)

    if total_user == 0:
        for admin_id in ADMIN_ID:
            await context.bot.send_message(chat_id=admin_id, text="Barcha login muvaffaqiyatli amalga oshirildi.")
    else:
        print(f'{total_user}ta loginda xatolik')

