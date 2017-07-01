from base64 import b64encode
from datetime import datetime, timedelta
import gzip
from hashlib import sha256
import hmac
import socket
import sys
from time import strftime, gmtime, sleep
import warnings

from io import StringIO
from urllib.request import HTTPError
from urllib.parse import quote

import requests
import config

from bs4 import BeautifulSoup

def checkOffers(itemId):
    params = {}

    params['AWSAccessKeyId'] = config.ACCESS_KEY
    params['Service'] = 'AWSECommerceService'
    params['Version'] = '2013-08-01'
    params['AssociateTag'] = config.ASOC_TAG
    params['Timestamp'] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
    params['Operation'] = 'ItemLookup'
    params['ResponseGroup'] = 'Offers' #OfferSummary
    params['IdType'] = 'ASIN'
    params['ItemId'] = itemId
    
    url = signateUrl(params)
    response = sendRequest(url, config.USER_AGENT)
    
    #print(response.decode("utf-8"))
    result = {}
    
    b = BeautifulSoup(response, 'lxml')
    #print(b.prettify())
    lowestPrice = b.find('lowestnewprice')
    if (lowestPrice is not None):
        lowestFormattedPrice = lowestPrice.formattedprice.string
        result['LowestNewPrice'] = lowestFormattedPrice
    
    lowestUsedPrice = b.find('lowestusedprice')
    if (lowestUsedPrice is not None):
        usedFormattedPrice = lowestUsedPrice.formattedprice.string
        result['LowestUsedPrice'] = usedFormattedPrice
    
    link = b.find('moreoffersurl')
    linkStr = link.string
    result['MoreOffersUrl'] = linkStr
    result['itemId'] = itemId
    
    return result   
    
    
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
    
def sendRequest(url, userAgent):
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': userAgent})
        return response.content
    except:
        return False