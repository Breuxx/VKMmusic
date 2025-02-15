import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from yt_dlp import YoutubeDL

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "ваш_токен_бота"

# Папка для временных файлов
TEMP_FOLDER = "temp"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Функция для скачивания аудио
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(TEMP_FOLDER, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".mp4", ".mp3")
        return audio_path, info.get('title', 'audio')

# Обработчик команды /start
async def start(update: Update, context):
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на видео или аудио с одной из поддерживаемых платформ:\n"
        "- Instagram Reels\n"
        "- YouTube\n"
        "- TikTok\n"
        "- Twitter\n"
        "- SoundCloud\n"
        "- VK\n"
        "- Facebook\n"
        "Я пришлю тебе аудио."
    )

# Обработчик текстовых сообщений
async def handle_message(update: Update, context):
    url = update.message.text
    supported_platforms = [
        "instagram.com", "youtube.com", "youtu.be", "tiktok.com", 
        "twitter.com", "soundcloud.com", "vk.com", "facebook.com"
    ]

    # Проверяем, поддерживается ли платформа
    if not any(platform in url for platform in supported_platforms):
        await update.message.reply_text(
            "Пожалуйста, отправьте ссылку на одну из поддерживаемых платформ:\n"
            "- Instagram Reels\n"
            "- YouTube\n"
            "- TikTok\n"
            "- Twitter\n"
            "- SoundCloud\n"
            "- VK\n"
            "- Facebook"
        )
        return

    await update.message.reply_text("Скачиваю аудио...")

    try:
        # Скачиваем аудио
        audio_path, title = download_audio(url)
        
        # Отправляем аудио пользователю
        with open(audio_path, 'rb') as audio_file:
            await update.message.reply_audio(audio_file, title=title)
        
        # Удаляем временный файл
        os.remove(audio_path)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Не удалось скачать аудио. Проверьте ссылку и попробуйте снова.")

# Основная функция
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
