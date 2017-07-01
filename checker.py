from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
import config
import telegram
import logging
from telegram.ext import CommandHandler
import sys
import signal
from random import randint

from telegram.ext import Updater

import aws_api as aws

updater = Updater(token=config.AUTH_TOKEN)

counter = 0

telegramBot = telegram.Bot(token=config.AUTH_TOKEN)
print(telegramBot.getMe())

dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def check(bot, update, args):
    print(args)
    if (len(args) == 1):
        info = aws.checkOffers(args[0])
        bot.send_message(chat_id=update.message.chat_id, text= 'Neu: ' + info['LowestNewPrice'] + ' Gebraucht: ' + info['LowestUsedPrice'] + ' [link](' + info['MoreOffersUrl'] + ')', parse_mode=telegram.ParseMode.MARKDOWN)
        print(update.message.chat_id)
    
check_handler = CommandHandler('check', check, pass_args=True)
dispatcher.add_handler(check_handler)

updater.start_polling()

prices = []

def checkProduct(itemId):
    info = aws.checkOffers(itemId)
    if info['LowestUsedPrice'] in prices:
        return True
    else:
        prices.append(info['LowestUsedPrice'])
        telegramBot.send_message(chat_id=config.CHAT_ID, text= 'ASIN: ' + info['itemId'] + ' Neu: ' + info['LowestNewPrice'] + ' Gebraucht: ' + info['LowestUsedPrice'] + ' [link](' + info['MoreOffersUrl'] + ')', parse_mode=telegram.ParseMode.MARKDOWN)
        print(info['LowestUsedPrice'])
    return True

if __name__ == "__main__":
    while True:
        if counter > 60:
            del prices[:]
            telegramBot.send_message(chat_id=config.CHAT_ID, text= 'deleted cache')
        if checkProduct(config.ASIN) == True:
            print('sleeping for 60 seconds.')
            print(str(datetime.now()))
            time.sleep(60)
            print()
            counter = counter + 1
        
        else:
            print('Sorry! Nothing found. Sleeping for 60 seconds.')
            print(str(datetime.now()))
            time.sleep(60)
            print()





