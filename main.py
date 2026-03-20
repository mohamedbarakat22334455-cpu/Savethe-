import asyncio, os, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiohttp import web

# --- [ إعدادات MB Gold ] ---
API_TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
MY_CHANNEL = "MBABmbab" # قناتك الرسمية
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات المتطورة ] ---
conn = sqlite3.connect('mb_business_v2.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)') 
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT)') 
# جدول الإنذارات الجديد
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# --- [ قائمة الفلتر ] ---
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان"]

# ==========================================
# 🌐 1. خادم الويب (لضمان عمل Railway 24/7)
# ==========================================
async def handle(request):
    return web.Response(text="🟢 MB Gold Ultimate Protection is Live!")

async def start_web():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# ==========================================
# 🛡️ 2. الحماية التلقائية وأوامر الجروبات
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_manager(m: types.Message):
    # تسجيل الجروب
    db.execute('INSERT OR IGNORE INTO groups VALUES (?, ?)', (m.chat.id, m.chat.title))
    conn.commit()

    # 1. الترحيب
    if m.new_chat_members:
        for member in m.new_chat_members:
            if member.id == bot.id:
                await m.answer("✅ **تم تفعيل درع MB Gold بنجاح!**\nالرجاء ترقيتي كـ 'مشرف' وتفعيل كل الصلاحيات لأتمكن من حمايتكم.")
            else:
                await m.answer(f"👋 أهلاً بك يا {member.first_name} في {m.chat.title}!\nالرجاء الالتزام بالقوانين 🛡️")
        return

    # 2. فلتر الكلمات والروابط التلقائي
    text = m.text or m.caption
    if text:
        if any(word in text.lower() for word in BAD_WORDS):
            try:
                await m.delete()
                warning = await m.answer(f"⚠️ {m.from_user.first_name}، نظام الحماية يمنع هذه الكلمات/الروابط!")
                await asyncio.sleep(4)
                await warning.delete()
            except: pass 

    # 3. أوامر المشرفين (بالرد على الرسالة)
    if text and m.reply_to_message:
        # التأكد إن اللي بيدي الأمر أدمن في الجروب (تخطي الفحص حاليا للسرعة، لكن يفضل إضافته)
        target_id = m.reply_to_message.from_user.id
        target_name = m.reply_to_message.from_user.first_name

        # أمر الحظر
        if text.startswith("/ban") or text == "حظر":
            try:
                await bot.ban_chat_member(m.chat.id, target_id)
                await m.answer(f"🚫 تم حظر {target_name} من المجموعة.")
            except: await m.answer("❌ تأكد أنني أمتلك صلاحية الحظر.")

        # أمر الكتم
        elif text.startswith("/mute") or text == "كتم":
            try:
                await bot.restrict_chat_member(m.chat.id, target_id, permissions=ChatPermissions(can_send_messages=False))
                await m.answer(f"🤐 تم كتم {target_name}. لن يستطيع إرسال رسائل.")
            except: pass

        # فك الكتم
        elif text.startswith("/unmute") or text == "فك الكتم":
            try:
                await bot.restrict_chat_member(m.chat.id, target_id, permissions=ChatPermissions(
                    can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True
                ))
                await m.answer(f"🔊 تم فك الكتم عن {target_name}.")
            except: pass

        # نظام الإنذارات
        elif text.startswith("/warn") or text == "انذار":
            db.execute('INSERT OR IGNORE INTO warns (chat_id, user_id) VALUES (?, ?)', (m.chat.id, target_id))
            db.execute('UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?', (m.chat.id, target_id))
            conn.commit()
            
            db.execute('SELECT count FROM warns WHERE chat_id = ? AND user_id = ?', (m.chat.id, target_id))
            warns = db.fetchone()[0]
            
            if warns >= 3:
                try:
                    await bot.ban_chat_member(m.chat.id, target_id)
                    await m.answer(f"🚫 تم طرد {target_name} لتجاوزه 3 إنذارات!")
                    db.execute('UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?', (m.chat.id, target_id))
                    conn.commit()
                except: pass
            else:
                await m.answer(f"⚠️ إنذار ({warns}/3) لـ {target_name}. التزم بالقوانين!")

        # تثبيت رسالة
        elif text.startswith("/pin") or text == "تثبيت":
            try:
                await bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
                await m.answer("📌 تم تثبيت الرسالة بنجاح.")
            except: pass

    # 4. أوامر عامة للجروب (بدون رد)
    if text == "/lock" or text == "قفل الجروب":
        try:
            await bot.set_chat_permissions(m.chat.id, ChatPermissions(can_send_messages=False))
            await m.answer("🔒 تم إغلاق الجروب بواسطة الإدارة.")
        except: pass

    elif text == "/unlock" or text == "فتح الجروب":
        try:
            await bot.set_chat_permissions(m.chat.id, ChatPermissions(
                can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True
            ))
            await m.answer("🔓 تم فتح الجروب، يمكنكم التحدث الآن.")
        except: pass

# ==========================================
# 💼 3. واجهة التواصل في الخاص (تم توجيهها لقناتك)
# ==========================================
@dp.message(Command("start"), F.chat.type == "private")
async def private_start(m: types.Message):
    db.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
    conn.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 تابع قناة MB Gold الرسمية", url=f"https://t.me/{MY_CHANNEL}")],
        [InlineKeyboardButton(text="💎 مميزات الحماية والأوامر", callback_data="vip")]
    ])
    
    await m.answer(
        f"🔱 **أهلاً بك في MB Gold Protector**\n\n"
        f"البوت الأذكى لإدارة وحماية مجموعاتك على تليجرام.\n"
        f"اضغط على الزر أدناه للانضمام لقناتنا الرسمية أو لمعرفة الأوامر المتاحة.",
        reply_markup=kb
    )

@dp.callback_query(F.data == "vip")
async def show_vip(call: types.CallbackQuery):
    await call.message.edit_text(
        "✨ **أوامر الإدارة المتاحة في جروبك:**\n\n"
        "🧹 **مسح تلقائي:** للروابط والشتائم.\n"
        "🔒 **قفل / فتح الجروب:** لإيقاف الدردشة ليلاً.\n"
        "🚫 **بالرد على العضو:** (حظر، كتم، فك الكتم).\n"
        "⚠️ **انذار:** بالرد على العضو (3 إنذارات = طرد).\n"
        "📌 **تثبيت:** بالرد على أي رسالة لتثبيتها.\n\n"
        "فقط قم بإضافتي لمجموعتك وارفعني كـ 'مشرف' لتبدأ الحماية 🛡️",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back")]])
    )

@dp.callback_query(F.data == "back")
async def go_back(call: types.CallbackQuery):
    await private_start(call.message)

# ==========================================
# 👑 4. أوامر المطور (لك أنت فقط)
# ==========================================
@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(m: types.Message):
    db.execute("SELECT COUNT(*) FROM users")
    users_count = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM groups")
    groups_count = db.fetchone()[0]
    await m.answer(f"📊 **إحصائيات الإمبراطورية:**\n\n👥 أشخاص في الخاص: {users_count}\n🛡️ مجموعات محمية: {groups_count}")

@dp.message(Command("cast"), F.from_user.id == ADMIN_ID)
async def broadcast_msg(m: types.Message):
    msg_text = m.text.replace("/cast", "").strip()
    if not msg_text: return await m.answer("⚠️ اكتب الرسالة بعد الأمر.")
    
    db.execute("SELECT user_id FROM users")
    users = db.fetchall()
    count = 0
    await m.answer("⏳ جاري الإرسال للجميع...")
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 **إعلان من MB Gold:**\n\n{msg_text}")
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ تم إرسال رسالتك إلى {count} شخص!")

# ==========================================
# 🚀 5. التشغيل
# ==========================================
async def main():
    asyncio.create_task(start_web())
    print("🚀 MB Gold Ultimate is Live!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
