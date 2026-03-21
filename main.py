import asyncio, os, sqlite3, time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- [ إعدادات الهوية الملكية ] ---
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- [ قاعدة بيانات الرتب والنقاط ] ---
conn = sqlite3.connect('mb_magnet.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, rank TEXT DEFAULT "برونزي 🥉")')
conn.commit()

# ==========================================
# 🔐 1. محرك التحقق من الاشتراك (Force Sub)
# ==========================================
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USER}", user_id)
        return member.status != "left"
    except: return True

# ==========================================
# 🎭 2. نظام الرتب والملف الشخصي (ID)
# ==========================================
@dp.message(F.text.in_({"ايدي", "ID", "/id", "ملفي"}))
async def user_profile(m: types.Message):
    db.execute('SELECT points, rank FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone()
    points = res[0] if res else 0
    rank = res[1] if res else "برونزي 🥉"

    profile_text = (
        f"🔱 **بطاقة الهوية الملكية - MB Gold**\n\n"
        f"👤 **الاسم:** `{m.from_user.first_name}`\n"
        f"🆔 **المعرف:** `{m.from_user.id}`\n"
        f"🏆 **الرتبة:** {rank}\n"
        f"✨ **النقاط:** `{points}`\n\n"
        f"🛡 _نظام حماية وتطوير MBAB المتكامل\._"
    )
    await m.answer(profile_text, parse_mode="MarkdownV2")

# ==========================================
# 🛡️ 3. حماية الجروبات + الجذب القسري
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_guard(m: types.Message):
    # تسجيل المستخدم وتحديث نقاطه (تفاعل)
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    # فحص الاشتراك الإجباري داخل الجروب (اختياري - يفضل في الخاص)
    # إذا أردت كتم غير المشتركين، فعل الكود التالي:
    """
    if not await check_subscription(m.from_user.id):
        try:
            await m.delete()
            # إرسال تنبيه وحذفه بعد 5 ثواني
            return
        except: pass
    """
    
    # فلتر الكلمات (تطوير الأسلوب)
    blacklist = ["t.me/", "http", "شتيمة"]
    if m.text and any(w in m.text.lower() for w in blacklist):
        user = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if user.status not in ["administrator", "creator"]:
            await m.delete()

# ==========================================
# 🎨 4. الترحيب "المغناطيسي" (Welcome)
# ==========================================
@dp.message(F.new_chat_members)
async def welcome_viral(m: types.Message):
    for user in m.new_chat_members:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="💎 انضم للمنظومة الذهبية", url=f"https://t.me/{CHANNEL_USER}"))
        
        await m.answer(
            f"👑 **مرحباً بك في المنطقة الملكية\!**\n\n"
            f"يا {user.mention_markdown()}\n"
            f"أنت الآن تحت حماية نظام **MB Gold** الذكي\.\n"
            f"تفاعل لترقية رتبتك والحصول على مميزات VIP 🏆\.",
            parse_mode="MarkdownV2",
            reply_markup=kb.as_markup()
        )
    try: await m.delete()
    except: pass

# ==========================================
# 🚀 5. واجهة البداية (The Hook)
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def start_private(m: types.Message):
    # الفخ: الاشتراك الإجباري
    if not await check_subscription(m.from_user.id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ اشترك لتفعيل البوت", url=f"https://t.me/{CHANNEL_USER}"))
        return await m.answer(
            f"⚠️ **عذراً\! الوصول محدود**\n\n"
            f"يجب عليك الاشتراك في قناة **MB Gold الرسمية** لتتمكن من استخدام خدمات البوت الملكية\.",
            parse_mode="MarkdownV2", reply_markup=kb.as_markup()
        )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ أضفني لجروبك الآن", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    kb.row(InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats"), InlineKeyboardButton(text="🔗 شارك البوت", switch_inline_query=""))
    
    await m.answer(
        f"🔱 **مرحباً بك في مركز تحكم MB Gold**\n\n"
        f"أقوى نظام لإدارة وحماية المجموعات بأسلوب عصري\.\n\n"
        f"✅ **حالة الحساب:** عضو ملكي\n"
        f"🚀 **الإصدار:** Black VIP V6",
        parse_mode="MarkdownV2", reply_markup=kb.as_markup()
    )

# ==========================================
# 🌐 6. تشغيل المحرك (Railway Ready)
# ==========================================
async def handle(request): return web.Response(text="MB Gold Magnet is Running!")
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(web._run_app(web.Application().add_routes([web.get('/', handle)]), port=PORT))
    print("🔥 MB Gold Magnet is Online!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
