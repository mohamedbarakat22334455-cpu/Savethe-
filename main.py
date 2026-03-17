import asyncio, sqlite3, time, requests, os, logging, yt_dlp
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# --- [ الإعدادات والبيانات ] ---
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 6363223356
CHANNEL_ID = '@MBABmbab'
MY_WALLET = 'UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.ERROR)

# --- [ نظام إدارة البيانات المطور ] ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('mb_gold_ultra.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT, join_date TEXT, downloads INTEGER DEFAULT 0)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, expire_at REAL, status TEXT DEFAULT "VIP")')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS tx_log (tx_hash TEXT PRIMARY KEY, amount REAL, date TEXT)')
        self.conn.commit()

    def add_user(self, uid, name):
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute('INSERT OR IGNORE INTO users (user_id, name, join_date) VALUES (?, ?, ?)', (uid, name, date))
        self.conn.commit()

db = Database()

# --- [ محرك التحميل الاحترافي ] ---
def get_video_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def download_task(url, msg_id, chat_id):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'downloads/{chat_id}_%(title)s.%(ext)s',
            'max_filesize': 50 * 1024 * 1024 # حد أقصى 50 ميجا للحفاظ على السيرفر
        }
        if not os.path.exists('downloads'): os.makedirs('downloads')
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            video = FSInputFile(path)
            await bot.send_video(chat_id, video, caption="✨ تم التحميل بنجاح بواسطة **MB Gold**")
            os.remove(path)
            db.cursor.execute('UPDATE users SET downloads = downloads + 1 WHERE user_id = ?', (chat_id,))
            db.conn.commit()
    except Exception as e:
        await bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)[:100]}")

# --- [ فحص الدفع والاشتراك ] ---
async def check_ton_api(price):
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_WALLET}&limit=10"
    try:
        r = requests.get(url, timeout=10).json()
        if r.get("ok"):
            for tx in r["result"]:
                val = int(tx["in_msg"]["value"]) / 1e9
                hsh = tx["transaction_id"]["hash"]
                if val >= price:
                    db.cursor.execute("SELECT tx_hash FROM tx_log WHERE tx_hash=?", (hsh,))
                    if not db.cursor.fetchone():
                        now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        db.cursor.execute("INSERT INTO tx_log VALUES (?, ?, ?)", (hsh, val, now))
                        db.conn.commit()
                        return True
    except: return False
    return False

# --- [ الأوامر والتفاعل ] ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    db.add_user(m.from_user.id, m.from_user.full_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 تفعيل VIP (1.0 TON)", callback_data="buy_vip")],
        [InlineKeyboardButton(text="📊 حسابي", callback_data="my_profile")],
        [InlineKeyboardButton(text="🔄 تأكيد الدفع", callback_data="verify_pay")]
    ])
    await m.answer(f"🔱 أهلاً بك في **MB Gold Ultra** يا {m.from_user.first_name}\n\n"
                   f"بوت التحميل الأول المدعوم بنظام الدفع الذكي.\n"
                   f"ارسل رابط الفيديو (TikTok, YouTube, Insta) للتحميل فوراً.\n\n"
                   f"لدخول القناة الخاصة، حول 1 TON للمحفظة:\n`{MY_WALLET}`", 
                   reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "my_profile")
async def profile_info(call: types.CallbackQuery):
    db.cursor.execute('SELECT join_date, downloads FROM users WHERE user_id = ?', (call.from_user.id,))
    user = db.cursor.fetchone()
    db.cursor.execute('SELECT expire_at FROM subs WHERE user_id = ?', (call.from_user.id,))
    sub = db.cursor.fetchone()
    
    status = "عادي ⚪" if not sub else f"VIP 👑 (ينتهي: {datetime.fromtimestamp(sub[0]).strftime('%Y-%m-%d')})"
    text = f"👤 **ملفك الشخصي**\n\n📅 تاريخ الانضمام: {user[0]}\n📥 عدد التحميلات: {user[1]}\n🌟 الحالة: {status}"
    await call.message.edit_text(text, parse_mode="Markdown")

@dp.message(F.text.startswith("http"))
async def handle_dl(m: types.Message):
    # نظام حماية بسيط
    status_msg = await m.answer("⏳ جاري تحليل الرابط...")
    asyncio.create_task(download_task(m.text, status_msg.message_id, m.chat.id))

# --- [ لوحة تحكم الإدارة ] ---
@dp.message(Command("admin"))
async def admin_panel(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    db.cursor.execute('SELECT COUNT(*) FROM users')
    total_users = db.cursor.fetchone()[0]
    db.cursor.execute('SELECT SUM(amount) FROM tx_log')
    total_income = db.cursor.fetchone()[0] or 0
    
    await m.answer(f"🛠 **لوحة تحكم محمد بركات**\n\n👥 إجمالي المستخدمين: {total_users}\n💰 إجمالي الأرباح: {total_income} TON")

async def main():
    try: await bot.send_message(ADMIN_ID, "🚀 MB Gold Ultra Engine Started!")
    except: pass
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
