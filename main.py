import asyncio, sqlite3, time, requests, os, logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
# تقليل مستوى الـ Logging عشان السيرفر ما يستهلكش موارد كتير
logging.basicConfig(level=logging.ERROR)

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = os.getenv('CHANNEL_ID')
MY_WALLET = os.getenv('MY_WALLET')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# قاعدة بيانات خفيفة وسريعة
conn = sqlite3.connect('mb_gold_stable.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, expire_at REAL)')
db.execute('CREATE TABLE IF NOT EXISTS tx_cache (tx_hash TEXT PRIMARY KEY)')
conn.commit()

async def check_payment_fast(price):
    """فحص سريع للبلوكشين مع تقليل استهلاك الـ API"""
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=5"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("ok"):
            for tx in res["result"]:
                val = int(tx["in_msg"]["value"]) / 1e9
                tx_hash = tx["transaction_id"]["hash"]
                if val >= price:
                    db.execute("SELECT tx_hash FROM tx_cache WHERE tx_hash=?", (tx_hash,))
                    if not db.fetchone():
                        db.execute("INSERT INTO tx_cache VALUES (?)", (tx_hash,))
                        conn.commit()
                        return True
    except: return False
    return False

# محرك الطرد (فحص ذكي كل ساعة)
async def auto_kick_system():
    while True:
        try:
            db.execute("SELECT user_id FROM subs WHERE expire_at < ?", (time.time(),))
            expired = db.fetchall()
            for (u_id,) in expired:
                await bot.ban_chat_member(CHANNEL_ID, u_id)
                await bot.unban_chat_member(CHANNEL_ID, u_id)
                db.execute("DELETE FROM subs WHERE user_id=?", (u_id,))
                conn.commit()
                await bot.send_message(u_id, "🔔 اشتراكك انتهى، ننتظرك مجدداً في MB Gold!")
        except: pass
        await asyncio.sleep(3600)

@dp.message(Command("start"))
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 اشتراك 1 TON", callback_data="buy")],
        [InlineKeyboardButton(text="🔄 تحقق سريع", callback_data="verify")]
    ])
    await m.answer(f"مرحباً بك في **MB Gold** 🔱\n\nحول 1 TON للمحفظة:\n`{MY_WALLET}`", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "verify")
async def verify(call: types.CallbackQuery):
    await call.message.answer("⏳ جاري الفحص السريع...")
    if await check_payment_fast(1.0):
        expire = time.time() + (30*24*60*60)
        db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?)", (call.from_user.id, expire))
        conn.commit()
        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        await call.message.answer(f"✅ تم التفعيل! تفضل الرابط:\n{link.invite_link}")
    else:
        await call.message.answer("❌ لم نجد دفعاً جديداً بعد.")

async def main():
    # إشعار للمدير إن السيرفر اشتغل بنجاح
    try: await bot.send_message(ADMIN_ID, "🚀 MB Gold Server is Online!")
    except: pass
    asyncio.create_task(auto_kick_system())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
