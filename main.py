import asyncio, sqlite3, time, requests, os, logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# تحميل المتغيرات من السيرفر (للأمان القصوى يا محمد)
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 6363223356))
CHANNEL_ID = os.getenv('CHANNEL_ID', '@MBABmbab')
MY_WALLET = 'UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ تطوير قاعدة البيانات: الحفاظ على البيانات من الضياع ] ---
def init_db():
    conn = sqlite3.connect('mb_gold_pro.db', check_same_thread=False)
    db = conn.cursor()
    db.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, expire_at REAL)')
    db.execute('CREATE TABLE IF NOT EXISTS tx_log (tx_hash TEXT PRIMARY KEY)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    db.execute("INSERT OR IGNORE INTO settings VALUES ('price', '1.0')")
    conn.commit()
    return conn

conn = init_db()
db = conn.cursor()

# --- [ نظام فحص الدفع المتطور ] ---
async def verify_payment(expected_amount):
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=10"
    try:
        r = requests.get(url, timeout=12).json()
        if r.get("ok"):
            for tx in r["result"]:
                val = int(tx["in_msg"]["value"]) / 1e9
                hsh = tx["transaction_id"]["hash"]
                if val >= expected_amount:
                    db.execute("SELECT tx_hash FROM tx_log WHERE tx_hash=?", (hsh,))
                    if not db.fetchone():
                        db.execute("INSERT INTO tx_log VALUES (?)", (hsh,))
                        conn.commit()
                        return True
    except: return False
    return False

# --- [ محرك الإدارة التلقائي ] ---
async def auto_manager():
    while True:
        # طرد الأعضاء الذين انتهى اشتراكهم
        db.execute("SELECT user_id FROM subs WHERE expire_at < ?", (time.time(),))
        expired_users = db.fetchall()
        for (uid,) in expired_users:
            try:
                await bot.ban_chat_member(CHANNEL_ID, uid)
                await bot.unban_chat_member(CHANNEL_ID, uid)
                db.execute("DELETE FROM subs WHERE user_id=?", (uid,))
                conn.commit()
                await bot.send_message(uid, "⚠️ انتهى اشتراكك في MB Gold. ننتظرك للتجديد!")
            except: pass
        await asyncio.sleep(3600) # فحص كل ساعة

# --- [ أوامر المستخدمين ] ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    db.execute("SELECT value FROM settings WHERE key='price'")
    price = db.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👑 شراء اشتراك ({price} TON)", callback_data="buy")],
        [InlineKeyboardButton(text="🔄 تأكيد التحويل", callback_data="check")]
    ])
    await m.answer(f"🔱 أهلاً بك في نظام **MB Gold**\n\nللحصول على رابط القناة، حول `{price}` TON للمحفظة:\n`{MY_WALLET}`", reply_markup=kb)

@dp.callback_query(F.data == "check")
async def verify_click(call: types.CallbackQuery):
    db.execute("SELECT value FROM settings WHERE key='price'")
    price = float(db.fetchone()[0])
    await call.message.answer("⏳ جاري فحص البلوكشين...")
    if await verify_payment(price):
        expire = time.time() + (30*24*60*60)
        db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?)", (call.from_user.id, expire))
        conn.commit()
        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        await call.message.answer(f"✅ تم تفعيل الاشتراك! رابط الدخول:\n{link.invite_link}")
        await bot.send_message(ADMIN_ID, f"💰 عملية دفع جديدة من {call.from_user.full_name}")
    else:
        await call.message.answer("❌ لم نجد عملية دفع جديدة.")

# --- [ لوحة تحكم الإدارة ] ---
@dp.message(Command("admin"))
async def admin_panel(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM subs")
    subs_count = db.fetchone()[0]
    await m.answer(f"🛠 **لوحة التحكم - محمد بركات**\n\n👥 المشتركين الحاليين: {subs_count}\n📍 القناة: {CHANNEL_ID}")

async def main():
    asyncio.create_task(auto_manager())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
