import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from ytmusicapi import YTMusic
import yt_dlp

# Получение токена из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден токен бота. Убедитесь, что TELEGRAM_BOT_TOKEN установлен.")

bot = telebot.TeleBot(TOKEN)

# Инициализация YTMusic API
ytmusic = YTMusic()

# Функция для поиска треков
def search_tracks(query):
    search_results = ytmusic.search(query, filter='songs')
    return search_results[:5]  # Возвращаем первые 5 результатов

# Функция для получения ссылки на скачивание
def get_download_link(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'skip_download': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info['url']

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я помогу найти и скачать музыку.\n"
        "Просто отправь название трека или исполнителя!"
    )

# Обработчик текстовых сообщений (поиск музыки)
@bot.message_handler(func=lambda message: True)
def search_music(message):
    query = message.text
    bot.send_message(message.chat.id, f"Ищу музыку по запросу: {query}...")

    tracks = search_tracks(query)

    if not tracks:
        bot.send_message(message.chat.id, "Ничего не найдено. Попробуйте другой запрос.")
        return

    for track in tracks:
        title = track['title']
        artist = track['artists'][0]['name']
        video_url = f"https://www.youtube.com/watch?v={track['videoId']}"

        # Клавиатура с кнопками
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Скачать MP3", callback_data=f"download|{track['videoId']}"))
        markup.add(InlineKeyboardButton("Открыть на YouTube", url=video_url))

        bot.send_message(
            message.chat.id,
            f"🎵 *{title}*\n👤 {artist}",
            parse_mode='Markdown',
            reply_markup=markup
        )

# Обработчик кнопок
@bot.callback_query_handler(func=lambda call: call.data.startswith("download|"))
def send_download_link(call):
    video_id = call.data.split('|')[1]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    bot.answer_callback_query(call.id, "Генерирую ссылку на скачивание...")
    try:
        download_url = get_download_link(video_url)
        bot.send_message(call.message.chat.id, f"🔗 Ваша ссылка на скачивание:\n{download_url}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка при генерации ссылки: {e}")

# Запуск бота
bot.polling(none_stop=True)
