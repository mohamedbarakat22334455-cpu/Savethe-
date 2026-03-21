import asyncio, os, sqlite3, time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- [ إعدادات البراند ] ---
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab" # يوزرك بدون @
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات - لتخزين النقاط والمشتركين ] ---
conn = sqlite3.connect('mb_viral.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)')
conn.commit()

# ==========================================
# 🔐 1. فحص الاشتراك (محرك الجذب)
# ==========================================
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USER}", user_id)
        return member.status != "left"
    except: return True # لو البوت مش أدمن هيعدي الناس مؤقتاً

# ==========================================
# 🎨 2. الترحيب "المبهر" (Welcome Viral)
# ==========================================
@dp.message(F.new_chat_members)
async def viral_welcome(m: types.Message):
    for user in m.new_chat_members:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🏆 انضم لعالم MB Gold", url=f"https://t.me/{CHANNEL_USER}"))
        
        # رسالة ترحيب فخمة بـ MarkdownV2
        await m.answer(
            f"✨ **أهلاً بك يا {user.mention_markdown()} في أرقى مجموعات تليجرام\!**\n\n"
            f"لقد تم تفعيل حماية **MB Gold** لتأمين وجودك معنا\. استمتع بتجربة فريدة وآمنة 🛡\.",
            parse_mode="MarkdownV2",
            reply_markup=kb.as_markup()
        )
    try: await m.delete() # مسح رسالة "انضم فلان" عشان النظافة
    except: pass

# ==========================================
# 💰 3. نظام التفاعل (نقاط MB الذهبية)
# ==========================================
@dp.message(Command("points"))
async def my_points(m: types.Message):
    db.execute('SELECT points FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone()
    p = res[0] if res else 0
    await m.answer(f"🔱 **رصيدك من نقاط MB الذهبية:** `{p}` نقطة\n\n*كلما تفاعلت أكثر، زادت رتبتك في النظام!*", parse_mode="Markdown")

# ==========================================
# 🚀 4. واجهة البداية (The Marketing Dashboard)
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def viral_start(m: types.Message):
    # 1. فحص الاشتراك الإجباري
    if not await is_subscribed(m.from_user.id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ اشترك لتفعيل النسخة الذهبية", url=f"https://t.me/{CHANNEL_USER}"))
        return await m.answer(
            f"⚠️ **عذراً يا {m.from_user.first_name}\!**\n\n"
            f"يجب عليك الانضمام لقناة المطور أولاً للاستفادة من مميزات البوت الحصرية\.",
            parse_mode="MarkdownV2", reply_markup=kb.as_markup()
        )

    # 2. تسجيل المستخدم
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    conn.commit()

    # 3. واجهة فخمة
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ أضفني لجروبك (حماية مجانية)", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(InlineKeyboardButton(text="💎 مميزات الـ VIP", callback_data="vip_features"),
                InlineKeyboardButton(text="🔗 دعوة صديق", switch_inline_query="انصحك باستخدام هذا البوت الجبار!"))
    builder.row(InlineKeyboardButton(text="🏆 قناتنا الرسمية", url=f"https://t.me/{CHANNEL_USER}"))

    await m.answer(
        f"👑 **مرحباً بك في مركز تحكم MB Gold**\n\n"
        f"أنت الآن تستخدم الإصدار **V5 Black Edition**\.\n"
        f"هذا البوت ليس مجرد حماية، بل هو بوابتك للتميز على تليجرام\.\n\n"
        f"✅ **حسابك:** بريميوم نشط\n"
        f"✨ **النقاط:** مفعّلة",
        parse_mode="MarkdownV2",
        reply_markup=builder.as_markup()
    )

# ==========================================
# 🌐 5. تشغيل السيرفر (The Engine)
# ==========================================
async def handle(request): return web.Response(text="MB Gold Viral is Live!")
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    
    print("🔥 MB Gold Viral: The Engine is Roaring!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
