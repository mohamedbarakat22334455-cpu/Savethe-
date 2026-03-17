import asyncio, sqlite3, os, requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- [ الإعدادات الرسمية ] ---
API_TOKEN = '8758046360:AAF8ilMxOrEHLr08fOGc5yZlT5blrByj1zs'
ADMIN_ID = 6363223356
CHANNEL_ID = -1002345678901 # تأكد من وضع ID قناتك هنا (رقم فقط)
MY_WALLET = 'UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('mb_guard.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, warnings INTEGER DEFAULT 0)')
db.execute('CREATE TABLE IF NOT EXISTS hash_log (h TEXT PRIMARY KEY)')
conn.commit()

# --- [ قائمة الحماية ] ---
BAD_WORDS = ["شتيمة", "إعلان", "t.me/", "http"]

# --- [ نظام الحماية ] ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def guard_system(m: types.Message):
    if any(word in m.text.lower() for word in BAD_WORDS):
        await m.delete()
        await m.answer(f"⚠️ ممنوع التجاوز يا {m.from_user.first_name}!")

# --- [ الأوامر ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 دخول القناة (1 TON)", callback_data="pay")],
        [InlineKeyboardButton(text="✅ تأكيد الدفع", callback_data="confirm")]
    ])
    await m.answer(f"🛡 **نظام حماية MB**\n\n- القناة محمية تماماً.\n- الدخول آمن وتلقائي.\n\nالمحفظة:\n`{MY_WALLET}`", reply_markup=kb)

@dp.callback_query(F.data == "confirm")
async def check_p(call: types.CallbackQuery):
    await call.message.answer("⏳ فحص البلوكشين...")
    try:
        r = requests.get(f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=5").json()
        if r.get("ok"):
            for tx in r["result"]:
                val = int(tx["in_msg"]["value"]) / 1e9
                hsh = tx["transaction_id"]["hash"]
                if val >= 1.0:
                    db.execute("INSERT OR IGNORE INTO hash_log VALUES (?)", (hsh,))
                    if db.rowcount > 0:
                        conn.commit()
                        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
                        await call.message.answer(f"✅ تم التأكيد! تفضل الرابط:\n{link.invite_link}")
                        return
        await call.message.answer("❌ لم نجد دفعاً جديداً بـ 1 TON.")
    except:
        await call.message.answer("⚠️ حدث خطأ في الشبكة، حاول لاحقاً.")

async def main():
    print("🚀 MB System is Online!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
