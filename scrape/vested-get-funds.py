import yfinance as yf
from datetime import date, timedelta
import pandas as pd
import numpy as np
import argparse
import time
import sys
import configparser
import requests
import json
import glob
from pprint import pprint

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
 
def get_price(symbol):
    #symbol = 'INR=X'
    #print('Getting price for symbol %s ...' % symbol)
    #symbol = 'TSLA'
    for i in range(5):
        try:
            r = yf.Ticker(symbol)
            #print(r.info)
            curprice = r.history(period="1d", interval="30m")['Close'].iloc[-1]
            #sys.exit(1)
            price = float(curprice)#r.major_holders[1][0])#r.info['regularMarketPrice']
            break
        except Exception as e:
            if i>1: print('Exception %d: yf %s:' % (i, symbol), e)
    if price is None: 
        pprint(vars(r))
        price = -1
    return price

# ----------------------------------------------------------------------------

def get_latest_file(base):
    fname = base + '202*.xls*'
    files = glob.glob(fname)
    if files == []: 
        print("get_latest_file: %s No files found %s" % (base, fname))
        return ""
    file = sorted(files)[-1]
    return file

def file2df(file):
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)
    df = xl.parse(0)    
    return df

# ----------------------------------------------------------------------------

args = argparse.ArgumentParser(description='Generate report')
args = args.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')

data = config['data']

basevested = data['basevested']
basevesteddet = data['basevesteddet']

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H', time.gmtime(now))
nowpr = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(now))
print("Current time: %s\n" % nowpr)

# process vested file
filedet = get_latest_file(basevesteddet)
dfv = file2df(filedet)

print('Processing file %s ...' % filedet)

usdinr = get_price('INR=X')
if usdinr == -1:
    print('ERROR: Failed to get price for USD-INR!!')
    sys.exit(1)
print('USD-INR %5.2f\n' % usdinr)

aedinr = get_price('AEDINR=X')
if aedinr == -1:
    print('ERROR: Failed to get price for AED-INR!!')
    sys.exit(1)
print('AED-INR %5.2f\n' % aedinr)

syms = dfv.Symbol.unique()
print(syms)

symbol_price = {}
for sym in syms:
    if sym == 'USD': 
        symbol_price[sym] = 1
    else:
        symbol_price[sym] = get_price(sym)
    if symbol_price[sym] == -1:
        print('ERROR: Failed to get price for %s!!' % sym)
        sys.exit(1)
print({k:int(symbol_price[k]) for k in symbol_price.keys()},'\n')

for index, row in dfv.iterrows():
    s = row['Symbol']
    dfv.at[index, 'NAV'] = symbol_price[s]
    dfv.at[index, 'USD'] = usdinr
    dfv.at[index, 'Value'] = row['Units'] * symbol_price[s] * usdinr

print(dfv)

# Generate fund excel
fname = basevested+nowstr+'.xlsx'
dfv.to_excel(fname, index=False, engine='xlsxwriter')
print("\nWritten %d rows to file %s ..." % (len(dfv),fname))
print('-------------------------------------------------------')




