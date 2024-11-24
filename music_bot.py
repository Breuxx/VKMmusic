import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from cachetools import TTLCache
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VK_SERVICE_KEY = os.getenv("VK_SERVICE_KEY")

# Настройка кэша (время хранения 1 час, максимум 100 запросов)
cache = TTLCache(maxsize=100, ttl=3600)

# Функция для поиска музыки через VK API
def search_music(query):
    if query in cache:
        return cache[query]
    url = "https://api.vk.com/method/audio.search"
    params = {
        "q": query,
        "access_token": VK_SERVICE_KEY,
        "v": "5.131",
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "response" in data and "items" in data["response"]:
        results = data["response"]["items"]
        cache[query] = results
        return results
    return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я могу найти музыку для тебя. Введи название трека или исполнителя.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = search_music(query)
    if results:
        message = "Вот что я нашел:\n"
        for track in results[:5]:
            title = track["title"]
            artist = track["artist"]
            url = f"https://vk.com/audio{track['owner_id']}_{track['id']}"
            message += f"{artist} - {title}: {url}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Извините, я ничего не нашел по вашему запросу.")

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Произошла ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

# Главная функция
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()