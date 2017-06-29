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

updater = Updater(token=config.AUTH_TOKEN)

counter = 0

def terminate(signal, frame):
    print("received SIGINT, exit...")
    updater.stop()
    quit()
    sys.exit(0)

signal.signal(signal.SIGINT, terminate)

telegramBot = telegram.Bot(token=config.AUTH_TOKEN)
print(telegramBot.getMe())

dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()

prices = []
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def checkIfSelling(url, name):
    try:
        productPage = requests.get(url, headers=headers)
        soup = BeautifulSoup(productPage.content, "html.parser")
    except:
        print('')
        print("Failed to load the page!")
        print('')
        return False;

    AMWcount = 0;
    for seller in soup.find_all('h3', {'class':'a-spacing-none olpSellerName'}): ##find imgs (denotes AMW seller)
        for img in seller.findAll('img'):
            if (img.get('alt', '') == 'Warehouse Deals'):
                 AMWcount += 1
                 priceDiv = seller.parent.parent.find('div', {'class':'a-column a-span2 olpPriceColumn'})
                 price = priceDiv.find('span', {'class':'a-size-large a-color-price olpOfferPrice a-text-bold'})
                 priceStr = price.string.strip()
                 print(priceStr)
                 if priceStr in prices:
                    break
                 else:
                    prices.append(priceStr)
                    telegramBot.send_message(chat_id=config.CHAT_ID, text= name + ' Preis: ' + priceStr + ' [link](' + url + ')', parse_mode=telegram.ParseMode.MARKDOWN)
    if AMWcount > 0:
        #telegramBot.send_message(chat_id=config.CHAT_ID, text= 'Aktive Warehouse Dealz: ' + AMWcount)
        return True;

if __name__ == "__main__":
    while True:
        print('Scanning for product name: ' + config.PRODUCTNAME)
        if counter > 60:
            del prices[:]
            telegramBot.send_message(chat_id=config.CHAT_ID, text= 'deleted cache')
        if checkIfSelling(config.PRODUCTURL, config.PRODUCTNAME) == True:
            rand = randint(30,120)
            print('Being sold - sleeping for ' + str(rand) + ' seconds.')
            print(str(datetime.now()))
            time.sleep(rand)
            print()
            counter = counter + 1
        
        else:
            print('Sorry! Nothing found. Sleeping for 60 seconds.')
            print(str(datetime.now()))
            time.sleep(60)
            print()





