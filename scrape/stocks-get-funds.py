import yfinance as yf
from datetime import date, timedelta
import pandas as pd
import argparse
import time
import sys
import configparser
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
    fname = base + '202*.*'
    files = glob.glob(fname)
    if files == []: 
        print("get_latest_file: %s No files found %s" % (base, fname))
        return ""
    file = sorted(files)[-1]
    return file

def file2df(file):
    if file == "":
        return pd.DataFrame()
    df = pd.read_csv(file)
    print(df)
    df.rename(columns={'Instrument':'Symbol', 'Qty.':'Units'}, inplace=True)
    
    return df

def get_latest_gold_rate():
    config = configparser.ConfigParser()
    config.read('config.ini')
    data = config['data']
    basegold = data['basegold']
    goldfile = get_latest_file(basegold)
    xl = pd.ExcelFile(goldfile)
    df = xl.parse(0)    
    records = df.to_dict()
    goldrate = records['Gold Rate'][0]
    #print(f'Goldrate from {goldfile}: {goldrate}')
    return goldrate
    
# ----------------------------------------------------------------------------

args = argparse.ArgumentParser(description='Generate report')
args = args.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')

data = config['data']
basezerodha = data['basezerodha']
baseholdzerodha = data['baseholdzerodha']

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H', time.gmtime(now))
nowpr = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(now))
print("Current time: %s\n" % nowpr)

# process vested file
filedet = get_latest_file(baseholdzerodha)
print('Processing file %s ...' % filedet)

dfv = file2df(filedet)

syms = dfv.Symbol.unique()
print(syms)

symbol_price = {}
for sym in syms:
    if sym.startswith('SGB'):
        symbol_price[sym] = get_latest_gold_rate()
    else:
        symbol_price[sym] = get_price(sym + '.NS')
    if symbol_price[sym] == -1:
        print('ERROR: Failed to get price for %s!!' % sym)
        sys.exit(1)
        
print({k:int(symbol_price[k]) for k in symbol_price.keys()},'\n')

for index, row in dfv.iterrows():
    s = row['Symbol']
    dfv.at[index, 'NAV'] = symbol_price[s]
    dfv.at[index, 'Value'] = row['Units'] * symbol_price[s]

print(dfv)

# Generate fund excel
fname = basezerodha+nowstr+'.xlsx'
dfv.to_excel(fname, index=False, engine='xlsxwriter')
print("\nWritten %d rows to file %s ..." % (len(dfv),fname))
print('-------------------------------------------------------')




