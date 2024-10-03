import requests
from bs4 import BeautifulSoup as BS
from telegram.ext import ContextTypes
from datetime import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from .database import create_connect
from telegram.error import TelegramError

ADMIN_ID = [1686807479, 6194484795]

# Har kuni 00:00 va 12:00 da ishga tushadigan funksiya
async def schedule_checks(context: ContextTypes.DEFAULT_TYPE) -> None:
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == "00:00" or now == "12:00":
            await check_logins(context)
        await asyncio.sleep(60)  # time.sleep o'rniga asyncio.sleep

# Foydalanuvchilarga eMaktab loginini tekshirish funksiyasi
def login_site(login, password):
    data = {"login": login, "password": password}
    req = requests.post("https://login.emaktab.uz", data=data)
    soup = BS(req.text, "html.parser")
    print(soup.title.text)
    return soup.title.text

async def check_logins(context: ContextTypes.DEFAULT_TYPE, table_name, times):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute(f"SELECT login, parol FROM {table_name}")
    users = cursor.fetchall()   
    total_user = 0

    for _ in range(times):  # Necha marta kirishni admin belgilaydi
        for user in users:
            login, password = user
            result = login_site(login, password)
            if "Yangiliklar tasmasi" in result or "Лента новостей" in result or "Янгиликлар тасмаси" in result:
                print("Muvaffaqiyatli")
            else:
                print('Xato')
                total_user += 1
                for i in ADMIN_ID:
                    try:
                        await context.bot.send_message(chat_id=i, text=f"ADMIN <code>{login}</code> loginida xatolik \n\nParoli: <code>{password}</code>", parse_mode="HTML")
                    except Exception as e:
                        print(e)
    
    for i in ADMIN_ID:
        await context.bot.send_message(chat_id=i, text=f'{total_user}ta loginda xatolik')

    print(f'{total_user}ta loginda xatolik')


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

# Kirish turini tanlash
async def table_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    table_name = query.data
    context.user_data['table_name'] = table_name
    
    keyboard = [
        [InlineKeyboardButton(text="Kunlik", callback_data="daily"),
         InlineKeyboardButton(text="Haftalik", callback_data="weekly")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_message_text(f"{table_name} jadvalini tanladingiz. Kirish turini tanlang:", reply_markup=reply_markup)

# Kirish turiga qarab so'rovni shakllantirish
async def login_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    login_type = query.data
    
    context.user_data['login_type'] = login_type
    
    if login_type == "daily":
        await query.message.edit_message_text("Kunlik kirish sonini kiriting (Misol: 2):")
    elif login_type == "weekly":
        await query.message.edit_message_text("Haftalik kirish sonini kiriting (Misol: 2):")

# Admin tomonidan sonni kiritish
async def receive_login_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    times = int(update.message.text)  # Admin kiritgan butun son
    table_name = context.user_data['table_name']
    login_type = context.user_data['login_type']
    
    if login_type == "daily":
        await update.message.reply_text(f"Kunlik {times} marta kirishni boshlaymiz.")
    elif login_type == "weekly":
        await update.message.reply_text(f"Haftalik {times} marta kirishni boshlaymiz.")
    
    # Tanlangan jadval va kirish marotabalarini yuborish
    await check_logins(context, table_name, times)
