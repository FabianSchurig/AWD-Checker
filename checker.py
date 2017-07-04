from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime,timedelta
import config
import telegram
import logging
from telegram.ext import CommandHandler
import sys
import signal
from random import randint

from telegram.ext import Updater

import aws_api

import sqlite3

conn = sqlite3.connect(config.DB_NAME, check_same_thread=False)
c = conn.cursor()

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
    t = (str(update.message.chat_id),)
    c.execute('SELECT * FROM Users WHERE chatID=?', t)
    row = c.fetchone()
    print(row)
    if row is None:
        c.execute('INSERT INTO Users (chatID, isAdmin) VALUES (?,?)',(str(update.message.chat_id),0,))
        conn.commit()
        print('Inserted new user with chat id '+str(t))

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def addItem(bot, update, args):
    print(args)
    if (len(args) == 1):
        t = (str(update.message.chat_id),)
        c.execute('SELECT id FROM Users WHERE chatID=?', t)
        userId = c.fetchone()
        
        asinStr = aws_api.validateItemIds(args[0])
        asins = asinStr.split(',')
        noInfo = []
        for asin in asins:
            c.execute('SELECT * FROM Items WHERE asin=?', (str(asin),))
            row = c.fetchone()
            if row is None:
                noInfo.append(asin)
            else:
                c.execute('SELECT * FROM Track WHERE UserID=? and ItemID=?', (userId[0],row[0],))
                if c.fetchone() is None:
                    c.execute('INSERT INTO Track (ItemID, UserID, TargetAmount) VALUES (?,?,?)',(row[0],userId[0],0,))
                    conn.commit()
        alreadyTracked = []
        c.execute('SELECT ItemID FROM Track WHERE UserID=?', userId)
        rows = c.fetchall()
        print(rows)
        for row in rows:
            alreadyTracked.append(row[0])
            print(row[0])
        if len(noInfo) > 0 and len(noInfo) <= 10:    
            items = aws_api.checkOffers(','.join(noInfo),'Offers')
            for item in items['items']:
                if 'ASIN' in item and 'MoreOffersUrl' in item:
                    c.execute('INSERT INTO Items (asin, url) VALUES (?,?)',(str(item['ASIN']),str(item['MoreOffersUrl']),))
                    conn.commit()
                    c.execute('SELECT id FROM Items WHERE asin=?', (str(item['ASIN']),))
                    row = c.fetchone()
                    print(row)
                    for price in item['prices']:
                        c.execute('INSERT INTO Prices (ItemID, Condition, Amount, CreatedAt, CurrencyCode) VALUES (?,?,?,?,?)',(row[0],price['Condition'],price['Amount'],price['CreatedAt'],price['CurrencyCode'],))
                        conn.commit()
                    if row[0] not in alreadyTracked:
                        c.execute('INSERT INTO Track (ItemID, UserID, TargetAmount) VALUES (?,?,?)',(row[0],userId[0],0,))
                        conn.commit()
                else:
                    print('Fail')
            bot.send_message(chat_id=update.message.chat_id, text= 'successfully added '+str(len(noInfo))+' items', parse_mode=telegram.ParseMode.MARKDOWN)
        print(update.message.chat_id)
    
addItem_handler = CommandHandler('add', addItem, pass_args=True)
dispatcher.add_handler(addItem_handler)

def check(bot, update, args):
    print(args)
    if (len(args) == 1):
        asinStr = aws_api.validateItemIds(args[0])
        asins = asinStr.split(',')
        for asin in asins:
            c.execute('SELECT * FROM Items WHERE asin=?', (str(asin),))
            row = c.fetchone()
            bot.send_message(chat_id=update.message.chat_id, text= row, parse_mode=telegram.ParseMode.MARKDOWN)        
        print(update.message.chat_id)
    
check_handler = CommandHandler('check', check, pass_args=True)
dispatcher.add_handler(check_handler)

def info(bot, update):
    c.execute('SELECT Max(Prices.CreatedAt) FROM Prices')
    maxTime = c.fetchone()
    queryTime = (datetime.strptime(maxTime[0], '%Y-%m-%d %H:%M:%S') - timedelta(seconds=120)).strftime('%Y-%m-%d %H:%M:%S')
    print(maxTime)
    print(queryTime)
    c.execute('SELECT Distinct chatID,url,asin,Amount,Condition,CurrencyCode FROM Prices INNER JOIN Items ON Prices.ItemID=Items.id INNER JOIN Track ON Items.id=Track.ItemID INNER JOIN Users On Users.id=Track.UserID Where Prices.CreatedAt>? and Users.chatID=?',(queryTime,update.message.chat_id,))
    rows = c.fetchall()
    print(rows)
    for row in rows:
        bot.send_message(chat_id=update.message.chat_id, text= 'Item '+'ASIN: '+row[2]+' Preis: '+str(row[3]/100)+' '+row[5]+' Zustand: '+('Gebraucht' if row[4] == 1 else 'Neu')+' [link]('+row[1]+')', parse_mode=telegram.ParseMode.MARKDOWN)      
    print(update.message.chat_id)
    
info_handler = CommandHandler('info', info)
dispatcher.add_handler(info_handler)

updater.start_polling()

def updatePrices(itemId):
    info = aws_api.checkOffers(itemId, responseGroup = 'OfferSummary')
    updated = False
    for item in info['items']:
        if 'ASIN' in item and 'prices' in item:
            for price in item['prices']:
                c.execute('SELECT id FROM Items WHERE asin=?', (str(item['ASIN']),))
                row = c.fetchone()
                c.execute('INSERT INTO Prices (ItemID, Condition, Amount, CreatedAt, CurrencyCode) VALUES (?,?,?,?,?)',(row[0],price['Condition'],price['Amount'],price['CreatedAt'],price['CurrencyCode'],))
                conn.commit()
                updated = True
    return updated


if __name__ == "__main__":
    while True:
        c.execute('SELECT Max(Prices.CreatedAt) FROM Prices')
        maxTime = c.fetchone()
        if maxTime[0] < (datetime.fromtimestamp(time.time()) - timedelta(seconds=61)).strftime('%Y-%m-%d %H:%M:%S'):
            print('old data')
        c.execute('SELECT Distinct asin FROM Items INNER JOIN Track ON Items.id=Track.ItemID')
        rows = c.fetchall()
        print(rows)
        counter = 0
        asins = []
        length = len(rows)
        for row in rows:
            counter = counter + 1
            length = length - 1
            asins.append(row[0])
            if counter > 8 or length == 0:
                counter = 0
                status = updatePrices(','.join(asins))
                print('updating following products: '+','.join(asins))
                print('update '+str(status))
        ts = time.time()
        timestamp = (datetime.fromtimestamp(ts) - timedelta(seconds=61)).strftime('%Y-%m-%d %H:%M:%S')
        print('Timestamp: '+timestamp)
        c.execute('SELECT * FROM Prices Where Prices.CreatedAt>? and Prices.Condition=1 group by Prices.ItemID,Prices.Amount order by Prices.CreatedAt ASC',(timestamp,))
        rows = c.fetchall()
        itemIds = []
        for row in rows:
            if row[1] in itemIds:
                print(row)
                c.execute('SELECT Distinct chatID,url,asin,Amount,Condition,CurrencyCode FROM Prices INNER JOIN Items ON Prices.ItemID=Items.id INNER JOIN Track ON Items.id=Track.ItemID INNER JOIN Users On Users.id=Track.UserID Where Prices.ItemID=? and Prices.Condition=1 and Prices.CreatedAt= (SELECT Max(Prices.CreatedAt) FROM Prices)',(row[1],))
                rowsN = c.fetchall()
                print(rowsN)
                for rowN in rowsN:
                    telegramBot.send_message(chat_id=rowN[0], text= 'Preisänderung '+'ASIN: '+rowN[2]+' Preis: '+str(rowN[3]/100)+' '+rowN[5]+' Zustand: '+('Gebraucht' if rowN[4] == 1 else 'Neu')+' [link]('+rowN[1]+')', parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                itemIds.append(row[1])
        print(str(datetime.now()))
        time.sleep(30)
        print()





