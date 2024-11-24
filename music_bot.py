import os
import time
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
VK_SERVICE_KEY = os.getenv("VK_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Кэш для запросов
cache = {}
user_playlists = {}

# Функция поиска музыки через VK API
def search_music(query):
    if query in cache:
        return cache[query]
    
    url = "https://api.vk.com/method/audio.search"
    params = {
        "q": query,
        "access_token": VK_SERVICE_KEY,
        "v": "5.131",
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        # Логирование ответа от VK API
        logger.info(f"VK API response for query '{query}': {data}")

        if "response" in data and "items" in data["response"]:
            results = data["response"]["items"]
            cache[query] = results
            return results
        elif "error" in data:
            logger.error(f"VK API error: {data['error']}")
    except Exception as e:
        logger.error(f"Error while making VK API request: {e}")
    
    return None

# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Я музыкальный бот. Напиши название песни, и я найду её для тебя!")

# Обработчик текстовых сообщений (поиск музыки)
async def handle_message(update: Update, context: CallbackContext):
    query = update.message.text.strip()
    user_id = update.message.from_user.id

    if not query:
        await update.message.reply_text("Пожалуйста, отправьте запрос для поиска музыки.")
        return

    results = search_music(query)

    if not results:
        await update.message.reply_text("Извините, я ничего не нашел по вашему запросу.")
        return

    # Создание клавиатуры с треками
    keyboard = [
        [InlineKeyboardButton(f"{item['artist']} - {item['title']}", callback_data=f"track:{user_id}:{item['id']}")]
        for item in results[:5]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Вот что я нашел:", reply_markup=reply_markup)

# Обработчик сохранения трека в плейлист
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("track:"):
        _, user_id, track_id = query.data.split(":")
        user_id = int(user_id)

        # Сохраняем трек в плейлист пользователя
        if user_id not in user_playlists:
            user_playlists[user_id] = []
        user_playlists[user_id].append(track_id)

        await query.edit_message_text("Трек добавлен в ваш плейлист!")

# Обработчик команды /playlist
async def show_playlist(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in user_playlists or not user_playlists[user_id]:
        await update.message.reply_text("Ваш плейлист пуст.")
        return

    tracks = user_playlists[user_id]
    message = "Ваш плейлист:\n" + "\n".join(f"- Трек ID: {track_id}" for track_id in tracks)
    await update.message.reply_text(message)

# Основная функция
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("playlist", show_playlist))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == "__main__":
    main()