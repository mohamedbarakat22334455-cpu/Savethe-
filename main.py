import asyncio, os, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- [ إعدادات MB Gold ] ---
API_TOKEN = '8758046360:AAF8ilMxOrEHLr08fOGc5yZlT5blrByj1zs'
ADMIN_ID = 6363223356
MY_USER_ID = "t.me/MBABmbab" 
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات للتسويق والإدارة ] ---
conn = sqlite3.connect('mb_business.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)') # لحفظ العملاء
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT)') # لحفظ الجروبات المحمية
conn.commit()

# --- [ قائمة الفلتر ] ---
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان"]

# ==========================================
# 🌐 1. صفحة الويب (عشان ريلاوي ميفصلش)
# ==========================================
async def handle(request):
    return web.Response(text="🟢 MB Gold Enterprise is Running Perfectly!")

async def start_web():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# ==========================================
# 🛡️ 2. نظام الحماية الذكي للجروبات
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_protector(m: types.Message):
    # تسجيل الجروب في قاعدة البيانات لو مش متسجل
    db.execute('INSERT OR IGNORE INTO groups VALUES (?, ?)', (m.chat.id, m.chat.title))
    conn.commit()

    # 1. الترحيب بالأعضاء الجدد
    if m.new_chat_members:
        for member in m.new_chat_members:
            if member.id == bot.id:
                await m.answer("✅ **تم تفعيل نظام حماية MB Gold بنجاح!**\nالرجاء ترقيتي كـ 'مشرف' لأتمكن من العمل.")
            else:
                await m.answer(f"👋 أهلاً بك يا {member.first_name} في الجروب! الرجاء الالتزام بالقوانين 🛡️")
        return

    # 2. فلتر الشتائم والروابط (في النص أو وصف الصور)
    text = m.text or m.caption
    if text:
        if any(word in text.lower() for word in BAD_WORDS):
            try:
                await m.delete()
                warning = await m.answer(f"⚠️ {m.from_user.first_name}، ممنوع إرسال روابط أو كلمات مسيئة!")
                await asyncio.sleep(5) # يمسح التحذير بعد 5 ثواني عشان ميزعجش الشات
                await warning.delete()
            except: pass # لو البوت مش مشرف مش هيعمل حاجة

    # 3. أوامر الإدارة لأصحاب الجروب (بالرد على الرسالة)
    if text and m.reply_to_message:
        # أمر الحظر
        if text.startswith("/ban") or text == "حظر":
            try:
                await bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
                await m.answer(f"🚫 تم حظر {m.reply_to_message.from_user.first_name} بنجاح!")
            except:
                await m.answer("❌ تأكد أنني أمتلك صلاحية الحظر وأنك مشرف.")

# ==========================================
# 💼 3. واجهة البيزنس (في الخاص)
# ==========================================
@dp.message(Command("start"), F.chat.type == "private")
async def private_start(m: types.Message):
    # حفظ العميل للتسويق
    db.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
    conn.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 مميزات الحماية VIP", callback_data="vip")],
        [InlineKeyboardButton(text="🤝 اطلب البوت لقناتك", url=f"https://t.me/{MY_USER_ID}")],
    ])
    
    await m.answer(
        f"🔱 **أهلاً بك في MB Gold Protector**\n\n"
        f"الدرع الأقوى لحماية مجموعاتك وقنواتك على تليجرام.\n"
        f"نقدم لك حماية تلقائية 24/7 بدون تدخل منك.\n\n"
        f"👇 اضغط أدناه لاكتشاف المميزات أو لطلب الخدمة.",
        reply_markup=kb
    )

@dp.callback_query(F.data == "vip")
async def show_vip(call: types.CallbackQuery):
    await call.message.edit_text(
        "✨ **نظام MB Gold يقدم لك:**\n\n"
        "🧹 **تنظيف آلي:** مسح الشتائم والروابط فوراً.\n"
        "🚫 **منع السرقة:** تقييد التحويل والنسخ للحفاظ على محتواك.\n"
        "👮‍♂️ **إدارة ذكية:** أوامر سريعة للحظر والكتم.\n"
        "👋 **ترحيب تلقائي:** بالأعضاء الجدد.\n\n"
        "📞 **تواصل مع المطور لربط البوت بمجموعتك الآن!**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back")]])
    )

@dp.callback_query(F.data == "back")
async def go_back(call: types.CallbackQuery):
    await private_start(call.message)

# ==========================================
# 👑 4. لوحة تحكم الإدارة (لك أنت فقط يا محمد)
# ==========================================
@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(m: types.Message):
    db.execute("SELECT COUNT(*) FROM users")
    users_count = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM groups")
    groups_count = db.fetchone()[0]
    
    await m.answer(f"📊 **إحصائيات إمبراطورية MB Gold:**\n\n👥 العملاء في الخاص: {users_count}\n🛡️ الجروبات المحمية: {groups_count}")

@dp.message(Command("cast"), F.from_user.id == ADMIN_ID)
async def broadcast_msg(m: types.Message):
    # أمر الإذاعة: اكتب /cast وبعدها رسالتك
    msg_text = m.text.replace("/cast", "").strip()
    if not msg_text:
        return await m.answer("⚠️ اكتب الرسالة بعد الأمر، هكذا:\n`/cast عرض خاص لجميع العملاء!`", parse_mode="Markdown")
    
    db.execute("SELECT user_id FROM users")
    users = db.fetchall()
    count = 0
    await m.answer("⏳ جاري الإرسال للجميع...")
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 **رسالة من الإدارة:**\n\n{msg_text}")
            count += 1
            await asyncio.sleep(0.05) # عشان تليجرام ميعملش حظر للبوت
        except: pass
    await m.answer(f"✅ تم إرسال رسالتك إلى {count} شخص بنجاح!")

# ==========================================
# 🚀 5. التشغيل
# ==========================================
async def main():
    asyncio.create_task(start_web())
    print("🚀 MB Gold Enterprise is Live!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
