import asyncio
import sqlite3
import time
import requests
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatInviteLink

# --- [ الإعدادات النهائية - محمد بركات ] ---
API_TOKEN = '8509628284:AAFSZRkfwJ9Wg5xT9utd6s1y5M-t4h0yazA'
ADMIN_ID = 6363223356  
CHANNEL_ID = '@MBABmbab' 
MY_WALLET = 'UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'

# إعداد السجلات لمراقبة أداء السيرفر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ إعداد قاعدة البيانات الشاملة ] ---
def init_db():
    conn = sqlite3.connect('mb_gold_pro.db', check_same_thread=False)
    db = conn.cursor()
    db.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, expire_at REAL)')
    db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, full_name TEXT)') 
    db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS processed_tx (tx_hash TEXT PRIMARY KEY)')
    db.execute("INSERT OR IGNORE INTO settings VALUES ('price', '1.0')")
    conn.commit()
    return conn

conn = init_db()
db = conn.cursor()

# --- [ وظائف النظام الاحترافية ] ---
async def check_ton_payment(expected_amount):
    """فحص البلوكشين مع معالجة الأخطاء المحسنة"""
    # نستخدم v2 API من TonCenter
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=15"
    try:
        # قمنا بزيادة الـ timeout لضمان عدم تعليق الكود
        response = requests.get(url, timeout=20)
        res = response.json()
        if res.get("ok"):
            for tx in res["result"]:
                value = int(tx["in_msg"]["value"]) / 1e9
                tx_hash = tx["transaction_id"]["hash"]
                
                if value >= expected_amount:
                    db.execute("SELECT tx_hash FROM processed_tx WHERE tx_hash = ?", (tx_hash,))
                    if not db.fetchone():
                        db.execute("INSERT INTO processed_tx VALUES (?)", (tx_hash,))
                        conn.commit()
                        return True
    except Exception as e:
        logging.error(f"Blockchain Error: {e}")
    return False

async def auto_kick_engine():
    """محرك الطرد التلقائي لمن انتهى اشتراكهم"""
    while True:
        try:
            current = time.time()
            db.execute("SELECT user_id FROM subs WHERE expire_at < ?", (current,))
            expired = db.fetchall()
            for (u_id,) in expired:
                try:
                    await bot.ban_chat_member(CHANNEL_ID, u_id)
                    await bot.unban_chat_member(CHANNEL_ID, u_id)
                    db.execute("DELETE FROM subs WHERE user_id = ?", (u_id,))
                    conn.commit()
                    await bot.send_message(u_id, "❌ انتهى وقت اشتراكك الـ VIP. جدد الآن للعودة!")
                except Exception as e:
                    logging.warning(f"Could not kick {u_id}: {e}")
        except Exception as e:
            logging.error(f"Auto-kick loop error: {e}")
        await asyncio.sleep(3600)

# --- [ لوحة التحكم والعمليات ] ---
@dp.message(Command("admin"))
async def admin_panel(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    db.execute("SELECT value FROM settings WHERE key = 'price'")
    price = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM subs")
    subs_v = db.fetchone()[0]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 ضبط السعر", callback_data="set_p"), 
         InlineKeyboardButton(text="📢 إذاعة", callback_data="bc")],
        [InlineKeyboardButton(text="📊 إحصائيات", callback_data="st")]
    ])
    await m.answer(f"⚙️ **لوحة التحكم | محمد بركات**\n\n💵 السعر: {price} TON\n💎 المشتركين: {subs_v}", reply_markup=kb)

@dp.callback_query(F.data == "bc")
async def start_bc(call: types.CallbackQuery):
    await call.message.answer("أرسل نص الإذاعة الآن:")
    await call.answer()

@dp.message(lambda m: m.from_user.id == ADMIN_ID and not m.text.startswith('/'))
async def handle_admin_msg(m: types.Message):
    if m.text.replace('.', '', 1).isdigit():
        db.execute("UPDATE settings SET value = ? WHERE key = 'price'", (m.text,))
        conn.commit()
        await m.answer(f"✅ تم تحديث السعر لـ {m.text} TON")
    else:
        db.execute("SELECT user_id FROM users")
        all_u = db.fetchall()
        s_count = 0
        for (u_id,) in all_u:
            try:
                await bot.send_message(u_id, m.text)
                s_count += 1
                await asyncio.sleep(0.05)
            except: pass
        await m.answer(f"✅ تم الإرسال لـ {s_count} مستخدم")

# --- [ واجهة المستخدم ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (m.from_user.id, m.from_user.full_name))
    conn.commit()
    db.execute("SELECT value FROM settings WHERE key = 'price'")
    p = db.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💎 اشتراك ({p} TON)", callback_data="buy")],
        [InlineKeyboardButton(text="🔄 تحقق من الدفع", callback_data="check")]
    ])
    await m.answer(f"🔱 أهلاً بك في نظام **MB GOLD**\n\nللدخول للقناة الحصرية، حول `{p}` TON لعنوان المحفظة:\n\n`{MY_WALLET}`", reply_markup=kb)

@dp.callback_query(F.data == "check")
async def verify(call: types.CallbackQuery):
    db.execute("SELECT value FROM settings WHERE key = 'price'")
    p = float(db.fetchone()[0])
    await call.message.answer("⏳ جاري الفحص... قد يستغرق الأمر دقيقة.")
    
    if await check_ton_payment(p):
        expire_time = time.time() + (30 * 24 * 60 * 60)
        db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?)", (call.from_user.id, expire_time))
        conn.commit()
        try:
            link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
            await call.message.answer(f"✅ مبروك! تم التأكيد. رابط الدخول:\n{link.invite_link}")
        except:
            await call.message.answer("✅ تم الدفع! لكن يرجى مراسلة الإدارة لإعطائك الرابط.")
    else:
        await call.message.answer("❌ لم يتم العثور على تحويل جديد. تأكد من إرسال المبلغ الصحيح.")

async def main():
    asyncio.create_task(auto_kick_engine())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
