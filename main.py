import asyncio, sqlite3, os, requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- [ الإعدادات ] ---
API_TOKEN = os.getenv('8509628284:AAFSZRkfwJ9Wg5xT9utd6s1y5M-t4h0yazA')
ADMIN_ID=6363223356
CHANNEL_ID=@MBABmbab
MY_WALLET='UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'
ADMIN_ID = 6363223356
CHANNEL_ID = -1002345678901 # ID قناتك
MY_WALLET = 'UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات المتطورة ] ---
conn = sqlite3.connect('mb_guard_elite.db', check_same_thread=False)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, warnings INTEGER DEFAULT 0)')
db.execute('CREATE TABLE IF NOT EXISTS promo (code TEXT PRIMARY KEY, uses INTEGER)')
db.execute('CREATE TABLE IF NOT EXISTS hash_log (h TEXT PRIMARY KEY)')
# إضافة كود خصم تجريبي ليك يا محمد (الكود: MB777)
db.execute('INSERT OR IGNORE INTO promo VALUES ("MB777", 10)') 
conn.commit()

# --- [ قائمة الحماية ] ---
BAD_WORDS = ["شتيمة", "إعلان", "t.me/", "http"]

# --- [ نظام المراقبة والتحذير ] ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def security_logic(m: types.Message):
    # 1. منع الروابط والشتائم
    if any(word in m.text.lower() for word in BAD_WORDS):
        await m.delete()
        
        # نظام التحذيرات
        db.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (m.from_user.id,))
        db.execute('UPDATE users SET warnings = warnings + 1 WHERE id = ?', (m.from_user.id,))
        conn.commit()
        
        db.execute('SELECT warnings FROM users WHERE id = ?', (m.from_user.id,))
        warns = db.fetchone()[0]
        
        if warns >= 3:
            await bot.ban_chat_member(m.chat.id, m.from_user.id)
            await m.answer(f"🚫 تم طرد {m.from_user.first_name} بسبب تخطي حدود التحذيرات.")
        else:
            await m.answer(f"⚠️ إنذار ({warns}/3) يا {m.from_user.first_name}! ممنوع الروابط أو التجاوز.")

# --- [ أوامر البوت ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 دخول القناة (1 TON)", callback_data="pay")],
        [InlineKeyboardButton(text="🎟 استخدام كود خصم", callback_data="promo")],
        [InlineKeyboardButton(text="✅ تأكيد الدفع", callback_data="confirm")]
    ])
    await m.answer(f"🛡 **نظام حماية MB Elite**\n\n- القناة محمية من السرقة.\n- الدخول آمن وتلقائي.\n\nالمحفظة:\n`{MY_WALLET}`", reply_markup=kb)

@dp.callback_query(F.data == "promo")
async def ask_promo(call: types.CallbackQuery):
    await call.message.answer("ارسل كود الخصم الآن في رسالة:")

@dp.message(F.text.startswith("MB")) # الأكواد بتبدأ بـ MB
async def check_promo(m: types.Message):
    db.execute('SELECT uses FROM promo WHERE code = ?', (m.text,))
    res = db.fetchone()
    if res and res[0] > 0:
        db.execute('UPDATE promo SET uses = uses - 1 WHERE code = ?', (m.text,))
        conn.commit()
        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        await m.answer(f"✅ الكود صحيح! تفضل رابط الدخول:\n{link.invite_link}")
    else:
        await m.answer("❌ الكود غير صحيح أو انتهت صلاحيته.")

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
                        await call.message.answer(f"✅ تم التأكيد! الرابط:\n{link.invite_link}")
                        return
        await call.message.answer("❌ لم نجد دفعاً جديداً.")
    except:
        await call.message.answer("⚠️ حاول مرة أخرى.")

# --- [ لوحة تحكم الإدمن ] ---
@dp.message(Command("admin"))
async def admin_stats(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM hash_log")
    sales = db.fetchone()[0]
    await m.answer(f"🛠 **إحصائيات MB Protector**\n\n💰 عدد المبيعات: {sales}\n💎 الدخل الإجمالي: {sales * 1} TON")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
