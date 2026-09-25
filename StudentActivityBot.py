import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import init_db, SessionLocal
from models import User

# ضع الـ Token الذي حصلت عليه من BotFather هنا
BOT_TOKEN = "8895052100:AAHSglL-iVro86AjX3FISRGN99aUA8YHqUQ"

# تهيئة قاعدة البيانات عند بدء تشغيل البوت
init_db()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# أمر /start عند فتح البوت من قبل الطالب أو الأدمن
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "طالب"
    
    db = SessionLocal()
    # التحقق مما إذا كان المستخدم مسجلاً من قبل
    db_user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not db_user:
        # إضافة المستخدم الجديد كـ طالب افتراضياً
        db_user = User(telegram_id=user_id, full_name=first_name, role="student")
        db.add(db_user)
        db.commit()
    
    # رابط الـ Web App (سنربطه بالـ Frontend لاحقاً)
    WEB_APP_URL = "https://ai-psi-olive-94.vercel.app/"

    keyboard = [[InlineKeyboardButton("فتح تطبيق النشاطات", web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"أهلاً بك يا {first_name} في بوت قسم هندسة تقنيات الذكاء الاصطناعي! 🚀\n\n"
        f"يمكنك عبر هذا البوت استعراض ورش ونشاطات القسم ورفع شهادات المشاركة للحصول على درجات النشاط.",
        reply_markup=reply_markup
    )
    db.close()

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("البوت يعمل الآن بنجاح...")
    app.run_polling()