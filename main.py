import asyncio, os, sqlite3, time, random, logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 👑 [ 1. الهوية الإمبراطورية والإعدادات ]
# ==========================================
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"
PORT = int(os.getenv("PORT", 8080))

# فلتر الكلمات البذيئة والروابط (موسع جداً)
BAD_WORDS = [
    "شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص", "متناك", 
    "سكس", "قحبة", "شرموط", "منيوك", "كوسة", "بضان", "تحميل", "اشترك"
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 💾 [ 2. قاعدة البيانات المركزية (المصنع) ]
# ==========================================
conn = sqlite3.connect('mb_gold_infinite.db', check_same_thread=False)
db = conn.cursor()
# مستخدمين ونقاط (أساس الـ Tap-to-Earn)
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, balance REAL DEFAULT 0.0)')
# جروبات مفعلة
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT, status TEXT DEFAULT "active")')
# نظام الإنذارات
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# ==========================================
# 🛡️ [ 3. درع الحماية الذكي (Anti-Flood) ]
# ==========================================
class UltimateMiddleware(BaseMiddleware):
    def __init__(self, limit=1.0):
        self.last_user_time = {}
        super().__init__()
    async def __call__(self, handler, event, data):
        if not event.from_user: return await handler(event, data)
        uid = event.from_user.id
        now = time.time()
        if uid in self.last_user_time and now - self.last_user_time[uid] < limit: return
        self.last_user_time[uid] = now
        return await handler(event, data)

dp.message.middleware(UltimateMiddleware())

# ==========================================
# 🔐 [ 4. المحركات المساعدة (فحص القناة والرتب) ]
# ==========================================
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USER}", user_id)
        return member.status not in ["left", "kicked"]
    except: return True

def calculate_rank(p, uid):
    if uid == ADMIN_ID: return "المطور الإمبراطوري 👑"
    if p >= 5000: return "الملك الذهبي 🏆"
    if p >= 1000: return "الأسطورة VIP 💎"
    if p >= 500: return "عضو ماسي 💠"
    if p >= 100: return "عضو ذهبي 🥇"
    return "عضو ناشئ 🌱"

# ==========================================
# 🤖 [ 5. نظام الـ Captcha والترحيب الاحترافي ]
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def join_handler(event: ChatMemberUpdated):
    user = event.from_user
    try:
        # تقييد فوري
        await bot.restrict_chat_member(event.chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ إثبات الهوية (أنا إنسان)", callback_data=f"v_{user.id}"))
        kb.row(InlineKeyboardButton(text="📢 القناة الرسمية", url=CHANNEL_LINK))
        await bot.send_message(
            event.chat.id, 
            f"🔱 **مرحباً بك {user.mention_markdown()} في عائلة MB Gold\!**\n\n"
            f"🛡️ نظام الحماية مفعل، اضغط على الزر أدناه لتتمكن من الدردشة في المجموعة\.",
            parse_mode="MarkdownV2", reply_markup=kb.as_markup()
        )
    except: pass

@dp.callback_query(F.data.startswith("v_"))
async def verify_callback(call: types.CallbackQuery):
    target = int(call.data.split("_")[1])
    if call.from_user.id != target: return await call.answer("❌ الزر ليس لك!", show_alert=True)
    await bot.restrict_chat_member(call.message.chat.id, target, permissions=ChatPermissions(
        can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True
    ))
    await call.message.delete()
    await call.answer("✅ تم فك القيود، استمتع!", show_alert=True)

# ==========================================
# 🎮 [ 6. الترفيه، النقاط، وبطاقة الهوية ]
# ==========================================
@dp.message(F.text.in_({"ايدي", "ID", "ملفي", "ايديه"}))
async def profile_card(m: types.Message):
    db.execute('SELECT points, balance FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone()
    pts, bal = (res[0], res[1]) if res else (0, 0.0)
    rank = calculate_rank(pts, m.from_user.id)
    
    msg = (
        f"🔱 **بـطـاقـة نـخـبـة MB Gold**\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **الاسم:** {m.from_user.first_name}\n"
        f"🆔 **الأيدي:** `{m.from_user.id}`\n"
        f"🏆 **الرتبة:** {rank}\n"
        f"✨ **النقاط:** {pts}\n"
        f"💰 **الرصيد:** {bal}$\n"
        f"━━━━━━━━━━━━━━\n"
        f"📢 [انضم للقناة لتفعيل الجوائز]({CHANNEL_LINK})"
    )
    await m.answer(msg, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(F.text == "حظي")
async def luck_game(m: types.Message):
    ans = ["ذهبي 👑", "سعيد جداً 🎁", "مليء بالأكواد 💻", "هادئ 🌊", "محظوظ ✨"]
    await m.reply(f"🔮 **حظك اليوم:** `{random.choice(ans)}`")

@dp.message(F.text.startswith("نسبة الحب"))
async def love_game(m: types.Message):
    await m.reply(f"❤️ **نسبة التوافق:** `{random.randint(0, 100)}%`")

# ==========================================
# ⚔️ [ 7. محرك المجموعات والإدارة بالرد ]
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_engine(m: types.Message):
    # مسح رسائل الدخول/الخروج
    if m.content_type in {'new_chat_members', 'left_chat_member'}:
        try: await m.delete()
        except: pass
        return

    # تسجيل الجروب وتزويد النقاط (Mining)
    db.execute('INSERT OR IGNORE INTO groups (chat_id, title) VALUES (?, ?)', (m.chat.id, m.chat.title))
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    text = (m.text or m.caption or "").lower()
    # نظام الفلترة
    if any(w in text for w in BAD_WORDS):
        chk = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if chk.status not in ["administrator", "creator"]:
            try: await m.delete(); return
            except: pass

    # أوامر الإدارة بالرد (الحظر، الكتم، الإنذار)
    if m.reply_to_message:
        me_admin = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if me_admin.status in ["administrator", "creator"] or m.from_user.id == ADMIN_ID:
            t_id = m.reply_to_message.from_user.id
            t_name = m.reply_to_message.from_user.first_name
            
            if text in ["حظر", "/ban"]:
                await bot.ban_chat_member(m.chat.id, t_id)
                await m.answer(f"🚫 تم طرد {t_name} نهائياً\.")
            elif text in ["كتم", "/mute"]:
                await bot.restrict_chat_member(m.chat.id, t_id, permissions=ChatPermissions(can_send_messages=False))
                await m.answer(f"🤐 تم كتم {t_name} عن الكلام\.")
            elif text in ["فك الكتم", "/unmute"]:
                await bot.restrict_chat_member(m.chat.id, t_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
                await m.answer(f"🔊 تم فك الكتم عن {t_name}\.")
            elif text in ["تثبيت", "/pin"]:
                await bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
                await m.answer("📌 تم التثبيت بنجاح\.")
            elif text in ["انذار", "/warn"]:
                db.execute('INSERT OR IGNORE INTO warns VALUES (?, ?, 0)', (m.chat.id, t_id))
                db.execute('UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?', (m.chat.id, t_id))
                conn.commit()
                db.execute('SELECT count FROM warns WHERE chat_id = ? AND user_id = ?', (m.chat.id, t_id))
                cnt = db.fetchone()[0]
                if cnt >= 3:
                    await bot.ban_chat_member(m.chat.id, t_id)
                    await m.answer(f"🚫 طرد {t_name} لتجاوزه 3 إنذارات\.")
                    db.execute('UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?', (m.chat.id, t_id))
                    conn.commit()
                else:
                    await m.answer(f"⚠️ إنذار ({cnt}/3) للعضو {t_name}\.")

# ==========================================
# 💼 [ 8. أوامر المطور (الإذاعة والإحصائيات) ]
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def private_welcome(m: types.Message):
    if not await is_subscribed(m.from_user.id):
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="✅ اشترك الآن لتفعيل البوت", url=CHANNEL_LINK))
        return await m.answer(f"⚠️ **مرحباً {m.from_user.first_name}\!**\nعذراً، يجب عليك الاشتراك في القناة لتشغيل مميزات MB Gold\.", reply_markup=kb.as_markup())
    
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,)); conn.commit()
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ أضفني لجروبك", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    kb.row(InlineKeyboardButton(text="💎 القناة الرسمية", url=CHANNEL_LINK))
    await m.answer(f"🔱 **أهلاً بك في نظام MB Gold المتكامل\!**\n\nأنا الآن بوت إداري، ترفيهي، ومحرك نقاط\. أضفني لمجموعتك واستمتع بالتحكم الكامل\.", reply_markup=kb.as_markup())

@dp.message(Command("cast"), F.from_user.id == ADMIN_ID)
async def admin_broadcast(m: types.Message):
    txt = m.text.replace("/cast", "").strip()
    if not txt: return await m.answer("اكتب الرسالة بعد الأمر!")
    db.execute("SELECT user_id FROM users"); u_list = db.fetchall()
    ok = 0
    for u in u_list:
        try: await bot.send_message(u[0], f"📢 **إشعار إمبراطوري:**\n\n{txt}"); ok += 1; await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ تم الإرسال لـ {ok} عضو\.")

@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(m: types.Message):
    db.execute("SELECT COUNT(*) FROM users"); u_c = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM groups"); g_c = db.fetchone()[0]
    await m.answer(f"📊 **الإحصائيات الحالية:**\n\n👤 المستخدمين: {u_c}\n🛡️ المجموعات: {g_c}")

# ==========================================
# 🚀 [ 9. الحل النهائي لعدم الرد + تشغيل Railway ]
# ==========================================
async def health_check(request): return web.Response(text="MB Gold: Alive and Responding!")

async def main():
    # 1. مسح أي رسايل معلقة (عشان ميهنجش)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 2. تشغيل سيرفر الويب (عشان ريلاوي ميفصلش)
    app = web.Application(); app.router.add_get('/', health_check)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    
    print("🔥 MB Gold Version 10: Infinite is LIVE!")
    # 3. تشغيل استقبال الرسايل (القلب النابض)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot Stopped!")
