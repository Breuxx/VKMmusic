import os
import json
import time
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext
)


# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VK_SERVICE_TOKEN = os.getenv("VK_SERVICE_TOKEN")

if not TELEGRAM_TOKEN or not VK_SERVICE_TOKEN:
    raise ValueError("TELEGRAM_TOKEN или VK_SERVICE_TOKEN не настроены!")

# Кэш для запросов
cache = {}
user_playlists = {}

# Функция для работы с VK API
def vk_api_request(method, params):
    """Отправка запроса к VK API с обработкой ошибок и кэшированием."""
    base_url = "https://api.vk.com/method/"
    params["access_token"] = VK_SERVICE_TOKEN
    params["v"] = "5.131"

    # Проверка кэша
    cache_key = json.dumps(params)
    if cache_key in cache:
        return cache[cache_key]

    try:
        response = requests.get(base_url + method, params=params).json()
        if "error" in response:
            raise Exception(f"Ошибка VK API: {response['error']['error_msg']}")
        result = response.get("response", {})
        cache[cache_key] = result  # Сохранение в кэш
        return result
    except Exception as e:
        print(f"Ошибка запроса к VK API: {e}")
        return None

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Я могу помочь найти музыку. Отправь название трека или используй команды: "
        "/playlist - показать твой плейлист, "
        "/help - помощь."
    )

# Поиск музыки
def search_music(update: Update, context: CallbackContext):
    query = update.message.text
    if not query:
        update.message.reply_text("Пожалуйста, введите название трека.")
        return

    # Поиск треков через VK API
    results = vk_api_request("audio.search", {"q": query, "count": 5})
    if not results or "items" not in results:
        update.message.reply_text("Не удалось найти треки. Попробуйте еще раз.")
        return

    # Отправка результатов пользователю
    tracks = results["items"]
    keyboard = []
    for track in tracks:
        title = f"{track['artist']} - {track['title']}"
        url = track.get("url", "Ссылка недоступна")
        update.message.reply_text(f"{title}\n{url}")
        keyboard.append([InlineKeyboardButton(title, callback_data=track["id"])])

    # Добавить клавиатуру для добавления в плейлист
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите трек для добавления в плейлист:", reply_markup=reply_markup)

# Добавление трека в плейлист
def add_to_playlist(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    track_id = query.data

    # Добавляем трек в пользовательский плейлист
    if user_id not in user_playlists:
        user_playlists[user_id] = []
    user_playlists[user_id].append(track_id)

    query.answer("Трек добавлен в ваш плейлист!")
    query.edit_message_text("Трек успешно добавлен в ваш плейлист.")

# Команда /playlist
def show_playlist(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    playlist = user_playlists.get(user_id, [])

    if not playlist:
        update.message.reply_text("Ваш плейлист пуст. Добавьте треки с помощью поиска.")
        return

    update.message.reply_text("Ваш плейлист:")
    for track_id in playlist:
        update.message.reply_text(f"ID трека: {track_id}")

# Команда /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Доступные команды:\n"
        "/start - начать работу с ботом\n"
        "/playlist - показать ваш плейлист\n"
        "/help - показать это сообщение\n"
        "Или просто отправьте название трека для поиска."
    )

# Основная функция
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("playlist", show_playlist))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, search_music))

    # Обработчик для инлайн-кнопок
    dispatcher.add_handler(
        CallbackQueryHandler(add_to_playlist)
    )

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()