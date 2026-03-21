import asyncio, os, sqlite3, time, random, logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 👑 [ الإعدادات العليا والهوية ]
# ==========================================
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"
PORT = int(os.getenv("PORT", 8080))
BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص", "متناك", "سكس"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 💾 [ قاعدة البيانات المدمجة ]
# ==========================================
conn = sqlite3.connect('mb_ultimate_master.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)')
db.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT)')
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# ==========================================
# 🛡️ [ Middleware: حماية من السبام والتكرار ]
# ==========================================
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit=2):
        self.last_from_user = {}
        super().__init__()
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = time.time()
        if user_id in self.last_from_user and now - self.last_from_user[user_id] < limit: return
        self.last_from_user[user_id] = now
        return await handler(event, data)

dp.message.middleware(AntiFloodMiddleware())

# ==========================================
# 🌐 [ خادم الويب - Railway Health ]
# ==========================================
async def handle(request): return web.Response(text="🏆 MB Gold Ultimate Masterpiece is LIVE!")
async def start_web():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# ==========================================
# 🔐 [ المحركات المساعدة ]
# ==========================================
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USER}", user_id)
        return member.status not in ["left", "kicked"]
    except: return True

def get_rank(points, user_id):
    if user_id == ADMIN_ID: return "المطور الملكي 👑"
    if points >= 500: return "VIP 💎"
    if points >= 200: return "عضو ذهبي 🥇"
    if points >= 50: return "عضو فضي 🥈"
    return "عضو برونزي 🥉"

# ==========================================
# 🤖 [ التحقق البشري والترحيب - Captcha ]
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_join_captcha(event: ChatMemberUpdated):
    user = event.from_user
    try:
        # تقييد العضو
        await bot.restrict_chat_member(event.chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        # إرسال زر التحقق
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ أنا إنسان (اضغط للتحقق)", callback_data=f"verify_{user.id}"))
        kb.row(InlineKeyboardButton(text="📢 اشترك بقناتنا", url=CHANNEL_LINK))
        
        await bot.send_message(
            event.chat.id, 
            f"🔱 أهلاً بك يا [{user.first_name}](tg://user?id={user.id})\n"
            f"🛡️ أنت الآن في حماية **MB Gold**.\n"
            f"يرجى الضغط على الزر أدناه لإثبات هويتك لتتمكن من الدردشة.", 
            parse_mode="Markdown", reply_markup=kb.as_markup()
        )
    except: pass

@dp.callback_query(F.data.startswith("verify_"))
async def verify_human(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    if call.from_user.id != target_id:
        return await call.answer("❌ هذا الزر مخصص للعضو الجديد فقط!", show_alert=True)
    
    await bot.restrict_chat_member(call.message.chat.id, target_id, permissions=ChatPermissions(
        can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True
    ))
    await call.message.delete()
    await call.answer("✅ تم التحقق بنجاح! نورت الجروب.", show_alert=True)

# ==========================================
# 🎮 [ الترفيه، البرستيج، والأوامر العامة ]
# ==========================================
@dp.message(F.text.in_({"ايدي", "ID", "ايديه", "ملفي"}))
async def show_profile(m: types.Message):
    db.execute('SELECT points FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone()
    points = res[0] if res else 0
    rank = get_rank(points, m.from_user.id)
    
    card = (
        f"🔱 **بـطـاقـة نـخـبـة MB Gold**\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **الاسم:** {m.from_user.first_name}\n"
        f"🆔 **المعرف:** `{m.from_user.id}`\n"
        f"🏆 **الرتبة:** {rank}\n"
        f"✨ **النقاط:** {points}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📢 [انضم لقناتنا الرسمية]({CHANNEL_LINK})"
    )
    await m.answer(card, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(F.text == "حظي")
async def game_luck(m: types.Message):
    lucks = ["حظك اليوم ذهبي 🌟", "يوم مليء بالأكواد الناجحة 💻", "خبر سعيد في الطريق إليك ⚡", "ركز في مشروعك القادم 🚀", "احذر من المتطفلين اليوم 👀"]
    await m.reply(f"🔮 **توقعات MB Gold:**\n`{random.choice(lucks)}`", parse_mode="Markdown")

@dp.message(F.text.startswith("نسبة الحب"))
async def game_love(m: types.Message):
    await m.reply(f"❤️ **نسبة التوافق هي:** `{random.randint(0, 100)}%`", parse_mode="Markdown")

# ==========================================
# 💼 [ واجهة المطور والخاص (التسويق) ]
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def private_start(m: types.Message):
    # الاشتراك الإجباري
    if not await check_sub(m.from_user.id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ اشترك لتفعيل البوت", url=CHANNEL_LINK))
        return await m.answer(f"⚠️ **عذراً!**\nيجب عليك الاشتراك في قناة **MB Gold** أولاً لتتمكن من استخدام البوت.", parse_mode="Markdown", reply_markup=kb.as_markup())

    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    conn.commit()

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ أضفني لمجموعتك الآن", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    kb.row(InlineKeyboardButton(text="📢 قناة المطور", url=CHANNEL_LINK), InlineKeyboardButton(text="🔗 دعوة صديق", switch_inline_query="جرب هذا البوت الأسطوري!"))
    
    await m.answer(
        f"👑 **مرحباً بك في نظام MB Gold المتكامل**\n\n"
        f"أنت الآن تستخدم أقوى منظومة حماية، إدارة، وترفيه على تليجرام.\n"
        f"✅ حسابك مفعل (VIP)\n\n"
        f"اضغط أدناه لإضافة البوت لمجموعتك.",
        parse_mode="Markdown", reply_markup=kb.as_markup()
    )

@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(m: types.Message):
    db.execute("SELECT COUNT(*) FROM users")
    u_count = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM groups")
    g_count = db.fetchone()[0]
    await m.answer(f"📊 **إحصائيات الإمبراطورية:**\n👥 مستخدمين: {u_count}\n🛡️ جروبات: {g_count}")

@dp.message(Command("cast"), F.from_user.id == ADMIN_ID)
async def admin_cast(m: types.Message):
    msg = m.text.replace("/cast", "").strip()
    if not msg: return await m.answer("اكتب الرسالة بعد الأمر!")
    db.execute("SELECT user_id FROM users")
    users = db.fetchall()
    count = 0
    await m.answer("⏳ جاري الإذاعة...")
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 **إعلان هام:**\n\n{msg}")
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ تم الإرسال إلى {count} شخص.")

# ==========================================
# ⚔️ [ أوامر المشرفين وإدارة الجروبات ]
# ==========================================
@dp.message(Command("admin"))
async def admin_dashboard(m: types.Message):
    user = await bot.get_chat_member(m.chat.id, m.from_user.id)
    if user.status not in ["administrator", "creator"] and m.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔒 قفل الشات", callback_data="lock_chat"), InlineKeyboardButton(text="🔓 فتح الشات", callback_data="unlock_chat"))
    await m.answer("🎛 **لوحة تحكم المشرفين:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.in_({"lock_chat", "unlock_chat"}))
async def toggle_chat(call: types.CallbackQuery):
    perms = False if call.data == "lock_chat" else True
    await bot.set_chat_permissions(call.message.chat.id, ChatPermissions(can_send_messages=perms, can_send_media_messages=perms, can_send_other_messages=perms))
    await call.answer("تم تنفيذ الأمر بنجاح 🛡️", show_alert=True)

# ==========================================
# 🛡️ [ المحرك الرئيسي: الحماية + التفاعل + الأوامر ]
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_master_handler(m: types.Message):
    # 1. مسح رسائل الخدمة المزعجة
    if m.content_type in {'new_chat_members', 'left_chat_member'}:
        try: await m.delete()
        except: pass
        return

    # 2. تسجيل الجروب وتحديث نقاط الأعضاء (Gamification)
    db.execute('INSERT OR IGNORE INTO groups VALUES (?, ?)', (m.chat.id, m.chat.title))
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    text = (m.text or m.caption or "").lower()
    if not text: return

    # 3. فلتر الحماية (الكلمات والروابط)
    if any(w in text for w in BAD_WORDS):
        user = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if user.status not in ["administrator", "creator"]:
            try:
                await m.delete()
                warning = await m.answer(f"⚠️ يمنع إرسال الكلمات المسيئة أو الروابط يا [{m.from_user.first_name}](tg://user?id={m.from_user.id})!", parse_mode="Markdown")
                await asyncio.sleep(4)
                await warning.delete()
            except: pass
            return

    # 4. أوامر المشرفين بالرد (Reply Commands)
    if m.reply_to_message:
        target_id = m.reply_to_message.from_user.id
        target_name = m.reply_to_message.from_user.first_name
        
        # التأكد إن اللي بيدي الأمر مشرف
        admin_check = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if admin_check.status in ["administrator", "creator"] or m.from_user.id == ADMIN_ID:
            
            if text in ["/ban", "حظر"]:
                try: 
                    await bot.ban_chat_member(m.chat.id, target_id)
                    await m.answer(f"🚫 تم حظر {target_name} بنجاح.")
                except: pass
            
            elif text in ["/mute", "كتم"]:
                try:
                    await bot.restrict_chat_member(m.chat.id, target_id, permissions=ChatPermissions(can_send_messages=False))
                    await m.answer(f"🤐 تم كتم {target_name}.")
                except: pass
                
            elif text in ["/unmute", "فك الكتم"]:
                try:
                    await bot.restrict_chat_member(m.chat.id, target_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True))
                    await m.answer(f"🔊 تم فك الكتم عن {target_name}.")
                except: pass
                
            elif text in ["/pin", "تثبيت"]:
                try:
                    await bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
                    await m.answer("📌 تم التثبيت.")
                except: pass
                
            elif text in ["/warn", "انذار"]:
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
                    await m.answer(f"⚠️ إنذار ({warns}/3) لـ {target_name}.")

    # 5. أوامر المشرفين العامة (بدون رد)
    admin_check = await bot.get_chat_member(m.chat.id, m.from_user.id)
    if admin_check.status in ["administrator", "creator"] or m.from_user.id == ADMIN_ID:
        if text in ["/lock", "قفل الجروب"]:
            try:
                await bot.set_chat_permissions(m.chat.id, ChatPermissions(can_send_messages=False))
                await m.answer("🔒 تم إغلاق الجروب بواسطة الإدارة.")
            except: pass
        elif text in ["/unlock", "فتح الجروب"]:
            try:
                await bot.set_chat_permissions(m.chat.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
                await m.answer("🔓 تم فتح الجروب، يمكنكم التحدث الآن.")
            except: pass

# ==========================================
# 🚀 [ الإطلاق والتنظيف ]
# ==========================================
async def main():
    # تنظيف أي رسايل معلقة عشان البوت ميهنجش
    print("🧹 جارٍ تنظيف الشبكة...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # تشغيل السيرفر
    asyncio.create_task(start_web())
    
    print("🔥 MB Gold Ultimate Masterpiece is ONLINE & ROARING!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
