import asyncio, os, sqlite3, time, random, logging, re
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 👑 [ 1. الهوية والبيانات الأساسية ]
# ==========================================
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"
PORT = int(os.getenv("PORT", 8080))

# فلتر الحماية (الكلمات، الروابط، الإعلانات)
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص", "متناك", "سكس", "شرموط"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 💾 [ 2. قاعدة البيانات (المصنع الشامل) ]
# ==========================================
conn = sqlite3.connect('mb_gold_master.db', check_same_thread=False)
db = conn.cursor()
# مستخدمين (نقاط، رصيد، محفظة)
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, balance REAL DEFAULT 0.0, wallet TEXT)')
# جروبات وإنذارات
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT)')
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# ==========================================
# 🛡️ [ 3. درع الحماية والرد السريع ]
# ==========================================
class MasterMiddleware(BaseMiddleware):
    def __init__(self, limit=0.7):
        self.users = {}
        super().__init__()
    async def __call__(self, handler, event, data):
        if not event.from_user: return await handler(event, data)
        uid = event.from_user.id
        now = time.time()
        if uid in self.users and now - self.users[uid] < limit: return
        self.users[uid] = now
        return await handler(event, data)

dp.message.middleware(MasterMiddleware())

# ==========================================
# 🔐 [ 4. المحركات المساعدة (الاشتراك والرتب) ]
# ==========================================
async def is_subscribed(uid):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USER}", uid)
        return member.status not in ["left", "kicked"]
    except: return True

def get_rank(p, uid):
    if uid == ADMIN_ID: return "المطور الإمبراطوري 👑"
    if p >= 5000: return "الملك الذهبي 🏆"
    if p >= 1000: return "VIP 💎"
    if p >= 500: return "عضو ماسي 💠"
    return "عضو جديد 🌱"

# ==========================================
# 🤖 [ 5. نظام الترحيب والتحقق ]
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_join(event: ChatMemberUpdated):
    user = event.from_user
    try:
        await bot.restrict_chat_member(event.chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="✅ أنا إنسان (تحقق)", callback_data=f"v_{user.id}"))
        await bot.send_message(event.chat.id, f"🔱 أهلاً {user.mention_markdown()}\! اضغط للتحقق وفتح مميزات البوت\.", parse_mode="MarkdownV2", reply_markup=kb.as_markup())
    except: pass

@dp.callback_query(F.data.startswith("v_"))
async def verify(call: types.CallbackQuery):
    tid = int(call.data.split("_")[1])
    if call.from_user.id != tid: return await call.answer("❌ الزر ليس لك!", show_alert=True)
    await bot.restrict_chat_member(call.message.chat.id, tid, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await call.message.delete()
    await call.answer("✅ تم التحقق بنجاح!", show_alert=True)

# ==========================================
# 📥 [ 6. نظام الداونلودر (MB Gold Downloader) ]
# ==========================================
@dp.message(F.text.regexp(r'(https?://[^\s]+)'))
async def link_handler(m: types.Message):
    url = m.text
    if "tiktok.com" in url or "instagram.com" in url or "youtube.com" in url:
        await m.reply("📥 **جاري معالجة الرابط عبر MB Gold Downloader...**\nيرجى الانتظار ثواني.")
        # هنا يتم ربط كود التحميل الذي صممناه سابقاً
        await asyncio.sleep(2)
        await m.answer("✅ الرابط جاهز للتحميل (سيتم إرسال الملف هنا)")

# ==========================================
# 🎮 [ 7. الأقسام المنفصلة (كل ميزة لوحدها) ]
# ==========================================

# 1. الملف الشخصي (ID & Wallet)
@dp.message(F.text.in_({"ايدي", "ID", "ملفي"}))
async def profile_cmd(m: types.Message):
    db.execute('SELECT points, balance, wallet FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone(); pts, bal, wal = (res[0], res[1], res[2]) if res else (0, 0.0, "غير مسجل")
    msg = (f"🔱 **بطاقة نخبة MB Gold**\n━━━━━━━━━━━━━━\n"
           f"👤 الاسم: {m.from_user.first_name}\n🆔 الأيدي: `{m.from_user.id}`\n"
           f"🏆 الرتبة: {get_rank(pts, m.from_user.id)}\n✨ النقاط: {pts}\n💰 الرصيد: {bal}$\n"
           f"💳 المحفظة: `{wal}`\n━━━━━━━━━━━━━━")
    await m.answer(msg, parse_mode="Markdown")

# 2. نظام التسلية
@dp.message(F.text == "حظي")
async def luck_cmd(m: types.Message):
    await m.reply(f"🔮 حظك اليوم: `{random.choice(['أسطوري 🏆', 'ذهبي 👑', 'سعيد ✨'])}`")

@dp.message(F.text.startswith("نسبة الحب"))
async def love_cmd(m: types.Message):
    await m.reply(f"❤️ نسبة التوافق: `{random.randint(0, 100)}%`")

# 3. نظام الـ 3D والـ AI
@dp.message(Command("anatomy"))
async def anatomy_cmd(m: types.Message):
    await m.answer("🦴 **Medical Atlas 3D**\nمرحباً بك في أطلس التشريح\. يمكنك اختيار العضو المراد معاينته من موقعنا قريباً\.")

@dp.message(Command("ai"))
async def ai_cmd(m: types.Message):
    await m.answer("🤖 **AI Blueprint**\nنظام توليد الصور والذكاء الاصطناعي قيد المعالجة الآن\.")

# ==========================================
# ⚔️ [ 8. محرك الإدارة الكامل (بالرد) ]
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_logic(m: types.Message):
    if m.content_type in {'new_chat_members', 'left_chat_member'}:
        try: await m.delete(); return
        except: pass

    # نظام تجميع النقاط (Mining)
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    text = (m.text or "").lower()
    if any(w in text for w in BAD_WORDS):
        adm = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if adm.status not in ["administrator", "creator"]:
            try: await m.delete(); return
            except: pass

    if m.reply_to_message:
        is_adm = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if is_adm.status in ["administrator", "creator"] or m.from_user.id == ADMIN_ID:
            tid = m.reply_to_message.from_user.id
            if text in ["حظر", "/ban"]: await bot.ban_chat_member(m.chat.id, tid); await m.answer("🚫 تم الطرد.")
            elif text in ["كتم", "/mute"]: await bot.restrict_chat_member(m.chat.id, tid, permissions=ChatPermissions(can_send_messages=False)); await m.answer("🤐 تم الكتم.")
            elif text in ["فك الكتم", "/unmute"]: await bot.restrict_chat_member(m.chat.id, tid, permissions=ChatPermissions(can_send_messages=True)); await m.answer("🔊 تم الفك.")
            elif text in ["انذار", "/warn"]:
                db.execute('INSERT OR IGNORE INTO warns VALUES (?, ?, 0)', (m.chat.id, tid))
                db.execute('UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?', (m.chat.id, tid))
                conn.commit()
                db.execute('SELECT count FROM warns WHERE chat_id = ? AND user_id = ?', (m.chat.id, tid))
                w = db.fetchone()[0]
                if w >= 3: await bot.ban_chat_member(m.chat.id, tid); await m.answer("🚫 طرد (تجاوز الإنذارات)")
                else: await m.answer(f"⚠️ إنذار ({w}/3)")

# ==========================================
# 🚀 [ 9. تشغيل السيرفر وإصلاح الرد ]
# ==========================================
async def handle_ping(request): return web.Response(text="MB Gold System: Online")

async def main():
    await bot.delete_webhook(drop_pending_updates=True) # حذف الزحمة القديمة للرد فوراً
    app = web.Application(); app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    print("🔥 MB Gold MASTER is LIVE!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
