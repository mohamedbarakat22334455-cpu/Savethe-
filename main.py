import asyncio, os, random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- [ إعدادات الهوية الفخمة ] ---
TOKEN = '8758046360:AAEJXi2E_Pf2cgCdrx_bFcUpAt1W8lGwR3s'
ADMIN_ID = 6363223356
CHANNEL_USER = "MBABmbab"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USER}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 🎭 1. ميزة "الترفيه والجذب" (Entertainment)
# ==========================================
@dp.message(F.text == "حظي")
async def daily_luck(m: types.Message):
    lucks = ["حظك اليوم ذهبي 🌟", "يوم مليء بالأكواد الناجحة 💻", "خبر سعيد في الطريق إليك ⚡", "ركز في مشروعك القادم 🚀"]
    await m.reply(f"🔮 **توقعات MB Gold لك:**\n\n`{random.choice(lucks)}`", parse_mode="MarkdownV2")

@dp.message(F.text.startswith("نسبة الحب"))
async def love_percent(m: types.Message):
    percent = random.randint(0, 100)
    await m.reply(f"❤️ **نسبة التوافق هي:** `{percent}%` \n\n🔱 [تابع جديدنا]({CHANNEL_LINK})", parse_mode="MarkdownV2")

# ==========================================
# 🆔 2. كارت الهوية المطور (User Card)
# ==========================================
@dp.message(F.text.in_({"ايدي", "ID", "ايديه"}))
async def premium_id(m: types.Message):
    # تحديد الرتبة بشكل شيك
    status = "العضو الملكي 👑" if m.from_user.id == ADMIN_ID else "عضو ذهبي ✨"
    
    card = (
        f"🔱 **بـطـاقـة نـخـبـة MB Gold**\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **الاسم:** `{m.from_user.first_name}`\n"
        f"🆔 **الأيدي:** `{m.from_user.id}`\n"
        f"🏆 **الرتبة:** {status}\n"
        f"📡 **الحالة:** متصل بنظام MBAB\n"
        f"━━━━━━━━━━━━━━\n"
        f"📢 [انضم لقناتنا الرسمية]({CHANNEL_LINK})"
    )
    await m.answer(card, parse_mode="MarkdownV2", disable_web_page_preview=True)

# ==========================================
# 🎨 3. الترحيب "الديناميكي" (Dynamic Welcome)
# ==========================================
@dp.message(F.new_chat_members)
async def welcome_v8(m: types.Message):
    for user in m.new_chat_members:
        welcomes = [
            f"نورت عالمنا يا {user.mention_markdown()}\! ✨",
            f"عضو جديد انضم لنخبة MB Gold: {user.mention_markdown()} 👑",
            f"أهلاً بك في أقوى مجتمع تقني: {user.mention_markdown()} 🚀"
        ]
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="💎 دخول القناة الملكية", url=CHANNEL_LINK))
        
        await m.answer(
            f"🔱 {random.choice(welcomes)}\n\n"
            f"استمتع بمميزات الحماية والترفيه الحصرية بالأسفل 👇",
            parse_mode="MarkdownV2",
            reply_markup=builder.as_markup()
        )
    try: await m.delete()
    except: pass

# ==========================================
# 👑 4. واجهة البداية (The Hook)
# ==========================================
@dp.message(CommandStart(), F.chat.type == "private")
async def private_v8(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📢 اشترك في MBAB", url=CHANNEL_LINK))
    kb.row(InlineKeyboardButton(text="➕ أضفني لجروبك (ستايل VIP)", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    
    await m.answer(
        f"👑 **مرحباً بك في الإصدار الثامن من MB Gold**\n\n"
        f"البوت الآن يعمل بنظام **التفاعل الذكي** لإحياء مجموعتك وجذب الأعضاء لقناتك فوراً\.\n\n"
        f"✅ اشتراكك في القناة هو مفتاح تشغيل الميزات الذهبية\.",
        parse_mode="MarkdownV2",
        reply_markup=kb.as_markup()
    )

# ==========================================
# 🚀 5. انطلاق المحرك (Railway Ready)
# ==========================================
async def handle(request): return web.Response(text="MB Gold V8 is Vibrant!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080))).start()
    
    print("🔥 MB Gold V8: The Elite Engine is Roaring!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
