from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

t = Thread(target=run)
t.start()
import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message, URLInputFile, InputMediaPhoto
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import yt_dlp

TOKEN = "1919695503:AAF5lDyP1HEd4IzZsAU9w6QzyvNMFv3b4jw"
ADMIN_ID = 1586886010
USERS_FILE = "users.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

WELCOME_IMAGE = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
PLATFORM_IMAGE = "https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=1000&auto=format&fit=crop"

class BotStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_broadcast = State()

def load_users():
    if not os.path.exists(USERS_FILE):
        return set()
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

def get_platforms_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📺 يوتيوب", callback_data="plat_youtube"),
                InlineKeyboardButton(text="🎵 تيك توك", callback_data="plat_tiktok")
            ],
            [
                InlineKeyboardButton(text="📸 إنستغرام", callback_data="plat_instagram")
            ]
        ]
    )

def get_download_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 تحميل فيديو (MP4)", callback_data="dl_video"),
                InlineKeyboardButton(text="🎵 تحميل صوتي (MP3)", callback_data="dl_audio")
            ],
            [
                InlineKeyboardButton(text="🔙 رجوع للمنصات", callback_data="back_to_platforms")
            ]
        ]
    )

def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 عدد المشتركين", callback_data="admin_count"),
                InlineKeyboardButton(text="📢 إذاعة جماعية", callback_data="admin_broadcast")
            ]
        ]
    )

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    users = load_users()
    if message.from_user.id not in users:
        users.add(message.from_user.id)
        save_users(users)
        
    await state.clear()
    
    welcome_text = (
        "✨ **مرحباً بك في بوت التحميل الاحترافي للميديا!** 🚀\n\n"
        "من هنا يمكنك تحميل الفيديوهات والصوتيات بأعلى جودة وبكل سهولة من:\n"
        "• يوتيوب 📺\n"
        "• تيك توك (بدون علامة مائية) 🎵\n"
        "• إنستغرام 📸\n\n"
        "👇 **اختر المنصة التي تريد التحميل منها للبدء:**"
    )
    
    await message.answer_photo(
        photo=URLInputFile(WELCOME_IMAGE),
        caption=welcome_text,
        reply_markup=get_platforms_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "back_to_platforms")
async def back_to_platforms(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=URLInputFile(PLATFORM_IMAGE),
            caption="📌 **الرجاء اختيار المنصة المطلوبة:**",
            parse_mode="Markdown"
        ),
        reply_markup=get_platforms_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("plat_"))
async def process_platform_selection(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split("_")[1]
    plat_names = {"youtube": "يوتيوب 📺", "tiktok": "تيك توك 🎵", "instagram": "إنستغرام 📸"}
    
    await state.set_state(BotStates.waiting_for_link)
    await callback.message.edit_caption(
        caption=f"🎯 لقد اخترت منصة: **{plat_names.get(platform, platform)}**\n\n🔗 **الآن أرسل الرابط الخاص بالفيديو:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 إلغاء والرجوع", callback_data="back_to_platforms")]]),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠️ **لوحة التحكم الإدارية الاحترافية:**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_count")
async def show_subscribers_count(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await callback.answer(f"📊 إجمالي عدد المشتركين في البوت: {len(users)} مشترك", show_alert=True)

@dp.callback_query(F.data == "admin_broadcast")
async def ask_broadcast_message(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📢 أرسل الآن الرسالة (نص، صورة، أو فيديو) ليتم إذاعتها لجميع المشتركين:")
    await state.set_state(BotStates.waiting_for_broadcast)
    await callback.answer()

@dp.message(BotStates.waiting_for_broadcast)
async def send_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = load_users()
    await state.clear()
    
    status_msg = await message.answer(f"⏳ جاري بدء الإذاعة الجماعية إلى {len(users)} مشترك...")
    success, failed = 0, 0
    
    for user_id in users:
        try:
            await message.send_copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1
            
    await status_msg.edit_text(f"✅ **تمت الإذاعة بنجاح!**\n\n- تم الإرسال إلى: {success}\n- فشل الإرسال لـ: {failed}", parse_mode="Markdown")

@dp.message(BotStates.waiting_for_link)
async def handle_user_link(message: Message, state: FSMContext):
    await state.update_data(media_link=message.text)
    await message.answer(
        "✨ **تم استلام الرابط بنجاح!**\n\nاختر الصيغة التي تناسبك للتحميل:",
        reply_markup=get_download_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("dl_"))
async def process_download(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    url = data.get("media_link")
    
    if not url:
        await callback.message.edit_text("❌ انتهت صلاحية الجلسة، أرسل /start للبدء من جديد.")
        return

    action = callback.data
    await callback.message.edit_text("⏳ **جاري معالجة وتحميل الملف، قد يستغرق ذلك بعض الوقت...**", parse_mode="Markdown")

    output_file = None
    try:
        if action == "dl_video":
            ydl_opts = {'cookiefile': 'cookies_new.txt',
                'format': 'best[ext=mp4]/best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'max_filesize': 50 * 1024 * 1024}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                output_file = ydl.prepare_filename(info)
            await callback.message.answer_video(FSInputFile(output_file), caption="✅ تم التحميل بنجاح بواسطة البوت.")
            
        elif action == "dl_audio":
            ydl_opts = {
                'cookiefile': 'cookies_new.txt',
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                output_file = os.path.splitext(filename)[0] + ".mp3"
            await callback.message.answer_audio(FSInputFile(output_file), caption="🎵 تم استخراج الصوت بنجاح.")

        await callback.message.delete()
        await state.clear()

    except Exception as e:
        await callback.message.edit_text(f"❌ حدث خطأ أثناء التحميل:\n`{str(e)}`", parse_mode="Markdown")
    
    finally:
        if output_file and os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass
    try:
        await callback.answer()
    except:
        pass

async def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
