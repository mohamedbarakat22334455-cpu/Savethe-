import asyncio, os, requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8758046360:AAF8ilMxOrEHLr08fOGc5yZlT5blrByj1zs'
MY_WALLET = 'UQAXaqsRtUoSf7nIQtNMyFQ1knLyde_wA_tIO825IivGuh1L'
PORT = int(os.getenv("PORT", 8080)) # ريلاوي بيدينا البورت تلقائياً

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ صفحة الويب البسيطة ] ---
async def handle(request):
    return web.Response(text="🟢 MB Gold Protector System is Online and Running!")

async def start_webhook():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"✨ Web server started on port {PORT}")

# --- [ أوامر البوت الأساسية ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(f"🛡 **نظام حماية MB يعمل بنجاح!**\n\nالرابط الخاص بك:\nhttps://worker-production-f9bd.up.railway.app")

# --- [ تشغيل كل شيء معاً ] ---
async def main():
    # تشغيل صفحة الويب في الخلفية
    asyncio.create_task(start_webhook())
    
    print("🚀 Bot Polling Started...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
