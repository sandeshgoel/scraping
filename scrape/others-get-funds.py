import yfinance as yf
import pandas as pd
import argparse
import time
import sys
import configparser
import glob
      
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
    df = pd.read_excel(file)
    #df.rename(columns={'Instrument':'Symbol', 'Qty.':'Units'}, inplace=True)
    
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
    print(f'Goldrate from {goldfile}: {goldrate}')
    return goldrate
    
def get_latest_aedinr_rate():
    config = configparser.ConfigParser()
    config.read('config.ini')
    data = config['data']
    basecurrency = data['basecurrency']
    currencyfile = get_latest_file(basecurrency)
    xl = pd.ExcelFile(currencyfile)
    df = xl.parse(0)
    records = df.to_dict()
    aedinr = records['AED'][0]
    print(f'AEDINR from {currencyfile}: {aedinr}')
    return aedinr
    
# ----------------------------------------------------------------------------

args = argparse.ArgumentParser(description='Generate report')
args = args.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')

data = config['data']
baseothers = data['baseothers']
baseholdothers = data['baseholdothers']

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H', time.gmtime(now))
nowpr = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(now))
print("Current time: %s\n" % nowpr)

# process others file
filedet = get_latest_file(baseholdothers)
print('Processing file %s ...' % filedet)

dfv = file2df(filedet)

if set(['Accrue', 'Created', 'Rate', 'Value']).issubset(dfv.columns):
    today = pd.Timestamp.today().normalize()
    accrue_mask = dfv['Accrue'].astype(str).str.lower().str.strip() == 'y'
    
    created_dates = pd.to_datetime(dfv['Created'], errors='coerce')
    days_diff = (today - created_dates).dt.days
    
    rate = pd.to_numeric(dfv['Rate'], errors='coerce')
    value = pd.to_numeric(dfv['Value'], errors='coerce')
    
    interest = value * (rate / 100.0) * (days_diff / 365.0)
    
    valid_mask = accrue_mask & created_dates.notna() & rate.notna() & value.notna()
    dfv.loc[valid_mask, 'Value'] = value[valid_mask] + interest[valid_mask]

    # set 'Accrue' to blank now
    dfv.loc[valid_mask, 'Accrue'] = ''
else:
    print('Columns Accrue, Created, Rate, Value not found in the file')


# if 'Category' is Jewellery, then multiply 'area' with per gram gold rate
if 'Category' in dfv.columns:
    goldrate = get_latest_gold_rate()
    jewellery_mask = dfv['Category'].astype(str).str.lower().str.strip() == 'jewellery'
    dfv.loc[jewellery_mask, 'Value'] = dfv.loc[jewellery_mask, 'area'] * goldrate / 100000

# if 'currency' is AED, then mutliply area and rate with AEDINR
if 'currency' in dfv.columns:
    # get latest AEDINR rate
    aedinr = get_latest_aedinr_rate()
    aedinr_mask = dfv['currency'].astype(str).str.lower().str.strip() == 'aed'
    dfv.loc[aedinr_mask, 'Value'] = dfv.loc[aedinr_mask, 'area'] * dfv.loc[aedinr_mask, 'rate'] * aedinr
    

#print(dfv)

# Generate fund excel
fname = baseothers+nowstr+'.xlsx'
dfv.to_excel(fname, index=False, engine='xlsxwriter')
print("\nWritten %d rows to file %s ..." % (len(dfv),fname))
print('-------------------------------------------------------')




