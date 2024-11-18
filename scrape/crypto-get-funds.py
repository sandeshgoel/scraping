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

# https://pro.coinmarketcap.com/account
def get_price_cmc(symbols):
    price = {}

    API_KEY = '524b3a9e-eb5c-42a5-8bf4-ac97de0d7f99'
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {
      'symbol':','.join(symbols),
      'convert':'USD'
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': API_KEY,
    }

    session = Session()
    session.headers.update(headers)

    try:
      response = session.get(url, params=parameters)
      data = json.loads(response.text)
      #print(data)
      if data['status']['error_code'] != 0:
        print('ERROR:', data['status'])
      else:
        for symbol in symbols:
            price[symbol] = data['data'][symbol][0]['quote']['USD']['price']
    except (ConnectionError, Timeout, TooManyRedirects) as e:
      print(e)
    return price
      
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

def get_price_wazirx_all(syms):
    s = requests.session()
    url = 'https://api.wazirx.com/sapi/v1/tickers/24hr'
    for i in range(5):
        try:
            r = s.get(url)
            d = json.loads(r.content)
            if len(d) > 0: 
                break
            else:
                print('Empty result, retrying')
                time.sleep(1)
        except Exception as e:
            if i>1: print('Exception %d: wazirx %s:' % (i), e)
            time.sleep(1)

    ret = {}
    for s in syms:
        ret[s] = next(int(float(x.get('lastPrice', -1))) for x in d if x['symbol'] == s.lower()+'inr')

    return ret


def get_price_wazirx(symbol):
    symbol = symbol.lower() + 'inr'
    #print('Getting price for symbol %s ...' % symbol)

    s = requests.session()
    url = 'https://api.wazirx.com/sapi/v1/ticker/24hr?symbol='+symbol
    for i in range(5):
        try:
            r = s.get(url)
            break
        except Exception as e:
            if i>1: print('Exception %d: wazirx %s:' % (i, symbol), e)

    d = json.loads(r.content)
    #print(d['symbol'], d['lastPrice'])
    return float(d['lastPrice'])

def get_fng():
    print('Getting fear and greed index ...') 
    # https://alternative.me/crypto/fear-and-greed-index/
    
    s = requests.session()
    url = 'https://api.alternative.me/fng/?limit=10'
    r = s.get(url)

    d = json.loads(r.content)
    fglist = [int(x['value']) for x in d['data']]
    print(fglist)
    print('Average Greed: %d%%' % (sum(fglist)/len(fglist)))
    print('-------------------------------------------------------')

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

def post_process_crypto():
    file = get_latest_file(basecrypto)
    print('\nProcessing file %s ...' % file)
    df = file2df(file)
    
    dfgroup = df[['Symbol', 'Value', 'ValueYF', 'Cost', 'Units']]
    summary_sym = dfgroup.groupby('Symbol').agg('sum')
    summary_sym['Value'] = (summary_sym['Value']/100000).apply(lambda x: round(x, 1))
    summary_sym['ValueYF'] = (summary_sym['ValueYF']/100000).apply(lambda x: round(x, 1))
    summary_sym['Cost'] = (summary_sym['Cost']/100000).apply(lambda x: round(x, 1))
    summary_sym['ProfitPC'] = (100*(summary_sym['Value'] - summary_sym['Cost'])/summary_sym['Cost']).apply(lambda x: round(x, 1))

    cost = summary_sym['Cost'].sum()
    val = summary_sym['Value'].sum()
    profit = 100*(val-cost)/cost
    valYF = summary_sym['ValueYF'].sum()
    spread = 100 * (val - valYF) / valYF
    summary_sym['Percent'] = (100*summary_sym['Value']/val).apply(lambda x: round(x, 1))

    print('\nSummary by symbol\n')
    print(summary_sym[['Units', 'Cost', 'Value', 'ValueYF', 'ProfitPC', 'Percent']])

    dfgroup = df[['Owner', 'Value', 'ValueYF', 'Cost', 'Units']]
    summary_own = dfgroup.groupby('Owner').agg('sum')
    summary_own['Value'] = (summary_own['Value']/100000).apply(lambda x: round(x, 1))
    summary_own['ValueYF'] = (summary_own['ValueYF']/100000).apply(lambda x: round(x, 1))
    summary_own['Cost'] = (summary_own['Cost']/100000).apply(lambda x: round(x, 1))
    summary_own['ProfitPC'] = (100*(summary_own['Value'] - summary_own['Cost'])/summary_own['Cost']).apply(lambda x: round(x, 1))
    summary_own['Percent'] = (100*summary_own['Value']/val).apply(lambda x: round(x, 1))
    print('\nSummary by owner\n')
    print(summary_own[['Cost', 'Value', 'ValueYF', 'ProfitPC', 'Percent']])


    print('\nTOTAL cost %.1f, value %.1f, profit %d%%' % (cost, val, profit))
    print('ValueYF %.1f spread %d%%' % (valYF, spread))
    print('-------------------------------------------------------')

# ----------------------------------------------------------------------------

args = argparse.ArgumentParser(description='Generate report')
args.add_argument('--process', '-p', help='only process most recent file', type=int, default=0)
args = args.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')

data = config['data']
basecrypto = data['basecrypto']
basecryptocostdet = data['basecryptocostdet']

basevested = data['basevested']
basevesteddet = data['basevesteddet']

if args.process == 0:
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
    print(symbol_price,'\n')

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

    # process crypto file
    filedet = get_latest_file(basecryptocostdet)
    df = file2df(filedet)

    print('\nProcessing file %s ...' % filedet)

    wazirx_price = {}

    # create a symbol map
    symbol_map = {}
    syms = df.Symbol.unique()
    #print(syms)

    for sym in syms:
        if symbol_map.get(sym, '') == '':
            symbol_map[sym] = (sym+'-USD')
        # for i in range(5):
        #     try:
        #         wazirx_price[sym] = get_price_wazirx(sym)
        #         time.sleep(1)
        #         break
        #     except Exception as e:
        #         print('Exception %d: %s: wazirx' % (i, sym), e)
        #         time.sleep(3)

    wazirx_price = get_price_wazirx_all(syms)
    
    print(wazirx_price)

    # get the symbol prices from yahoo
#    for sym in syms:
#        s = symbol_map[sym]
#        symbol_price[sym] = get_price(s)
#        if symbol_price[sym] == -1:
#            print('ERROR: Failed to get price for %s!!' % s)
#            sys.exit(1)
    # get symbol proces from coin market cap
    symbol_price = get_price_cmc(['BTC', 'ETH', 'SOL', 'WRX', 'MANA'])
    print([(x[0], int(x[1])) for x in symbol_price.items()])

    for index, row in df.iterrows():
        s = row['Symbol']
        df.at[index, 'NAV'] = symbol_price[s]
        df.at[index, 'NAVINR'] = wazirx_price[s]
        df.at[index, 'USD'] = usdinr
        df.at[index, 'ValueWX'] = row['Units'] * wazirx_price[s]
        df.at[index, 'ValueYF'] = row['Units'] * symbol_price[s] * usdinr
        df.at[index, 'Value'] = row['Units'] * symbol_price[s] * usdinr

    # Generate fund excel
    fname = basecrypto+nowstr+'.xlsx'
    df.to_excel(fname, index=False, engine='xlsxwriter')
    print("\nWritten %d rows to file %s ..." % (len(df),fname))
    print('-------------------------------------------------------')

post_process_crypto()
get_fng()



