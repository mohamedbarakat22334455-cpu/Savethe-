import asyncio, os, sqlite3, time, random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- [ الإعدادات العليا ] ---
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
OFFICIAL_CHANNEL = "MBABmbab"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- [ محرك قاعدة البيانات - Singleton Pattern ] ---
class MB_Database:
    def __init__(self):
        self.conn = sqlite3.connect('mb_infinity.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup()

    def setup(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, anti_link INTEGER DEFAULT 1, anti_service INTEGER DEFAULT 1, welcome_msg TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER DEFAULT 0)')
        self.cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES ("total_actions", 0)')
        self.conn.commit()

db = MB_Database()

# --- [ Middleware: حماية من السبام والتكرار ] ---
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit=2): # ثانيتين بين كل رسالة
        self.last_from_user = {}
        super().__init__()

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = time.time()
        if user_id in self.last_from_user and now - self.last_from_user[user_id] < 2:
            return # تجاهل الرسالة
        self.last_from_user[user_id] = now
        return await handler(event, data)

dp.message.middleware(AntiFloodMiddleware())

# ==========================================
# 🌐 1. Server Health Check (Railway)
# ==========================================
async def handle(request): return web.Response(text="🏆 MB Gold Infinity is Online")
async def start_web():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# ==========================================
# 🛡️ 2. التحقق البشري (Advanced Captcha)
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user = event.from_user
    chat_id = event.chat.id
    
    # تقييد العضو فوراً
    try:
        await bot.restrict_chat_member(chat_id, user.id, permissions=ChatPermissions(can_send_messages=False))
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="✅ أنا إنسان (تحقق)", callback_data=f"verify_{user.id}"))
        
        await bot.send_message(
            chat_id, 
            f"🔱 **مرحباً بك {user.mention_markdown()} في مجموعتنا\!**\n\n🛡️ لحماية المجموعة من البوتات، يرجى الضغط على الزر أدناه للتحقق من هويتك خلال 60 ثانية\.",
            parse_mode="MarkdownV2",
            reply_markup=builder.as_markup()
        )
    except: pass

@dp.callback_query(F.data.startswith("verify_"))
async def verify_callback(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    if call.from_user.id != user_id:
        return await call.answer("❌ هذا الزر ليس لك!", show_alert=True)
    
    await bot.restrict_chat_member(call.message.chat.id, user_id, permissions=ChatPermissions(
        can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True
    ))
    await call.message.delete()
    await call.answer("✅ تم التحقق بنجاح! استمتع بالدردشة.", show_alert=True)

# ==========================================
# ⚙️ 3. لوحة تحكم عصرية (Glassmorphism Style)
# ==========================================
@dp.message(Command("settings"))
async def admin_settings(m: types.Message):
    user_stat = await bot.get_chat_member(m.chat.id, m.from_user.id)
    if user_stat.status not in ["administrator", "creator"] and m.from_user.id != ADMIN_ID: return

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 منع الروابط", callback_data="toggle_links"),
                InlineKeyboardButton(text="🧹 تنظيف الخدمة", callback_data="toggle_service"))
    builder.row(InlineKeyboardButton(text="🔒 قفل الشات", callback_data="set_lock"),
                InlineKeyboardButton(text="🔓 فتح الشات", callback_data="set_unlock"))
    builder.row(InlineKeyboardButton(text="🔱 القناة الرسمية", url=f"https://t.me/{OFFICIAL_CHANNEL}"))

    await m.answer(
        "💎 **إعدادات MB Gold PRO**\n\n"
        "تحكم في خصائص الحماية المتقدمة لجروبك الآن\.",
        parse_mode="MarkdownV2",
        reply_markup=builder.as_markup()
    )

# ==========================================
# 👑 4. محرك الحماية من الروابط والشتائم
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_guardian(m: types.Message):
    if not m.text: return
    
    # فلتر متطور باستخدام Regex أو الكلمات المفتاحية
    blacklist = ["t.me/", "http", "شتيمة", "إعلان", "كسم"] 
    if any(word in m.text.lower() for word in blacklist):
        user = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if user.status in ["administrator", "creator"]: return
        
        try:
            await m.delete()
            # تحديث الإحصائيات في القاعدة
            db.cursor.execute('UPDATE stats SET value = value + 1 WHERE key = "total_actions"')
            db.conn.commit()
        except: pass

# ==========================================
# 🚀 5. انطلاق النظام
# ==========================================
async def main():
    asyncio.create_task(start_web())
    print("🔱 MB Gold Infinity: The Engine is Roaring!")
    # حذف الـ Webhook القديم لضمان عدم التداخل
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
