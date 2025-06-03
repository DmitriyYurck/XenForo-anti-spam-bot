import os
from datetime import datetime
import time

import requests
import telebot

from dotenv import load_dotenv

load_dotenv()
XENFORO_API_KEY = os.getenv("TOKEN")
XENFORO_API_URL = os.getenv("URL")
TELEGRAM_BOT_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

BANNED_WORDS = ["kraken", "mega", "blacksprut", "Кракен", "мега", "блэкспрут"]

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def get_all_threads():
    endpoint = f"{XENFORO_API_URL}/threads"
    headers = {"XF-Api-Key": XENFORO_API_KEY}
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json().get('threads', [])[:10]  # Возвращаем только первые 10 тем
    except Exception as e:
        log(f"Ошибка при получении тем: {e}")
        return []

def check_banned_words(text):
    if not text:
        return False
    return any(word.lower() in text.lower() for word in BANNED_WORDS)

def delete_thread(thread_id):
    endpoint = f"{XENFORO_API_URL}/threads/{thread_id}"
    headers = {"XF-Api-Key": XENFORO_API_KEY}
    
    try:
        response = requests.delete(endpoint, headers=headers)
        response.raise_for_status()
        log(f"Тема {thread_id} успешно удалена")
        return True
    except Exception as e:
        log(f"Ошибка при удалении темы {thread_id}: {e}")
        return False

def send_alert(thread_info, banned_word):
    message = (
        f"⚠️ Нарушение правил форума! \n"
        f"📌 Тема: {thread_info.get('title', 'Без названия')}\n"
        f"🆔 ID темы: {thread_info.get('thread_id')}\n"
        f"🚫 Слово: {banned_word}\n"
        f"😈 Ссылка: {thread_info.get('view_url')}\n"
        f"⚡ Пользователь: {thread_info.get('username')}\n"
    )
    
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        log("Уведомление отправлено в Telegram")
    except Exception as e:
        log(f"Ошибка отправки в Telegram: {e}")

def moderate_threads():
    while True:
        threads = get_all_threads()
        print(threads[0])
        if not threads:
            log("Нет доступных тем для проверки.")
            time.sleep(1)  # Задержка перед следующей проверкой
            continue 
        
        for thread in threads:
            thread_id = thread.get('thread_id')
            title = thread.get('title', '')
            content = thread.get('first_post', {}).get('message', '')
            log(f"Проверка темы: {title} (ID: {thread_id})")
            
            if check_banned_words(title) or check_banned_words(content):
                banned_word = next(word for word in BANNED_WORDS if word.lower() in title.lower() or word.lower() in content.lower())
                if delete_thread(thread_id):
                    send_alert(thread, banned_word)
        
        time.sleep(1)  # Задержка перед следующей проверкой

if __name__ == "__main__":
    try:
       moderate_threads()
    except KeyboardInterrupt:
        print("exit...")
