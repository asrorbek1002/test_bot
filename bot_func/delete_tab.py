from .database import create_connect
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Barcha jadvallar ro'yxatini inline tugmalar bilan ko'rsatish (o'chirish uchun)
async def start_delete_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_connection = create_connect()
    cursor = db_connection.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    keyboard = []
    for table in tables:
        table_name = table[0]
        keyboard.append([InlineKeyboardButton(text=table_name, callback_data=f"delete_{table_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("O'chirish uchun jadvalni tanlang:", reply_markup=reply_markup)

# Jadvalni o'chirish uchun tasdiqlash funksiyasi
async def delete_table_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    table_name = query.data.replace("delete_", "")

    # Jadvalni o'chirish uchun tasdiqlash tugmasi
    keyboard = [
        [InlineKeyboardButton(text="Ha", callback_data=f"confirm_delete_{table_name}"),
         InlineKeyboardButton(text="Yo'q", callback_data="cancel_delete")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(f"Siz {table_name} jadvalini o'chirmoqchimisiz?", reply_markup=reply_markup)

# Jadvalni o'chirishni tasdiqlash
async def confirm_delete_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    table_name = query.data.replace("confirm_delete_", "")
    
    db_connection = create_connect()
    cursor = db_connection.cursor()
    
    try:
        cursor.execute(f"DROP TABLE {table_name}")
        db_connection.commit()
        await query.message.reply_text(f"{table_name} jadvali muvaffaqiyatli o'chirildi.")
        print(f"{table_name} jadvali o'chirildi.")
    except Exception as e:
        await query.message.reply_text(f"Xato yuz berdi: {e}")
    finally:
        db_connection.close()

# Jadvalni o'chirishni bekor qilish
async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Jadvalni o'chirish bekor qilindi.")
