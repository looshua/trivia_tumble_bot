# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 18:07:29 2020

@author: looshua
"""

# token for bot access
from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, ConversationHandler,
                          CallbackQueryHandler, Filters)
import player
import admin
import token_file
from telegram import ReplyKeyboardMarkup
import logging
import telegram

TOKEN = token_file.token

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


class NormUser:
    def __init__(self):
        pass


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    main_bot = admin.MainBot()
    player_bot = player.PlayerBot(main_bot)

    main_bot.add_handlers(dp)
    player_bot.add_handlers(dp)

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
