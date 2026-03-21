import asyncio, os, sqlite3, time, random, logging, threading
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 👑 [ 1. الإعدادات والتوكنات ]
# ==========================================
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"
PORT = int(os.getenv("PORT", 8080))

BAD_WORDS = ["شتيمة", "t.me/", "http", "زفت", "إعلان", "كسم", "عرص", "متناك", "سكس", "قحبة", "شرموط"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 💾 [ 2. قاعدة البيانات ]
# ==========================================
conn = sqlite3.connect('mb_gold_v3.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, balance REAL DEFAULT 0.0, wallet TEXT DEFAULT "لم تسجل")')
db.execute('CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))')
conn.commit()

# ==========================================
# 🔐 [ 3. التحقق والاشتراك ]
# ==========================================
async def is_subscribed(uid):
    try:
        m = await bot.get_chat_member(f"@{CHANNEL_USER}", uid)
        return m.status not in ["left", "kicked"]
    except: return True

# ==========================================
# 🤖 [ 4. نظام الترحيب والتحقق ]
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def welcome_logic(event: ChatMemberUpdated):
    user = event.from_user
    try:
        await bot.restrict_chat_member(event.chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="✅ أنا إنسان (تحقق)", callback_data=f"v_{user.id}"))
        await bot.send_message(event.chat.id, f"🔱 أهلاً {user.first_name}\! اضغط للتحقق وفتح المميزات\.", parse_mode="MarkdownV2", reply_markup=kb.as_markup())
    except: pass

@dp.callback_query(F.data.startswith("v_"))
async def verify_done(call: types.CallbackQuery):
    tid = int(call.data.split("_")[1])
    if call.from_user.id != tid: return await call.answer("❌ الزر ليس لك!", show_alert=True)
    await bot.restrict_chat_member(call.message.chat.id, tid, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await call.message.delete()
    await call.answer("✅ تم التحقق!", show_alert=True)

# ==========================================
# 🎮 [ 5. الأوامر (كل حاجة لوحدها) ]
# ==========================================

@dp.message(F.text.in_({"ايدي", "ID", "ملفي"}))
async def cmd_id(m: types.Message):
    db.execute('SELECT points, balance, wallet FROM users WHERE user_id = ?', (m.from_user.id,))
    res = db.fetchone(); pts, bal, wal = (res[0], res[1], res[2]) if res else (0, 0.0, "غير مسجل")
    await m.answer(f"🔱 **نخبة MB Gold**\n━━━━━━━━━━━━\n👤 الاسم: {m.from_user.first_name}\n🆔 الأيدي: `{m.from_user.id}`\n✨ النقاط: {pts}\n💰 الرصيد: {bal}$\n💳 المحفظة: `{wal}`\n━━━━━━━━━━━━", parse_mode="Markdown")

@dp.message(Command("anatomy"))
async def cmd_anatomy(m: types.Message):
    await m.answer("🦴 **Medical Atlas 3D**\nمرحباً بك في نظام التشريح ثلاثي الأبعاد\. الأجزاء جاهزة للعرض قريباً\.")

@dp.message(Command("ai"))
async def cmd_ai(m: types.Message):
    await m.answer("🤖 **AI Blueprint**\nنظام الذكاء الاصطناعي الخاص بـ MB Gold قيد التشغيل\.")

# ==========================================
# ⚔️ [ 6. محرك الإدارة (بالرد) ]
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_handler(m: types.Message):
    # زيادة النقاط تلقائياً
    db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (m.from_user.id,))
    db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (m.from_user.id,))
    conn.commit()

    text = (m.text or "").lower()
    if m.reply_to_message:
        adm = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if adm.status in ["administrator", "creator"] or m.from_user.id == ADMIN_ID:
            tid = m.reply_to_message.from_user.id
            if text in ["حظر", "/ban"]: await bot.ban_chat_member(m.chat.id, tid); await m.answer("🚫 تم الحظر.")
            elif text in ["كتم", "/mute"]: await bot.restrict_chat_member(m.chat.id, tid, permissions=ChatPermissions(can_send_messages=False)); await m.answer("🤐 تم الكتم.")

# ==========================================
# 🚀 [ 7. تشغيل السيرفر (الحل النهائي للرد) ]
# ==========================================

# وظيفة سيرفر الويب لـ Railway
def run_web():
    async def handle(request): return web.Response(text="MB Gold Is Live")
    app = web.Application()
    app.router.add_get('/', handle)
    web.run_app(app, host='0.0.0.0', port=PORT)

async def main():
    # أهم خطوة: مسح الرسايل القديمة عشان يرد فوراً
    await bot.delete_webhook(drop_pending_updates=True)
    
    # تشغيل سيرفر الويب في خلفية منفصلة تماماً
    threading.Thread(target=run_web, daemon=True).start()
    
    print("🔥 MB Gold is LIVE and Responding!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        pass
