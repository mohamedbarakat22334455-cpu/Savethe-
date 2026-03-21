import asyncio, os, sqlite3, time, random, logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 👑 [ 1. الإعدادات العليا والهوية ]
# ==========================================
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"
PORT = int(os.getenv("PORT", 8080))

# قائمة الكلمات والروابط المحظورة (الدرع الحامي)
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص", "متناك", "سكس", "قحبة", "شرموط"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 💾 [ 2. قاعدة البيانات (الأرشيف الذهبي) ]
# ==========================================
conn = sqlite3.connect('mb_gold_final_archive.db', check_same_thread=False)
db = conn.cursor()
# جداول: المستخدمين، النقاط، الرصيد، الجروبات، الإنذارات
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, balance REAL DEFAULT 0.0)')
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT, status TEXT DEFAULT "open")')
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# ==========================================
# 🛡️ [ 3. نظام الحماية (Middleware) ]
# ==========================================
class FloodShield(BaseMiddleware):
    def __init__(self, rate_limit=1.0):
        self.users = {}
        super().__init__()
    async def __call__(self, handler, event, data):
        if not event.from_user: return await handler(event, data)
        uid = event.from_user.id
        now = time.time()
        if uid in self.users and now - self.users[uid] < rate_limit: return
        self.users[uid] = now
        return await handler(event, data)

dp.message.middleware(FloodShield())

# ==========================================
# 🔐 [ 4. المحركات (الاشتراك والرتب) ]
# ==========================================
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USER}", user_id)
        return member.status not in ["left", "kicked"]
    except: return True

def get_rank(p, uid):
    if uid == ADMIN_ID: return "المطور الإمبراطوري 👑"
    if p >= 5000: return "الملك الذهبي 🏆"
    if p >= 1000: return "VIP 💎"
    if p >= 500: return "عضو ماسي 💠"
    return "عضو جديد 🌱"

# ==========================================
# 🤖 [ 5. التحقق البشري والترحيب ]
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def welcome_captcha(event: ChatMemberUpdated):
    user = event.from_user
    try:
        await bot.restrict_chat_member(event.chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ أنا إنسان (تحقق)", callback_data=f"verify_{user.id}"))
        kb.row(InlineKeyboardButton(text="📢 القناة الرسمية", url=CHANNEL_LINK))
        await bot.send_message(event.chat.id, f"🔱 أهلاً {user.mention_markdown()}\! في حماية **MB Gold**\. اضغط للتحقق وكشف مميزات البوت\.", parse_mode="MarkdownV2", reply_markup=kb.as_markup())
    except: pass

@dp.callback_query(F.data.startswith("verify_"))
async def verify_user(call: types.CallbackQuery):
    t_id = int(call.data.split("_")[1])
    if call.from_user.id != t_id: return await call.answer("الزر ليس لك! ❌", show_alert=True)
    await bot.restrict_chat_member(call.message.chat.id, t_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await call.message.delete()
    await call.answer("✅ تم التحقق، نورت الجروب!", show_alert=True)

# ==========================================
# 🎮 [ 6. أوامر التسلية والـ AI والبصمة ]
# ==========================================
@dp.message(F.text.in_({"ايدي", "ID", "ملفي"}))
async def profile(m: types.Message):
    db.execute('SELECT points, balance FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone(); pts, bal = (res[0], res[1]) if res else (0, 0.0)
    await m.answer(f"🔱 **بطاقة MB Gold**\n👤 الاسم: {m.from_user.first_name}\n🆔 الأيدي: `{m.from_user.id}`\n🏆 الرتبة: {get_rank(pts, m.from_user.id)}\n✨ النقاط: {pts}\n💰 الرصيد: {bal}$", parse_mode="Markdown")

@dp.message(F.text == "حظي")
async def luck(m: types.Message):
    await m.reply(f"🔮 حظك اليوم: `{random.choice(['ذهبي 👑', 'سعيد ✨', 'محظوظ 🎁', 'هادئ 🌊'])}`")

@dp.message(F.text.startswith("نسبة الحب"))
async def love_meter(m: types.Message):
    await m.reply(f"❤️ نسبة الحب هي: `{random.randint(0, 100)}%`")

# نظام الـ AI (Blueprint)
@dp.message(Command("ai"))
async def ai_feature(m: types.Message):
    await m.reply("🤖 نظام الـ AI Dashboard قيد التجهيز للربط بموقعك قريباً!")

# نظام الـ Anatomy 3D
@dp.message(Command("anatomy"))
async def anatomy_link(m: types.Message):
    await m.reply("🦴 تفضل بزيارة أطلس التشريح ثلاثي الأبعاد الخاص بنا:\n(رابط موقعك هنا قريباً)")

# ==========================================
# ⚔️ [ 7. إدارة الجروبات الفولاذية ]
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_master(m: types.Message):
    if m.content_type in {'new_chat_members', 'left_chat_member'}:
        try: await m.delete(); return
        except: pass

    # زيادة النقاط (Tap-to-Earn System)
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    text = (m.text or "").lower()
    # الحماية من الروابط والشتائم
    if any(w in text for w in BAD_WORDS):
        admin = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if admin.status not in ["administrator", "creator"]:
            try: await m.delete(); return
            except: pass

    # أوامر الإدارة بالرد
    if m.reply_to_message:
        me = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if me.status in ["administrator", "creator"] or m.from_user.id == ADMIN_ID:
            t_id = m.reply_to_message.from_user.id
            t_name = m.reply_to_message.from_user.first_name
            if text in ["حظر", "/ban"]: await bot.ban_chat_member(m.chat.id, t_id); await m.answer(f"🚫 تم طرد {t_name}")
            elif text in ["كتم", "/mute"]: await bot.restrict_chat_member(m.chat.id, t_id, permissions=ChatPermissions(can_send_messages=False)); await m.answer(f"🤐 تم كتم {t_name}")
            elif text in ["فك الكتم", "/unmute"]: await bot.restrict_chat_member(m.chat.id, t_id, permissions=ChatPermissions(can_send_messages=True)); await m.answer(f"🔊 فك كتم {t_name}")
            elif text in ["تثبيت", "/pin"]: await bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id); await m.answer("📌 تم التثبيت")
            elif text in ["انذار", "/warn"]:
                db.execute('INSERT OR IGNORE INTO warns VALUES (?, ?, 0)', (m.chat.id, t_id))
                db.execute('UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?', (m.chat.id, t_id))
                conn.commit()
                db.execute('SELECT count FROM warns WHERE chat_id = ? AND user_id = ?', (m.chat.id, t_id))
                w = db.fetchone()[0]
                if w >= 3: await bot.ban_chat_member(m.chat.id, t_id); await m.answer(f"🚫 طرد {t_name} لتجاوز الإنذارات"); db.execute('UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?', (m.chat.id, t_id)); conn.commit()
                else: await m.answer(f"⚠️ إنذار ({w}/3) لـ {t_name}")

    # أوامر القفل والفتح العام
    if text == "قفل الجروب":
        await bot.set_chat_permissions(m.chat.id, ChatPermissions(can_send_messages=False))
        await m.answer("🔒 تم قفل المجموعة.")
    elif text == "فتح الجروب":
        await bot.set_chat_permissions(m.chat.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await m.answer("🔓 تم فتح المجموعة.")

# ==========================================
# 💼 [ 8. أوامر الخاص والمطور ]
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def start_private(m: types.Message):
    if not await check_sub(m.from_user.id):
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="✅ اشترك لتفعيل البوت", url=CHANNEL_LINK))
        return await m.answer(f"⚠️ **مرحباً {m.from_user.first_name}\!**\nعذراً، يجب عليك الاشتراك في القناة أولاً\.", reply_markup=kb.as_markup())
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,)); conn.commit()
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ أضفني لجروبك", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    kb.row(InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats_me"))
    await m.answer(f"👑 **أهلاً بك في MB Gold الشامل\!**\n\nأنا الآن محرك كامل للإدارة، الترفيه، وجمع النقاط\. أضفني لجروبك الآن واستمتع بالتحكم المطلق\.", reply_markup=kb.as_markup())

@dp.message(Command("cast"), F.from_user.id == ADMIN_ID)
async def broadcast(m: types.Message):
    txt = m.text.replace("/cast", "").strip()
    if not txt: return await m.answer("اكتب الرسالة!")
    db.execute("SELECT user_id FROM users"); u_list = db.fetchall()
    ok = 0
    for u in u_list:
        try: await bot.send_message(u[0], f"📢 **إعلان هام:**\n\n{txt}"); ok += 1; await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ تم الإرسال لـ {ok} شخص\.")

@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def stats_admin(m: types.Message):
    db.execute("SELECT COUNT(*) FROM users"); u_c = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM groups"); g_c = db.fetchone()[0]
    await m.answer(f"📊 **إحصائيات الإمبراطورية:**\nالمستخدمين: {u_c}\nالجروبات: {g_c}")

# ==========================================
# 🚀 [ 9. الحل النهائي للرد وتشغيل Railway ]
# ==========================================
async def web_handle(request): return web.Response(text="MB Gold System: Online")

async def main():
    # الخطوة الأهم: حذف الويب هوك وتنظيف الرسائل المعلقة
    await bot.delete_webhook(drop_pending_updates=True)
    
    # تشغيل سيرفر الصحة لريلاوي
    app = web.Application(); app.router.add_get('/', web_handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    
    print("🔥 MB Gold Supreme Archive is LIVE!")
    # بدء استقبال الرسائل (القلب النابض)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
