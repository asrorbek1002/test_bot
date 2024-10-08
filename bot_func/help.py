from telegram import Update
from telegram.ext import ContextTypes

# /help komanda - botdan foydalanish bo'yicha ko'rsatma beradi
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Botning komandalar bo'yicha qo'llanmasi:*\n\n"
        "1. */start* - Botni boshlash va admin huquqini tasdiqlash.\n"
        "2. */add_login* - Excel faylini yuborib, login va parollarni bazaga qo'shish.\n"
        "3. */start_login* - Jadvallarni tanlab, foydalanuvchi logini tekshirish (kunlik yoki haftalik).\n"
        "4. */delete_table* - Mavjud jadvallarni o'chirish.\n"
        "5. */show_info* - Bazadagi barcha jadvallarni va ularning ichidagi ma'lumotlar sonini ko'rsatish.\n"
        "6. */help* - Ushbu yordam qo'llanmasini ko'rsatadi.\n\n"
        "Botni qanday ishlatishni oson tushunish uchun komandalarni to'g'ri kiriting va ko'rsatmalarga amal qiling."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")