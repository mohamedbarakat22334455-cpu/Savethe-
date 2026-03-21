import asyncio, os, sqlite3, time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiohttp import web

# --- [ إعدادات MB Gold ] ---
# استخدمنا التوكن الجديد بتاعك هنا
API_TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
MY_CHANNEL = "MBABmbab"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('mb_gold_v4.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT)')
conn.commit()

# --- [ قائمة الفلتر الذهبية ] ---
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص"]

# ==========================================
# 🌐 1. صفحة الويب (لضمان بقاء البوت حياً)
# ==========================================
async def handle(request):
    return web.Response(text="🏆 MB Gold Guardian V4 is Online!")

async def start_web():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# ==========================================
# 🛡️ 2. محرك الحماية والاستجابة السريعة
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def security_engine(m: types.Message):
    # تسجيل الجروب أوتوماتيك
    db.execute('INSERT OR IGNORE INTO groups VALUES (?, ?)', (m.chat.id, m.chat.title))
    conn.commit()
    
    # طباعة في الـ Logs عشان نتأكد إن البوت شايف الرسايل
    print(f"📩 رسالة جديدة من {m.chat.title}: {m.text}")

    # 1. الترحيب (بلمسة ذهبية)
    if m.new_chat_members:
        for member in m.new_chat_members:
            welcome_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔱 انضم لقناتنا", url=f"https://t.me/{MY_CHANNEL}")]
            ])
            await m.answer(f"✨ **أهلاً بك يا {member.first_name} في عالمنا!**\n🛡️ نحن هنا لحمايتك، التزم بالقوانين.", reply_markup=welcome_kb)
        return

    # 2. فلتر الكلمات والروابط (مسح فوري)
    text = (m.text or m.caption or "").lower()
    if any(word in text for word in BAD_WORDS):
        try:
            await m.delete()
            await bot.send_message(ADMIN_ID, f"🔔 **بلاغ أمني:** تم حذف مخالفة في {m.chat.title}")
        except: pass

# ==========================================
# ⚙️ 3. أوامر الإدارة الشاملة
# ==========================================
@dp.message(Command("admin"))
async def admin_panel(m: types.Message):
    # التأكد من هوية المشرف
    member = await bot.get_chat_member(m.chat.id, m.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return await m.answer("⚠️ عذراً، هذا الأمر للذهب (المشرفين) فقط!")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔒 إغلاق الدردشة", callback_data="lock"),
         InlineKeyboardButton(text="🔓 فتح الدردشة", callback_data="unlock")],
        [InlineKeyboardButton(text="📊 حالة النظام", callback_data="stats_grp")]
    ])
    await m.answer("🛠 **لوحة تحكم MB Gold الذكية:**", reply_markup=kb)

@dp.callback_query(F.data.in_({"lock", "unlock"}))
async def toggle_chat(call: types.CallbackQuery):
    if call.data == "lock":
        await bot.set_chat_permissions(call.message.chat.id, ChatPermissions(can_send_messages=False))
        await call.answer("تم إغلاق الدردشة بنجاح 🔒", show_alert=True)
    else:
        await bot.set_chat_permissions(call.message.chat.id, ChatPermissions(
            can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True
        ))
        await call.answer("تم فتح الدردشة للجميع 🔓", show_alert=True)

# ==========================================
# 💼 4. واجهة الخاص (التسويق)
# ==========================================
@dp.message(Command("start"), F.chat.type == "private")
async def private_start(m: types.Message):
    db.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 انضم لقناة MBAB الرسمية", url=f"https://t.me/{MY_CHANNEL}")],
        [InlineKeyboardButton(text="🤖 ضيفني لجروبك الآن", url=f"https://t.me/{ (await bot.get_me()).username }?startgroup=true")]
    ])
    
    await m.answer(
        f"🔱 **مرحباً بك في نظام MB Gold المتطور**\n\n"
        f"أقوى بوت حماية وإدارة في تليجرام.\n"
        f"دقة، سرعة، وأمان لا يتوقف.\n\n"
        f"✅ **الحالة:** متصل ويعمل\n"
        f"🚀 **الإصدار:** V4.0 Enterprise",
        reply_markup=kb
    )

# ==========================================
# 🚀 5. تشغيل المحرك
# ==========================================
async def main():
    asyncio.create_task(start_web())
    print("🔥 MB Gold Engine is Roaring!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
