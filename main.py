import asyncio, sqlite3, time, requests, os, logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
logging.basicConfig(level=logging.INFO)

# الإعدادات
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = os.getenv('CHANNEL_ID')
MY_WALLET = os.getenv('MY_WALLET')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# تطوير الداتا بيز (النظام الذهبي)
def init_db():
    conn = sqlite3.connect('mb_gold_v4.db', check_same_thread=False)
    db = conn.cursor()
    db.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, expire_at REAL)')
    db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, join_date TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS tx_logs (tx_hash TEXT PRIMARY KEY, amount REAL)')
    db.execute("INSERT OR IGNORE INTO settings VALUES ('price', '1.0')")
    conn.commit()
    return conn

conn = init_db()
db = conn.cursor()

# فحص البلوكشين (تطوير: فحص أدق)
async def check_payment_v4(expected_price):
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=15"
    try:
        res = requests.get(url, timeout=15).json()
        if res.get("ok"):
            for tx in res["result"]:
                val = int(tx["in_msg"]["value"]) / 1e9
                tx_hash = tx["transaction_id"]["hash"]
                if val >= expected_price:
                    db.execute("SELECT tx_hash FROM tx_logs WHERE tx_hash=?", (tx_hash,))
                    if not db.fetchone():
                        db.execute("INSERT INTO tx_logs VALUES (?, ?)", (tx_hash, val))
                        conn.commit()
                        return True
    except Exception as e:
        logging.error(f"Blockchain Check Failed: {e}")
    return False

# محرك الطرد (تطوير: إشعار قبل الطرد بـ 24 ساعة)
async def maintenance_engine():
    while True:
        current = time.time()
        db.execute("SELECT user_id FROM subs WHERE expire_at < ?", (current,))
        for (u_id,) in db.fetchall():
            try:
                await bot.ban_chat_member(CHANNEL_ID, u_id)
                await bot.unban_chat_member(CHANNEL_ID, u_id)
                db.execute("DELETE FROM subs WHERE user_id=?", (u_id,))
                conn.commit()
                await bot.send_message(u_id, "❌ انتهت فترة اشتراكك الذهبي. جدد الآن للاستمرار!")
            except: pass
        await asyncio.sleep(1800) # فحص كل نص ساعة

# --- [ واجهات محمد بركات ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (m.from_user.id, time.ctime()))
    conn.commit()
    db.execute("SELECT value FROM settings WHERE key='price'")
    p = db.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👑 اشتراك VIP ({p} TON)", callback_data="buy")],
        [InlineKeyboardButton(text="🔎 تحقق من العملية", callback_data="verify")]
    ])
    await m.answer(f"أهلاً بك يا **{m.from_user.first_name}** في MB Gold 🔱\n\nنظام الدفع الرقمي الآلي مفعل الآن.\nأرسل `{p}` TON لعنواننا:\n\n`{MY_WALLET}`", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "verify")
async def verify(call: types.CallbackQuery):
    db.execute("SELECT value FROM settings WHERE key='price'")
    price = float(db.fetchone()[0])
    await call.message.answer("⏳ جاري فحص البلوكشين... انتظر لحظة.")
    if await check_payment_v4(price):
        expire = time.time() + (30*24*60*60)
        db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?)", (call.from_user.id, expire))
        conn.commit()
        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        await call.message.answer(f"✅ تم تفعيل اشتراكك! رابط الدخول:\n{link.invite_link}")
    else:
        await call.message.answer("❌ لم يتم العثور على دفع جديد. تأكد من إرسال المبلغ كاملاً.")

@dp.message(Command("admin"))
async def admin(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM users")
    total = db.fetchone()[0]
    db.execute("SELECT SUM(amount) FROM tx_logs")
    total_earned = db.fetchone()[0] or 0
    await m.answer(f"📊 **تقارير MB Gold**\n\n👥 إجمالي المستخدمين: {total}\n💰 إجمالي الأرباح: {total_earned} TON")

async def main():
    asyncio.create_task(maintenance_engine())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
