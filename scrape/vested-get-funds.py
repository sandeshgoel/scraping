import yfinance as yf
from datetime import date, timedelta
import pandas as pd
import numpy as np
import argparse
import time
import sys
import configparser
import glob
from pprint import pprint
 
def get_price(symbol):
    #print('Getting price for symbol %s ...' % symbol)
    price = -1
    currency = 'USD'
    r = None
    for i in range(3):
        try:
            r = yf.Ticker(symbol)
            currency = r.info['currency'].upper()
            curprice = r.history(period=f"{i+1}d", interval="30m")['Close'].iloc[-1]
            price = float(curprice)#r.major_holders[1][0])#r.info['regularMarketPrice']
            break
        except Exception as e:
            if i>0: print('Exception %d: yf %s:' % (i, symbol), e)
        time.sleep(2)
        
    if price == -1: 
        pprint(vars(r))
    return price, currency
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

usdinr, _ = get_price('INR=X')
if usdinr == -1:
    print('ERROR: Failed to get price for USD-INR!!')
    sys.exit(1)
print('USD-INR %5.2f' % usdinr)

aedinr, _ = get_price('AEDINR=X')
if aedinr == -1:
    print('ERROR: Failed to get price for AED-INR!!')
    sys.exit(1)
print('AED-INR %5.2f' % aedinr)

gbpinr, _ = get_price('GBPINR=X')
if gbpinr == -1:
    print('ERROR: Failed to get price for GBP-INR!!')
    sys.exit(1)
print('GBP-INR %5.2f\n' % gbpinr)

currency2inr = {
    'USD': usdinr,
    'AED': aedinr,
    'GBP': gbpinr,
}

syms = dfv.Symbol.unique()
print(syms)

symbol_price = {}
symbol_currency = {}
for sym in syms:
    if sym in ['GBP', 'USD']: 
        symbol_price[sym] = 1
        symbol_currency[sym] = sym
    else:
        symbol_price[sym], symbol_currency[sym] = get_price(sym)
    if symbol_price[sym] == -1:
        print('ERROR: Failed to get price for %s!!' % sym)
        sys.exit(1)
print({k:str(int(symbol_price[k]))+' '+symbol_currency[k] for k in symbol_price.keys()},'\n')

# for index, row in dfv.iterrows():
#     s = row['Symbol']
#     dfv.at[index, 'NAV'] = symbol_price[s]
#     dfv.at[index, 'Currency'] = symbol_currency[s]
#     dfv.at[index, 'Rate'] = currency2inr[symbol_currency[s]]
#     dfv.at[index, 'Value'] = row['Units'] * symbol_price[s] * currency2inr[symbol_currency[s]]

dfv['NAV'] = dfv['Symbol'].map(symbol_price)
dfv['Currency'] = dfv['Symbol'].map(symbol_currency)
dfv['Rate'] = dfv['Currency'].map(currency2inr)
dfv['Value'] = dfv['Units'] * dfv['NAV'] * dfv['Rate']

print(dfv)

# Generate fund excel
fname = basevested+nowstr+'.xlsx'
dfv.to_excel(fname, index=False, engine='xlsxwriter')
print("\nWritten %d rows to file %s ..." % (len(dfv),fname))
print('-------------------------------------------------------')




