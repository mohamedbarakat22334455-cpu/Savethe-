import asyncio, os, sqlite3, time, logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- [ إعدادات النظام ] ---
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
OFFICIAL_CHANNEL = "MBABmbab"
PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('mb_final.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, anti_link INTEGER DEFAULT 1)')
conn.commit()

# --- [ Middleware: حماية من الإغراق/السبام ] ---
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit=2):
        self.last_from_user = {}
        super().__init__()
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = time.time()
        if user_id in self.last_from_user and now - self.last_from_user[user_id] < limit:
            return
        self.last_from_user[user_id] = now
        return await handler(event, data)

dp.message.middleware(AntiFloodMiddleware())

# ==========================================
# 🌐 1. Server Health (Railway)
# ==========================================
async def handle(request): return web.Response(text="MB Gold is Live!")
async def start_web():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# ==========================================
# 🛡️ 2. نظام التحقق البشري (Captcha)
# ==========================================
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user = event.from_user
    try:
        await bot.restrict_chat_member(event.chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="✅ اضغط للتحقق (60 ثانية)", callback_data=f"v_{user.id}"))
        await bot.send_message(event.chat.id, f"🔱 أهلاً {user.mention_markdown()}\! إثبت إنك مش بوت بالضغط أدناه\.", parse_mode="MarkdownV2", reply_markup=kb.as_markup())
    except: pass

@dp.callback_query(F.data.startswith("v_"))
async def verify(call: types.CallbackQuery):
    u_id = int(call.data.split("_")[1])
    if call.from_user.id != u_id: return await call.answer("الزر مش ليك!", show_alert=True)
    await bot.restrict_chat_member(call.message.chat.id, u_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await call.message.delete()
    await call.answer("تم التحقق بنجاح! 👑")

# ==========================================
# ⚙️ 3. لوحة التحكم (Admin Panel)
# ==========================================
@dp.message(Command("settings"))
async def settings(m: types.Message):
    user = await bot.get_chat_member(m.chat.id, m.from_user.id)
    if user.status not in ["administrator", "creator"] and m.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔒 قفل الشات", callback_data="l_c"), InlineKeyboardButton(text="🔓 فتح الشات", callback_data="u_c"))
    await m.answer("⚙️ **إعدادات حماية MB Gold:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.in_({"l_c", "u_c"}))
async def lock_unlock(call: types.CallbackQuery):
    perms = False if call.data == "l_c" else True
    await bot.set_chat_permissions(call.message.chat.id, ChatPermissions(can_send_messages=perms))
    await call.answer("تم تنفيذ الأمر بنجاح!")

# ==========================================
# 👑 4. الواجهة والخدمات (Start)
# ==========================================
@dp.message(CommandStart())
async def start(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💠 القناة الرسمية", url=f"https://t.me/{OFFICIAL_CHANNEL}"))
    kb.row(InlineKeyboardButton(text="➕ أضفني لمجموعتك", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    await m.answer(f"🔱 **أهلاً بك في عالم MB Gold Infinity**\n\nنظام الحماية الأكثر تطوراً في تليجرام جاهز لخدمتك الآن\.", parse_mode="MarkdownV2", reply_markup=kb.as_markup())

# ==========================================
# 🚀 5. التشغيل الذكي (The Fix)
# ==========================================
async def main():
    # الخطوة اللي بتصلح الـ "مبيردش"
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(start_web())
    print("🔥 MB Gold Infinity is Roaring!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
