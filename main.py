import asyncio, os, sqlite3, time, random, logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 👑 [ 1. الإعدادات والتوكن ]
# ==========================================
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"
PORT = int(os.getenv("PORT", 8080))

# فلاتر الحماية
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص", "متناك", "سكس"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 💾 [ 2. قاعدة البيانات الشاملة ]
# ==========================================
conn = sqlite3.connect('mb_gold_clean.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, balance REAL DEFAULT 0.0)')
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT)')
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# ==========================================
# 🛡️ [ 3. نظام الحماية (Middleware) ]
# ==========================================
class AntiFlood(BaseMiddleware):
    def __init__(self, limit=1.0):
        self.users = {}
        super().__init__()
    async def __call__(self, handler, event, data):
        if not event.from_user: return await handler(event, data)
        uid = event.from_user.id
        now = time.time()
        if uid in self.users and now - self.users[uid] < limit: return
        self.users[uid] = now
        return await handler(event, data)

dp.message.middleware(AntiFlood())

# ==========================================
# 🔐 [ 4. التحقق والاشتراك الإجباري ]
# ==========================================
async def is_sub(uid):
    try:
        m = await bot.get_chat_member(f"@{CHANNEL_USER}", uid)
        return m.status not in ["left", "kicked"]
    except: return True

# ==========================================
# 🤖 [ 5. نظام الترحيب الذكي (بدون زحمة) ]
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def welcome_logic(event: ChatMemberUpdated):
    u = event.from_user
    try:
        await bot.restrict_chat_member(event.chat.id, u.id, permissions=ChatPermissions(can_send_messages=False))
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="✅ اضغط للتحقق", callback_data=f"verify_{u.id}"))
        await bot.send_message(event.chat.id, f"🔱 أهلاً {u.first_name}\! يرجى إثبات أنك إنسان لفتح المميزات\.", parse_mode="MarkdownV2", reply_markup=kb.as_markup())
    except: pass

@dp.callback_query(F.data.startswith("verify_"))
async def verify_done(call: types.CallbackQuery):
    tid = int(call.data.split("_")[1])
    if call.from_user.id != tid: return await call.answer("مش ليك! ❌", show_alert=True)
    await bot.restrict_chat_member(call.message.chat.id, tid, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await call.message.delete()
    await call.answer("✅ تم التفعيل بنجاح!", show_alert=True)

# ==========================================
# 🎮 [ 6. الأقسام المنفصلة (كل حاجة لوحدها) ]
# ==========================================

# القسم 1: معلومات الحساب (ID & Points)
@dp.message(F.text.in_({"ايدي", "ID", "ملفي"}))
async def cmd_id(m: types.Message):
    db.execute('SELECT points, balance FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone(); pts, bal = (res[0], res[1]) if res else (0, 0.0)
    await m.answer(f"🔱 **حساب MB Gold**\n👤 الاسم: {m.from_user.first_name}\n✨ النقاط: {pts}\n💰 الرصيد: {bal}$", parse_mode="Markdown")

# القسم 2: الألعاب والتسلية (حظي)
@dp.message(F.text == "حظي")
async def cmd_luck(m: types.Message):
    await m.reply(f"🔮 حظك اليوم هو: `{random.choice(['أسطوري 🏆', 'جميل ✨', 'ذهبي 👑'])}`", parse_mode="Markdown")

# القسم 3: نسبة الحب
@dp.message(F.text.startswith("نسبة الحب"))
async def cmd_love(m: types.Message):
    await m.reply(f"❤️ نسبة التوافق: `{random.randint(0, 100)}%`", parse_mode="Markdown")

# القسم 4: الـ AI والـ Anatomy (أوامر منفصلة)
@dp.message(Command("ai"))
async def cmd_ai(m: types.Message):
    await m.answer("🤖 **AI Dashboard**\nنظام التلخيص وتوليد الصور جاهز للربط قريباً!")

@dp.message(Command("anatomy"))
async def cmd_anatomy(m: types.Message):
    await m.answer("🦴 **Medical Atlas**\nجاري تجهيز عرض الـ 3D Anatomy لموقعك.")

# ==========================================
# ⚔️ [ 7. محرك الإدارة الفولاذي ]
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_handler(m: types.Message):
    if m.content_type in {'new_chat_members', 'left_chat_member'}:
        try: await m.delete(); return
        except: pass

    # نظام الـ Tap-to-Earn (تجميع النقاط من الشات)
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    text = (m.text or "").lower()
    if any(w in text for w in BAD_WORDS):
        adm = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if adm.status not in ["administrator", "creator"]:
            try: await m.delete(); return
            except: pass

    # أوامر الرد (كتم، حظر، إنذار) - كل واحد لوحده وبأزرار أقل
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
# 💼 [ 8. الخاص والمطور (تنظيم الأزرار) ]
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def start_p(m: types.Message):
    if not await is_sub(m.from_user.id):
        kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="✅ اشترك لتفعيل البوت", url=CHANNEL_LINK))
        return await m.answer(f"⚠️ **مرحباً {m.from_user.first_name}\!**\nعذراً، اشترك بالقناة أولاً لتشغيل مميزات البوت\.", reply_markup=kb.as_markup())
    
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,)); conn.commit()
    
    # أزرار قليلة جداً ومنظمة
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ أضفني لجروبك", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    kb.row(InlineKeyboardButton(text="📢 القناة", url=CHANNEL_LINK), InlineKeyboardButton(text="🛠️ المطور", url="https://t.me/MBABmbab"))
    
    await m.answer(f"👑 **MB Gold Supreme**\nالبوت شغال بكل المميزات (إدارة، نقاط، AI، ألعاب)\. أضفني الآن لجروبك واستمتع\.", reply_markup=kb.as_markup())

@dp.message(Command("cast"), F.from_user.id == ADMIN_ID)
async def cmd_cast(m: types.Message):
    txt = m.text.replace("/cast", "").strip()
    if not txt: return await m.answer("اكتب الرسالة!")
    db.execute("SELECT user_id FROM users"); u_list = db.fetchall()
    c = 0
    for u in u_list:
        try: await bot.send_message(u[0], f"📢 **إعلان:**\n\n{txt}"); c += 1; await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ تم الإرسال لـ {c} مستخدم.")

# ==========================================
# 🚀 [ 9. تشغيل Railway وإصلاح الرد ]
# ==========================================
async def handle_home(request): return web.Response(text="MB Gold System is Online")

async def main():
    # أهم خطوة لضمان الرد: حذف الويب هوك القديم
    await bot.delete_webhook(drop_pending_updates=True)
    
    # تشغيل سيرفر الويب لريلاوي
    app = web.Application(); app.router.add_get('/', handle_home)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    
    print("🔥 MB Gold Clean Elite is LIVE!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
