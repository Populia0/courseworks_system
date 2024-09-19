from django.core.management.base import BaseCommand
from telegram.ext import Updater, Filters, CommandHandler, Updater, MessageHandler, ConversationHandler, CallbackQueryHandler
from telegram_bot.bot import EMAIL, SEND_TEACHER_CHOICES, TEACHER_CALLBACK, SEND_TOPIC_CALLBACK, PROPOSE_TOPIC, CONFIRM_TOPIC, BUTTON_HANDLER, REJECT_REASON, handle_reject_reason, propose_topic, button_handler, confirm_topic_callback, send_topic_callback, start, process_email, stop, send_teacher_choices, teacher_callback
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self):
        updater = Updater(token="7209327789:AAEN03EYp3q4a57F0GEiLwxdsWUyntxduj8")
        dispatcher = updater.dispatcher
        
        conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, process_email)],
            SEND_TEACHER_CHOICES: [MessageHandler(Filters.text & ~Filters.command, send_teacher_choices)],
            PROPOSE_TOPIC: [MessageHandler(Filters.text & ~Filters.command, propose_topic)],
            TEACHER_CALLBACK: [CallbackQueryHandler(teacher_callback)],
            SEND_TOPIC_CALLBACK: [CallbackQueryHandler(send_topic_callback)],
            REJECT_REASON: [MessageHandler(Filters.text & ~Filters.command, handle_reject_reason)],
            CONFIRM_TOPIC: [CallbackQueryHandler(confirm_topic_callback)],
            BUTTON_HANDLER: [CallbackQueryHandler(button_handler)],
        },

        fallbacks=[CommandHandler('stop', stop)]
        )

        dispatcher.add_handler(conv_handler)
        updater.start_polling()
        updater.idle()


        