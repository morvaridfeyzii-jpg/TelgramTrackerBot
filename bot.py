import os
import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8572888068:AAF2yf1BozORKz_TH1fCSp9R09c-Lg4T0Ts")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlwaysOnlineTracker:
    def __init__(self):
        self.setup_database()
    
    def setup_database(self):
        self.conn = sqlite3.connect('/app/tracker.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id INTEGER,
                visitor_name TEXT,
                target_id INTEGER,
                click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        logger.info("✅ دیتابیس آماده شد")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if context.args and context.args[0].startswith('user_'):
            target_id = int(context.args[0].split('_')[1])
            await self.track_visit(update, context, user, target_id)
        else:
            bot_username = context.bot.username
            personal_link = f"https://t.me/{bot_username}?start=user_{user.id}"
            
            await update.message.reply_text(
                f"🤖 **ربات ردیابی همیشه آنلاین**\n\n"
                f"🔗 لینک شما:\n`{personal_link}`\n\n"
                f"✅ این ربات ۲۴/۷ فعال است!",
                parse_mode='MARKDOWN'
            )
    
    async def track_visit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, visitor, target_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO clicks (visitor_id, visitor_name, target_id) VALUES (?, ?, ?)",
            (visitor.id, visitor.first_name, target_id)
        )
        self.conn.commit()
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"👀 **بازدید جدید!**\n\n"
                     f"📛 نام: {visitor.first_name}\n"
                     f"🆔 آیدی: `{visitor.id}`\n"
                     f"🔖 یوزرنیم: @{visitor.username or 'ندارد'}",
                parse_mode='MARKDOWN'
            )
            logger.info(f"📨 اطلاعیه برای {target_id} ارسال شد")
        except Exception as e:
            logger.error(f"⚠️ خطا در ارسال اطلاع: {e}")
        
        await update.message.reply_text("✅ به پروفایل خوش آمدید!")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM clicks WHERE target_id = ?", (user.id,))
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT visitor_id) FROM clicks WHERE target_id = ?", (user.id,))
        unique = cursor.fetchone()[0]
        
        await update.message.reply_text(
            f"📊 **آمار شما:**\n\n"
            f"👥 کل کلیک‌ها: `{total}`\n"
            f"👤 بازدیدکنندگان منحصر به فرد: `{unique}`\n"
            f"🟢 وضعیت: همیشه آنلاین",
            parse_mode='MARKDOWN'
        )
    
    def run(self):
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stats", self.stats))
        
        logger.info("🚀 ربات در حال اجرا روی سرور...")
        application.run_polling()

if __name__ == "__main__":
    bot = AlwaysOnlineTracker()
    bot.run()
