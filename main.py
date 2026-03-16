import asyncio
import sqlite3
import time
import requests
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# تحميل البيانات من الخزنة (.env)
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = os.getenv('CHANNEL_ID')
MY_WALLET = os.getenv('MY_WALLET')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('mb_gold.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, expire_at REAL)')
db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
db.execute('CREATE TABLE IF NOT EXISTS processed_tx (tx_hash TEXT PRIMARY KEY)')
db.execute("INSERT OR IGNORE INTO settings VALUES ('price', '1.0')")
conn.commit()

# --- [ دوائر النظام ] ---
async def check_payment(price):
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=10"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("ok"):
            for tx in res["result"]:
                val = int(tx["in_msg"]["value"]) / 1e9
                tx_hash = tx["transaction_id"]["hash"]
                if val >= price:
                    db.execute("SELECT tx_hash FROM processed_tx WHERE tx_hash=?", (tx_hash,))
                    if not db.fetchone():
                        db.execute("INSERT INTO processed_tx VALUES (?)", (tx_hash,))
                        conn.commit()
                        return True
    except: return False
    return False

async def auto_kick():
    while True:
        db.execute("SELECT user_id FROM subs WHERE expire_at < ?", (time.time(),))
        expired = db.fetchall()
        for (u_id,) in expired:
            try:
                await bot.ban_chat_member(CHANNEL_ID, u_id)
                await bot.unban_chat_member(CHANNEL_ID, u_id)
                db.execute("DELETE FROM subs WHERE user_id=?", (u_id,))
                conn.commit()
                await bot.send_message(u_id, "⚠️ انتهى اشتراكك الـ VIP!")
            except: pass
        await asyncio.sleep(3600)

# --- [ الأوامر ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users VALUES (?)", (m.from_user.id,))
    conn.commit()
    db.execute("SELECT value FROM settings WHERE key='price'")
    p = db.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💎 اشتراك ({p} TON)", callback_data="pay")],
        [InlineKeyboardButton(text="🔄 تحقق من الدفع", callback_data="verify")]
    ])
    await m.answer(f"🔱 أهلاً بك يا {m.from_user.first_name}\nللاشتراك حول `{p}` TON لعنواننا:\n`{MY_WALLET}`", reply_markup=kb)

@dp.callback_query(F.data == "verify")
async def verify(call: types.CallbackQuery):
    db.execute("SELECT value FROM settings WHERE key='price'")
    p = float(db.fetchone()[0])
    await call.message.answer("⏳ نراجع البلوكشين...")
    if await check_payment(p):
        expire = time.time() + (30*24*60*60)
        db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?)", (call.from_user.id, expire))
        conn.commit()
        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        await call.message.answer(f"✅ تم التأكيد! الرابط:\n{link.invite_link}")
    else:
        await call.message.answer("❌ لم نجد دفعاً جديداً.")

@dp.message(Command("admin"))
async def admin(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM subs")
    count = db.fetchone()[0]
    await m.answer(f"🛠 لوحة التحكم\nالمشتركين: {count}\nالسعر الحالي: {os.getenv('price', '1.0')} TON")

async def main():
    asyncio.create_task(auto_kick())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
