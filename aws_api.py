from base64 import b64encode
from bs4 import BeautifulSoup
import config
from datetime import datetime
from hashlib import sha256
import hmac
from ratelimit import *
import re
import requests
import time
from time import strftime, gmtime
from urllib.parse import quote


def checkOffers(itemIdStr, responseGroup):
    params = {}

    itemId = validateItemIds(itemIdStr)
    if not itemId:
        return

    params['AWSAccessKeyId'] = config.ACCESS_KEY
    params['Service'] = 'AWSECommerceService'
    params['Version'] = '2013-08-01'
    params['AssociateTag'] = config.ASOC_TAG
    params['Timestamp'] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
    params['Operation'] = 'ItemLookup'
    params['ResponseGroup'] = responseGroup #'OfferSummary' #Offers
    params['IdType'] = 'ASIN'
    params['ItemId'] = itemId

    url = signateUrl(params)
    response = sendRequest(url, config.USER_AGENT)

    #print(response.decode("utf-8"))
    result = {}
    result['items'] = []

    ts = time.time()
    timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    b = BeautifulSoup(response, 'lxml')
    #print(b.prettify())
    items = b.find_all('item')
    for item in items:
        itemResult = {}
        itemResult['prices'] = []

        lowestPrice = item.find('lowestnewprice')
        if lowestPrice is not None:
            price = {} # Condition, Amount, CreatedAt, CurrencyCode
            price['Amount'] = lowestPrice.amount.string
            price['Condition'] = 0
            price['CreatedAt'] = timestamp
            price['CurrencyCode'] = lowestPrice.currencycode.string
            itemResult['prices'].append(price)


        lowestUsedPrice = item.find('lowestusedprice')
        if lowestUsedPrice is not None:
            price = {} # Condition, Amount, CreatedAt, CurrencyCode
            price['Amount'] = lowestUsedPrice.amount.string
            price['Condition'] = 1
            price['CreatedAt'] = timestamp
            price['CurrencyCode'] = lowestUsedPrice.currencycode.string
            itemResult['prices'].append(price)
            print(price['Amount'])

        link = item.find('moreoffersurl')
        if link is not None:
            linkStr = link.string
            itemResult['MoreOffersUrl'] = linkStr
        if item.asin is not None:
            itemResult['ASIN'] = item.asin.string
        result['items'].append(itemResult)
    print(result)
    return result

def validateItemIds(itemIdStr):
    itemIds = itemIdStr.split(',')
    valid = []
    for item in itemIds:
        check = isValidASIN(item)
        if check is not None:
            valid.append(item)
    return ','.join(valid)

def isValidASIN(itemId):
    pattern = re.compile("^B\d{2}\w{7}|\d{9}(X|\d)$")
    return pattern.match(itemId)


def signateUrl(params):
    # create signature
    keys = sorted(params.keys())
    args = '&'.join('%s=%s' % (
        key, quote(str(params[key]).encode('utf-8'))) for key in keys)

    msg = 'GET'
    msg += '\n' + config.HOST
    msg += '\n/onca/xml'
    msg += '\n' + args

    key = config.SECRET_KEY or ''

    hash = hmac.new(key.encode(), msg.encode(), sha256)

    signature = quote(b64encode(hash.digest()))
    url = 'http://%s/onca/xml?%s&Signature=%s' % (config.HOST, args, signature)
    return url

@rate_limited(1)
def sendRequest(url, userAgent):
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': userAgent})
        return response.content
    except Exception:
        return False

#print(checkOffers(config.ASIN))
