import os
import pandas as pd
from bot_func.help import help_command
from telegram import Update
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, 
                          ConversationHandler, ContextTypes, CallbackQueryHandler)
from bot_func.database import create_connect
from bot_func.login_site import start_login, button_handler, set_interval, check_logins, table_selected
from bot_func.delete_tab import delete_table_confirmation, confirm_delete_table, start_delete_table, cancel_delete

ADMIN_ID = [1686807479, 6194484795]

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in ADMIN_ID:
        await update.message.reply_text("Salom, admin! Sizga qanday yordam bera olishim mumkin?")
    else:
        await update.message.reply_text("Sizda bu botdan foydalanish huquqi yo'q.")

# SQLite bazasini yaratish yoki ochish
def create_db():
    db_connection = create_connect()
    db_connection.close()

# Excel faylini o'qish va ma'lumotlarni bazaga kiritish
def insert_data_from_excel(excel_file_path, table_name):
    try:
        data = pd.read_excel(excel_file_path)
        
        db_connection = create_connect()
        cursor = db_connection.cursor()

        # Jadvalni yaratish
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                login TEXT,
                parol TEXT
            )
        ''')
        
        for index, row in data.iterrows():
            query = f"INSERT INTO {table_name} (login, parol) VALUES (?, ?)"
            values = tuple(row)  # Assuming columns match order and names
            cursor.execute(query, values)

        db_connection.commit()  # Commit changes
    except Exception as e:
        print(f"Xato: {e}")  # Logging xatolar
    finally:
        db_connection.close()  # Close the connection

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_info = await update.message.document.get_file()
        await file_info.download_to_drive('received_file.xlsx')

        # Jadval nomini fayldan olish
        table_name = 'users_' + os.path.splitext(update.message.document.file_name)[0]

        insert_data_from_excel('received_file.xlsx', table_name)
        os.remove('received_file.xlsx')  # Faylni o'chirish

        await update.message.reply_text(f"Ma'lumotlar {table_name} jadvaliga muvaffaqiyatli qo'shildi.")
    else:
        await update.message.reply_text("Iltimos, Excel faylini jo'nating.")

# Barcha jadvallar va ma'lumotlar haqida ma'lumot ko'rsatish
async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_connection = create_connect()
    cursor = db_connection.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    response = "Jadvallar:\n"
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        response += f"Jadval: {table_name}, Ma'lumotlar soni: {count}\n"

    db_connection.close()
    await update.message.reply_text(response)



# Bekor qilish funksiyasi
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Jarayon bekor qilindi.")
    return ConversationHandler.END

# Botni ishga tushirish
async def start_add_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Excel faylini jo'nating!")

# Admin panelidagi callbacklar uchun funksiya
async def inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    table_name = context.user_data['table_name']
    if query.data == 'login_now':
        await query.edit_message_text(text="Kirishni boshladim bu bir necha daqiqa vaqt oladi. Iltimos kuting...")
        await check_logins(context, table_name)
        await query.edit_message_text(text="Barcha foydalanuvchilar hozir tekshirildi.")


# Botni ishga tushirish
def main():
    create_db()
    # Bot tokenini shu yerga kiriting
    TOKEN = "7506530510:AAEVJwbfUJkwWKV5CxLSIgUtOph9N0niwRs"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("show_info", show_info))

    # Boshqa komandalar va handlerlarni ro'yxatdan o'tkazish
    application.add_handler(CommandHandler("add_login", start_add_db))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start_login', start_login))
    # Inline tugmalar bilan ishlash
    application.add_handler(CallbackQueryHandler(table_selected, pattern='^users_'))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='start_daily_login')],
        states={
            "ASK_INTERVAL": [MessageHandler(filters.TEXT & ~filters.COMMAND, set_interval)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('delete_table', start_delete_table))  # Jadvalni o'chirish komandasi
    
    # Inline tugmalar bilan ishlash
    application.add_handler(CallbackQueryHandler(table_selected, pattern='^users_'))
    application.add_handler(CallbackQueryHandler(delete_table_confirmation, pattern='^delete_'))
    application.add_handler(CallbackQueryHandler(confirm_delete_table, pattern='^confirm_delete_'))
    application.add_handler(CallbackQueryHandler(cancel_delete, pattern='cancel_delete'))
    application.add_handler(CallbackQueryHandler(inline_button))

    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Botni ishga tushirish
    application.run_polling()

if __name__ == '__main__':
    main()
