from django.core.management.base import BaseCommand
from telegram.ext import Updater, Filters
from telegram_bot.bot import start, process_email, teacher_menu, set_limit, add_topic
from django.core.management.base import BaseCommand
from telegram import Bot, Update
from telegram.ext import CommandHandler, CallbackContext, Updater, MessageHandler


class Command(BaseCommand):
    help = "Run the Telegram bot"

    def handle(self, *args, **options):
        updater = Updater(token="7209327789:AAEN03EYp3q4a57F0GEiLwxdsWUyntxduj8")
        dispatcher = updater.dispatcher

        # Обработчики
        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_email))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, teacher_menu))

        updater.start_polling()
        updater.idle()

