from flask import Flask
import logging
from telegram.ext import Updater

# Create Flask app (only needed if you're using webhooks)
app = Flask(__name__)

# Initialize the Telegram bot
TOKEN = "7410637757:AAGfu2Em_j31Qieqop9uzSum89P9SLM1J9k"
updater = Updater(token=TOKEN, use_context=True)

def start_polling():
    """Start bot's polling mode to keep it alive"""
    dispatcher = updater.dispatcher
    updater.start_polling()
    updater.idle()  # This ensures it stays alive

if __name__ == '__main__':
    logging.info("Starting bot...")
    start_polling()  # Start the bot
