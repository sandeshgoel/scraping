import time
import glob
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import numpy as np
import sys
import xlsxwriter
from xlsxwriter.utility import * #xl_rowcol_to_cell
import configparser

from time_util import *

def label_category(row):    
    if ('GOLD' in row['Code']) or ('SGB' in row['Code']):
        return 'GOLD'
    if 'NIFTY' in row['Code'] or 'NIFETF' in row['Code']:
        return 'NIFTY'
    return 'STOCKS'

def label_subtype(row):
    if row['Category'] in ['GOLD']:
        return 'GOLD'

    if row['Category'] in ['FD']:
        return 'FD'
    if row['Category'] in ['TM', 'Gilt']:
        return 'GILT'
    if row['Category'] in ['DEBT', 'CASH', 'Liquid']:
        return 'LIQUID'
    if row['Category'] in ['Short Duration', 'Corporate Bond', 'Credit Risk']:
        return 'STDEBT'
    if row['Category'] in ['EPF', 'PPF', 'NPS', 'SCSS', 'PMVVY', 'LIC', 'RBI']:
        return 'BOND'

    if row['Category'] in ['NIFTY', 'Index', 'EQUITY']:
        return 'PASSIVE'
    if row['Category'] in ['Value', 'Balanced', 'Focussed', 'Multi Cap', 'Large Cap']:
        return 'ACTIVE'
    if row['Category'] in ['STOCKS', 'Small Cap', 'PMS']:
        return 'ACTIVE'
    if row['Category'] in ['Mid Cap']:
        return 'ACTIVE'
    if row['Category'] in ['PE']:
        return 'PE'

    if row['Category'] in ['Global', 'USA', 'China']:
        return 'GLOBAL'

    if (row['Source'] in ['CRYPTO']) or (row['Category'] in ['CRYPTO', 'BTCETF']):
        return 'CRYPTO'

    if row['Category'] in ['Contingency']:
        return 'CONTINGENCY'

    if row['Category'] in ['PROPERTY']:
        return 'PROPERTY'

    print('label_subtype: Invalid category: %s' % row['Category'])
    print(row)
    sys.exit(1)

subtype2type = {'GOLD':'GOLD', 
                'BOND':'DEBT', 'GILT':'DEBT', 'FD':'DEBT', 'LIQUID':'DEBT', 'STDEBT':'DEBT',
                'PASSIVE':'EQUITY', 'ACTIVE':'EQUITY',
                'PE': 'PE',
                'GLOBAL':'GLOBAL',
                'CRYPTO':'CRYPTO',
                'CONTINGENCY':'CONTINGENCY',
                'PROPERTY': 'CONTINGENCY'}
target = {'GOLD':10.5, 
          'BOND':20, 'GILT':10, 'FD':5, 'STDEBT':2, 'LIQUID':18, 
          'PASSIVE':4, 'ACTIVE':10, 
          'PE':5.5,
          'GLOBAL':11,
          'CRYPTO':4}

def label_type(row):
    return subtype2type[row['Subtype']]

def targetType(typ):
    t = 0
    for k in target.keys():
        if subtype2type[k] == typ: t += target[k]
    return t
    
# -----------------------------------------------------------------------------

def get_latest_file(base, owner=None, ext='xls'):
    if owner is None:
        fname = base + '202*.'+ext+'*'
    else:
        fname = base + '202*-' + owner + '.'+ext+'*'
    files = glob.glob(fname)
    if files == []: 
        print("get_latest_file: %s No files found %s" % (base, fname))
        return ""
    file = sorted(files)[-1]
    return file

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
    
def get_report_file(now, offset):
    base = "REPORTS/report-"
    nowdate = time_str_date_utc(now - offset*86400)
    fname = base + nowdate + '.xlsx'
    files = glob.glob(fname)
    if files == []: 
        #print("No files found %s" % fname)
        return ""
    file = files[0]
    return file

def get_amfi_file(now, offset):
    base = "DATA/amfi-"
    nowdate = time_str_date_utc(now - offset*86400)
    fname = base + nowdate + '*.xls*'
    files = glob.glob(fname)
    if files == []: 
        #print("No files found %s" % fname)
        return ""
    file = files[0]
    return file

def get_file(now, offset, base, ext='xls'):
    nowdate = time_str_date_utc(now - offset*86400)
    fname = base + nowdate + '*.' + ext + '*'
    files = glob.glob(fname)
    if files == []: 
        #print("No files found %s" % fname)
        return ""
    files.sort(reverse=True)
    file = files[0]
    return file

def get_classifier_df():
    file = "fund-classifier.xls"
    xl = pd.ExcelFile(file)
    total_rows = xl.book.sheet_by_index(0).nrows
    df = xl.parse(0) #, skiprows=1, skip_footer=1)

    dfc = pd.DataFrame()
    dfc['Code'] = df['Fund Code'] + '-' + df['Scheme Code']
    dfc['Classification'] = df['Classification']
    return dfc

def get_isin_classifier_df():
    file = "isin-classifier.xls"
    xl = pd.ExcelFile(file)
    total_rows = xl.book.sheet_by_index(0).nrows
    df = xl.parse(0) #, skiprows=1, skip_footer=1)
    return df

def get_amfi_df(now, offset):
    file = get_amfi_file(now, offset)
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)
    #total_rows = xl.book.sheet_by_index(0).nrows
    df = xl.parse(0, skiprows=1, skipfooter=1)

    df.rename(columns={'Fund Name':'Fund',
                       'Scheme Details':'Desc',
                       'Current Value based on NAV':"NAV", 
                       'as on NAV Date':'Date', 
                       'Current Value':'Value'},
              inplace=True)
    return df
    
# -----------------------------------------------------------------------------


def file2df_mfparse(file):
    if file == "":
        return pd.DataFrame()
    try:
        xl = pd.ExcelFile(file)
    except Exception as e:
        print(e)
        print(file)
        sys.exit(1)

    df = xl.parse(0)
    df = df.replace(np.nan, 0, regex=True)
    df['Value'] = df['Value']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Direct'] = df['Desc'].str.contains('Direct', case=False)
    df['Source'] = 'MFU'
    if 'Owner' not in df.columns: 
        df['Owner'] = 'sandesh'
    
    return df

def file2df_funds(file):
    if file == "":
        return pd.DataFrame()
    try:
        xl = pd.ExcelFile(file)
    except Exception as e:
        print(e)
        print(file)
        sys.exit(1)

    #total_rows = xl.book.sheet_by_index(0).nrows
    df = xl.parse(0, skiprows=1, skipfooter=1)

    df.rename(columns={'Fund Name':'Fund',
                       'Scheme Details':'Desc',
                       'Current Value based on NAV':"NAV", 
                       'as on NAV Date':'Date', 
                       'Current Value':'Value'},
              inplace=True)
    df = df.replace(np.nan, 0, regex=True)
    #print(df[['Desc', 'Value']])
    #df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df['Value'] = df['Value']/100000

    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Direct'] = df['Desc'].str.contains('Direct', case=False)
    df['Code'] = df['Fund Code'] + '-' + df['Scheme Code']
    df['Source'] = 'MFU'
    df['Owner'] = 'sandesh'
    
    if 'Fund Code' in df: df.pop('Fund Code')
    if 'Scheme Code' in df: df.pop('Scheme Code')

    return df

def get_funds_df(now, offset, base, dfc, basemfparse, dfic):
    nowdate = time_str_date_utc(now - offset*86400)
    if nowdate >= '2023-10-04':
        file = get_file(now, offset, basemfparse)
        df = file2df_mfparse(file)
        if not df.empty:
            df = pd.merge(df, dfic, how='left', on='ISIN')
            df.fillna('unknown', inplace=True)
            df['Category'] = np.where(df['Classification'] == 'unknown', df['Category'], df['Classification'])    
    else:
        file = get_file(now, offset, base)
        df = file2df_funds(file)
        if not df.empty:
            df = pd.merge(df, dfc, how='left', on='Code')
            df.fillna('unknown', inplace=True)
            df['Category'] = np.where(df['Classification'] == 'unknown', df['Category'], df['Classification'])    
    return df

def file2df_geojit(file, base):    
    if file == "":
        return pd.DataFrame()

    datestart=len(base)
    nowdate = file[datestart:datestart+10]
    #print(file, nowdate)

    if nowdate >= '2024-03-26':
        if nowdate >= '2024-05-03':
            df = pd.read_csv(file, skiprows=2, index_col=False)#, dtype={'MktVal': 'Int32'})
        else:
            xl = pd.ExcelFile(file)
            df = xl.parse(0, skiprows=2)
        if len(df.index) == 0:
            return pd.DataFrame()
        df.rename(columns={'Net Pos':'Units',
                           'MktRate':"NAV",  
                           'MktVal':'Value',
                           'Symbol':'Code'},
                  inplace=True)
    else:
        xl = pd.ExcelFile(file)
        df = xl.parse(0, skipfooter=1)
        if len(df.index) == 0:
            return pd.DataFrame()
        df.rename(columns={'Net Qty':'Units',
                           'Mkt Rate':"NAV",  
                           'Mkt Val':'Value',
                           'Security Name':'Code'},
                  inplace=True)
    df['Value'] = df['Value']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Category'] = df.apply (lambda row: label_category (row),axis=1)
    df['Source'] = 'GEOJIT'
    df['Owner'] = 'sandesh'
    df['Desc'] = df['Code']
    if 'Product' in df: df.pop('Product')
    if 'Venue' in df: df.pop('Venue')
    if 'InstType/Exp/ Strike/Opt' in df: df.pop('InstType/Exp/ Strike/Opt')
    if 'AvgRate' in df: df.pop('AvgRate')
    if 'Gain/Loss' in df: df.pop('Gain/Loss')
    return df

def get_geojit_df(now, offset, base):
    file = get_file(now, offset, base, ext='')
    return file2df_geojit(file, base)

def file2df_zerodha(file, base):
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)    
    
    #nowdate = time_str_date_utc(now - offset*86400)
    datestart=len(base)
    nowdate = file[datestart:datestart+10]
    #print(file, nowdate)

    if nowdate >= '2022-10-14':
        df = xl.parse(0, skiprows=22)
        if len(df.index) == 0:
            print('Empty file', file)
            return pd.DataFrame()
        df.rename(columns={'Quantity Available':'Units',
                           'Previous Closing Price':"NAV", 
                           'Symbol':'Code'},
                  inplace=True)
        df['Value'] = df['Units'] * df['NAV']
    elif nowdate >= '2021-01-12':
        #print('%s: New format' % file)
        df = xl.parse(0, thousands=',')
        if len(df.index) == 0:
            return pd.DataFrame()

        if nowdate >= '2022-06-03':
            df.rename(columns={'Qty.':'Units',
                           'LTP':"NAV",  
                           'Present value':'Value',
                           'Symbol':'Code'},
                  inplace=True)
        else:
            df.rename(columns={'Qty.':'Units',
                           'Prev. close':"NAV",  
                           'Present value':'Value',
                           'Symbol':'Code'},
                  inplace=True)
    elif nowdate >= '2020-02-21':
        #print('%s: New format' % file)
        df = xl.parse(0, skiprows=9)
        if len(df.index) == 0:
            return pd.DataFrame()

        df.rename(columns={'Qty Available':'Units',
                           'Previous Closing Price':"NAV",  
                           'Current Value':'Value',
                           'Symbol':'Code'},
                  inplace=True)
    elif nowdate >= '2019-02-13':
        #print('%s: New format' % file)
        df = xl.parse(0, skiprows=9, skipfooter=2)
        if len(df.index) == 0:
            return pd.DataFrame()

        df.rename(columns={'Qty Available':'Units',
                           'Previous Closing Price':"NAV",  
                           'Current Value':'Value',
                           'Symbol':'Code'},
                  inplace=True)
    elif nowdate >= '2019-02-01':
        #print('%s: New format' % file)
        df = xl.parse(0, skiprows=9, skipfooter=1)
        if len(df.index) == 0:
            return pd.DataFrame()

        df.rename(columns={'Qty Available':'Units',
                           'Previous Closing Price':"NAV",  
                           'Closing Value':'Value',
                           'Symbol':'Code'},
                  inplace=True)
    elif nowdate >= '2018-12-05':
        #print('%s: New format' % file)
        df = xl.parse(0, skiprows=9)
        if len(df.index) == 0:
            return pd.DataFrame()

        df.rename(columns={'Qty Available':'Units',
                           'Previous Closing Price':"NAV",  
                           'Closing Value':'Value',
                           'Symbol':'Code'},
                  inplace=True)
        #print(df)
    elif nowdate >= '2018-11-14':
        #print('%s: New format' % file)
        df = xl.parse(0, skiprows=6)
        if len(df.index) == 0:
            return pd.DataFrame()

        df.rename(columns={'Qty Available':'Units',
                           'Previous Closing Price':"NAV",  
                           'Closing Value':'Value',
                           'Trading Symbol':'Code'},
                  inplace=True)
        #print(df)
    else:
        df = xl.parse(0, skiprows=13, skipfooter=10)
        if len(df.index) == 0:
            return pd.DataFrame()

        df.rename(columns={'Quantity':'Units',
                           'Prev. closing price':"NAV",  
                           'Present value':'Value',
                           'Symbol':'Code'},
                  inplace=True)

    df['Value'] = df['Value']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Category'] = df.apply (lambda row: label_category (row),axis=1)
    df['Source'] = 'ZERODHA'
    df['Owner'] = 'sandesh'
    df['Desc'] = df['Code']
    return df

def get_zerodha_df(now, offset, base):
    file = get_file(now, offset, base)
    return file2df_zerodha(file, base)

def file2df_assets(file, base):
    if file == "":
        return pd.DataFrame()
    #print(file)
    xl = pd.ExcelFile(file)
    df = xl.parse(0)
    df.dropna(subset=['Category'], inplace=True)
    
    datestart = len(base)
    nowdate = file[datestart:datestart+10]

    if nowdate < '2023-06-03':
        df = pd.concat([df,pd.DataFrame({'Category': ['PROPERTY'], 
                                         'Desc': ['Aggregate'], 
                                         'Value': [84000000], 
                                         'Owner': ['sandesh']})
                        ],
                        ignore_index=True)

    if nowdate >= '2024-09-27':
        gold_rate = get_latest_gold_rate()
        df.loc[df['Category'] == 'GOLD', 'Value'] = df['area'] * 0.9 * gold_rate / 100000
        #print(df[df['Category'].isin(['GOLD', 'Liquid'])])

    if nowdate >= '2023-07-28':
        df['Value'] = df['Value']
    else:
        df['Value'] = df['Value']/100000

    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Source'] = 'OTHERS'
    df['Today'] = datetime.date.today()
    df['Today'] = pd.to_datetime(df['Today'])
    df['Interest'] = 0.0
    df['Age'] = 0
    df['Principal'] = df['Value']
    for index, row in df.iterrows():
        if row.get('Accrue', '') == 'y':
            age = (row['Today']- row['Created']).days
            df.at[index, 'Age'] = age
            interest = 0.9 * age * row['Rate'] * row['Value'] / 36500
            df.at[index, 'Interest'] = interest
            df.at[index, 'Value'] = row['Value'] + interest
        if nowdate >= '2021-01-01' and row.get('Maturity', '') != '':
            ttm = (row['Maturity'] - row['Today']).days
            df.at[index, 'TTM'] = ttm

    return df

def get_assets_df(now, offset, base):
    file = get_file(now, offset, base)
    return file2df_assets(file, base)

def file2df_crypto(file, base):
    if file == "":
        return pd.DataFrame()
    #print(file)
    xl = pd.ExcelFile(file)
    df = xl.parse(0)
    
    df['Value'] = df['Value']/100000
    if 'ValueYF' in df.columns:
        df['ValueYF'] = df['ValueYF']/100000
    if 'Cost' in df.columns:
        df['Cost'] = df['Cost']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Source'] = 'CRYPTO'
    df['Category'] = df['Desc']
    return df

def get_crypto_df(now, offset, base):
    file = get_file(now, offset, base)
    try:
        return file2df_crypto(file, base)
    except Exception as e:
        print(e)
        print(file)
        sys.exit(1)

def get_hdfc_df(now, offset, base):
    file = get_file(now, offset, base)
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)
    df = xl.parse(0)  
    return df

def get_axis_df(now, offset, base):
    file = get_file(now, offset, base)
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)
    df = xl.parse(0)  
    return df

def file2df_idfc(file, base):
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)
    df = xl.parse(0)

    df['Value'] = df['Amount']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Owner'] = df['Name']
    df['Desc'] = df['Name']+' IDFC'
    df['Source'] = 'IDFC'
    df['Category'] = 'Liquid'
    
    return df

def get_idfc_df(now, offset, base):
    file = get_file(now, offset, base)
    return file2df_idfc(file, base)

def file2df_cm(file, base):
    if file == "":
        return pd.DataFrame()
    xl = pd.ExcelFile(file)
    df = xl.parse(0)

    df['Value'] = df['Current']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Owner'] = 'sandesh'
    df['Desc'] = 'Capitalmind PMS'
    df['Source'] = 'Capitalmind'
    df['Category'] = 'PMS'
    
    return df

def get_cm_df(now, offset, base):
    file = get_file(now, offset, base)
    return file2df_cm(file, base)
    
def file2df_vested(file, base):
    if file == "":
        return pd.DataFrame()
    #print(file)
    xl = pd.ExcelFile(file)
    df = xl.parse(0)
    
    df['Value'] = df['Value']/100000
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    df['Source'] = 'VESTED'
    df['Category'] = 'USA'
    df.loc[df['Desc'] == 'USD', 'Category'] = 'Liquid'
    df.loc[df['Desc'] == 'IBIT', 'Category'] = 'BTCETF'
    df.loc[df['Desc'] == 'KWEB', 'Category'] = 'China'
    return df

def get_vested_df(now, offset, base):
    file = get_file(now, offset, base)
    return file2df_vested(file, base)

    
# -----------------------------------------------------------------------------


def get_recent_df(daily, NUM_DAYS):
    offset = 0
    while (offset < NUM_DAYS) and (daily[offset].empty): offset += 1
    if offset == NUM_DAYS:
        print("No file found in last %d days" % NUM_DAYS)
        offset = 0
    return daily[offset], offset

def get_summary_from_combined(dfi, owner=''):
    df = dfi.copy()

    if owner != '': df = df[df['Owner']==owner]

    #pd.set_option('display.max_rows', None)
    #print(df[['Desc', 'Category']])

    df['Subtype'] = df.apply (lambda row: label_subtype (row),axis=1)
    df['Type'] = df.apply (lambda row: label_type (row),axis=1)
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()

    dff = df.copy()

    df = df[df['Type']!='CONTINGENCY']
    #df.drop(df[df['Type']=='CONTINGENCY'].index, inplace = True)
    df['Percent'] = 100 * df['Value'] / df['Value'].sum()
    #print(df[['Desc','Value']])
    #print('Before, after contingency', len(df), len(dff))

    dfgroup = df[['Type', 'Subtype','Value']]
    sub = dfgroup.groupby(['Type','Subtype']).agg('sum')
    sub['Percent'] = 100 * sub['Value'] / sub['Value'].sum()
    #print(sub)

    dfgroup = df[['Type', 'Subtype', 'Category', 'Value']]
    cat = dfgroup.groupby(['Type', 'Subtype', 'Category']).agg('sum')
    cat['Percent'] = 100 * cat['Value'] / cat['Value'].sum()
    #print(cat)

    dfgroup = df[['Type', 'Value']]
    typ = dfgroup.groupby('Type').agg('sum')
    typ['Percent'] = 100 * typ['Value'] / typ['Value'].sum()
    #print(typ)
    typ['Value'].plot.pie(subplots=True, autopct='%3.1f%%')

    dfgroup = df[['Source', 'Value']]
    ave = dfgroup.groupby('Source').agg('sum')
    ave['Percent'] = 100 * ave['Value'] / ave['Value'].sum()
    #print(ave)
    
    dfgroup = df[['Direct', 'Value']]
    dir = dfgroup.groupby('Direct').agg('sum')
    dir['Percent'] = 100 * dir['Value'] / dir['Value'].sum()
    #print(dir)

    dfgroup = df[['Owner', 'Value']]
    own = dfgroup.groupby('Owner').agg('sum')
    own['Percent'] = 100 * own['Value'] / own['Value'].sum()
    #print(own)

    return sub, cat, typ, ave, dir, own, df, dff
    
def get_summary(df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfv_daily, NUM_DAYS, owner=''):
    df, o = get_recent_df(df_daily, NUM_DAYS)
    dfg, og = get_recent_df(dfg_daily, NUM_DAYS)
    dfz, oz = get_recent_df(dfz_daily, NUM_DAYS)
    dfa, oa = get_recent_df(dfa_daily, NUM_DAYS)
    dfc, oc = get_recent_df(dfc_daily, NUM_DAYS)
    dfb, ob = get_recent_df(dfb_daily, NUM_DAYS)
    dfcm, ocm = get_recent_df(dfcm_daily, NUM_DAYS)
    dfv, ov = get_recent_df(dfv_daily, NUM_DAYS)
   
    df = pd.concat([df, dfg, dfz, dfa, dfc, dfb, dfcm, dfv])
    return get_summary_from_combined(df, owner)


def label_transaction(row):
    if row['Units'] < 0:
        return 'SOLD'
    else:
        return 'BOUGHT'
    
def funds_delta(dfo, dfn, date, offset):
    dfn = dfn.rename(columns={'Units':'new Units', 'NAV':'new NAV', 'Desc':'new Desc'})
    dfo = dfo.rename(columns={'Units':'old Units', 'NAV':'old NAV', 'Desc':'old Desc'})
    joined = pd.merge(dfo, dfn, how='outer', on='Code')
    joined.fillna(0, inplace=True)
    
    joined['Units'] = joined['new Units'] - joined['old Units']
    joined['NAV'] = np.where(joined['Units'] < 0, joined['old NAV'], joined['new NAV'])
    joined['Desc'] = np.where(joined['Units'] < 0, joined['old Desc'], joined['new Desc'])
    joined['Date'] = date
    joined['Offset'] = offset
    joined['Amount'] = (joined['Units'] * joined['NAV']).astype(int)
    joined['Transaction'] = joined.apply (lambda row: label_transaction (row),axis=1)
    joined = joined[['Date', 'Code', 'Transaction', 'Units', 'NAV', 'Amount', 
                     'old Units', 'new Units', 'Offset', 'Desc']]

    joined['Units'] = joined['Units'].abs()
    joined['Amount'] = joined['Amount'].abs()

    joined = joined.loc[joined['Units'] != 0]
    return joined

def changelog(daily, NUM_DAYS, now):
    changes = pd.DataFrame()
    offset = 0
    while offset < NUM_DAYS:
        while offset < NUM_DAYS and daily[offset].empty: offset += 1
        if offset >= (NUM_DAYS-1): break
        offn = offset
        dfn = daily[offset]
        offset += 1
        while offset < NUM_DAYS and daily[offset].empty: offset += 1
        if offset >= NUM_DAYS: break
        offo = offset
        dfo = daily[offset]
        
        sdate = time_str_date_utc(now - offn*86400)
        #print("*** Comparing offsets", offo, offn)
        delta = funds_delta(dfo, dfn, sdate, offo-offn)
        #print(delta)
        changes = pd.concat([changes, delta])
    return changes

def get_nearest_df(daily, offset, NUM_DAYS):
    orig = offset
    # first look in the past
    while(offset < NUM_DAYS and daily[offset].empty):
        offset += 1
    if offset == NUM_DAYS: 
        offset = orig
        # nothing found in past, so look in future
        while(offset >= 0 and daily[offset].empty):
            offset -= 1
        if offset == -1:
            offset = orig
    return daily[offset]

def get_stats(df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfv_daily, offset, NUM_DAYS, now, owner):
    df = get_nearest_df(df_daily, offset, NUM_DAYS)
    dfg = get_nearest_df(dfg_daily, offset, NUM_DAYS)
    dfz = get_nearest_df(dfz_daily, offset, NUM_DAYS)
    dfa = get_nearest_df(dfa_daily, offset, NUM_DAYS)
    dfc = get_nearest_df(dfc_daily, offset, NUM_DAYS)
    dfb = get_nearest_df(dfb_daily, offset, NUM_DAYS)
    dfcm = get_nearest_df(dfcm_daily, offset, NUM_DAYS)
    dfv = get_nearest_df(dfv_daily, offset, NUM_DAYS)
   
    df =  pd.concat([df, dfg, dfz, dfa, dfc, dfb, dfcm, dfv])
    if df.empty: return pd.DataFrame(), pd.DataFrame()

    if owner != '': df = df[df['Owner']==owner]

    df['Subtype'] = df.apply (lambda row: label_subtype (row),axis=1)
    df['Type'] = df.apply (lambda row: label_type (row),axis=1)

    sdate = time_str_date_utc(now - offset*86400)
    total = df['Value'].sum()
    data_typ = {'Date':sdate, 'Total':total}
    data_cat = {'Date':sdate, 'Total':total}

    dfgroup = df[['Category', 'Value']]
    summary_cat = dfgroup.groupby('Category').agg('sum')
    for index, row in summary_cat.iterrows():
        data_cat[index] = row['Value']
        
    dfgroup = df[['Type', 'Value']]
    summary_typ = dfgroup.groupby('Type').agg('sum')
    for index, row in summary_typ.iterrows():
        data_typ[index] = row['Value']

    stats_typ = pd.DataFrame([data_typ])
    stats_typ.fillna(0, inplace=True)

    stats_cat = pd.DataFrame([data_cat])
    stats_cat.fillna(0, inplace=True)
    return stats_typ, stats_cat, total

def get_daily_stats(df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfv_daily, NUM_DAYS, now, owner=''):
    stats_daily_typ = pd.DataFrame()
    stats_daily_cat = pd.DataFrame()

    stats_weekly_typ = pd.DataFrame()
    stats_weekly_cat = pd.DataFrame()

    totalh = 0
    totallist = []
    for offset in range(NUM_DAYS):
        row_typ, row_cat, total = get_stats(df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfv_daily, offset, NUM_DAYS, now, owner)
        totallist.append(total)
        stats_daily_typ = pd.concat([stats_daily_typ, row_typ])
        stats_daily_cat = pd.concat([stats_daily_cat, row_cat])
        if total > totalh:
            totalh = total
            row_typh = row_typ
            row_cath = row_cat
        if (offset % 7) == 6:
            stats_weekly_typ = pd.concat([stats_weekly_typ, row_typh])
            stats_weekly_cat = pd.concat([stats_weekly_cat, row_cath])
            totalh = 0

    stats_daily_typ.fillna(0, inplace=True)
    #stats_daily_typ.sort_values(by='Date', ascending=True, inplace=True)
    stats_daily_cat.fillna(0, inplace=True)
    #stats_daily_cat.sort_values(by='Date', ascending=True, inplace=True)

    return stats_daily_typ, stats_daily_cat, stats_weekly_typ, stats_weekly_cat, totallist

# ---------------------------------------------------
# Generate fund excel
# ---------------------------------------------------

def add_ws(wb, df, o, title, style, now):
    wsname = title
    print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)

    mfu = False    
    if title == 'MFU': mfu = True

    row = 0
    if mfu:
        cols = ['Desc', 'Direct', 'Classification', 'Folio#', 'Units', 'NAV', 'Value']
    elif title in ['Geojit','Zerodha']:
        cols = ['Desc', 'Units', 'NAV', 'Value']
    elif title in ['Crypto']:
        cols = ['Symbol', 'Desc', 'Units', 'NAVINR', 'NAV', 'USD', 'Value', 'ValueYF', 'Owner', 'Held in']
    elif title in ['IDFC']:
        cols = ['Desc','Value', 'Owner']
    elif title in ['Capitalmind']:
        cols = ['Desc','Total', 'Value', 'Owner']
    else: # Others
        cols = ['Desc', 'Value', 'Owner', 'Maturity', 'Created', 'Rate', 'Principal', 'TTM']
        df['Maturity'] = df['Maturity'].dt.strftime('%Y-%m')
        df['Created'] = df['Created'].dt.strftime('%Y-%m')
        df = df.infer_objects(copy=False).fillna(0)

    ws.write_row(row, 0, cols+['Percent'], style['bold'])
    row += 2

    df['Subtype'] = df.apply (lambda row: label_subtype (row),axis=1)
    df['Type'] = df.apply (lambda row: label_type (row),axis=1)

    dfgroup = df[['Subtype', 'Value', 'Percent']]
    summary_cat = dfgroup.groupby('Subtype').agg('sum')

    for cat in summary_cat.index:
        dfcat = df.loc[df['Subtype'] == cat]
        dfcat = dfcat.sort_values(by='Value', ascending=False, inplace=False)
        cnt = len(dfcat)

        ws.write_row(row, 0, [cat + ' (' + str(cnt) + ')'], style['bold'])
        row += 1

        for i, x in dfcat.iterrows():
            ws.write_row(row, 0, [x[y] for y in cols])
            ws.write_row(row, len(cols), [x['Percent']/100], style['percent'])
            row += 1
        row += 1

    nowdate = time_str_date_utc(now - o*86400)
    ws.write_row(row, 0, 
                 ['NOTE: Data as of date ' + nowdate + ' (%d days old)' % o], 
                 style['ital'])
    row += 2
    if mfu:
        ws.set_column(0, 0, 50)
    else:
        ws.set_column(0, 0, 20)

    out_str = 'TOTAL: %4.2f Cr (%d funds)' % (summary_cat['Value'].sum()/100, len(df))
    ws.write_row(row, 0, [out_str], style['large-red'])
    print('\t' + out_str)
    row += 1
    
    if mfu:
        dfgroup = df[['Direct', 'Value']]
        summary_dir = dfgroup.groupby('Direct').agg('sum')
        dfdir = df.loc[df['Direct'] == False]
        num_ind = len(dfdir)
        ws.write_row(row, 0, ['Indirect MF: %4.2f Cr (%d funds)' % 
                              (summary_dir.loc[False]['Value']/100 if (num_ind > 0) else 0, num_ind)], style['bold'])
        row += 1
    row += 1

    # today split by subtype
    ws.write_row(row, 0, ['Category', 'Value (L)', 'Percent'], style['bold'])
    row += 1
    numrows = 0
    types = summary_cat.index.values
    for x in types:
        ws.write_row(row, 0, [x])
        ws.write_row(row, 1, [summary_cat.loc[x]['Value']], style['value'])
        ws.write_row(row, 2, [summary_cat.loc[x]['Percent']/100], style['percent'])
        row += 1
        numrows += 1

    chart1 = wb.add_chart({'type': 'pie'})
    chart1.add_series({
        'name':       'Category split',
        'categories': [wsname, row-numrows, 0, row-1, 0],
        'values':     [wsname, row-numrows, 1, row-1, 1],
        'data_labels':{'percentage':True,'category':True,'position':'outside_end'}
    })
    chart1.set_title({'name': ''})
    chart1.set_legend({'none': True})
    chart1.set_size({'width': 300, 'height': 250})
    chart1.set_style(10)
    ws.insert_chart('E'+str(row-numrows-2), chart1)
    row += 2

    if title in ['Others']:
        # today split by owner
        dfgroup = df[['Owner', 'Value', 'Percent']]
        summary_owner = dfgroup.groupby('Owner').agg('sum')
        #print(summary_owner)
        ws.write_row(row, 0, ['Owner', 'Value (L)', 'Percent'], style['bold'])
        row += 1
        owners = summary_owner.index.values
        for x in owners:
            ws.write_row(row, 0, [x])
            ws.write_row(row, 1, [summary_owner.loc[x]['Value']], style['value'])
            ws.write_row(row, 2, [summary_owner.loc[x]['Percent']/100], style['percent'])
            row += 1
        row += 1

        for owner in ['saroj', 'skgoel']:#summary_owner.index:

            row += 1
            ws.write_row(row, 0, ['>>>>>> ' + owner + '\'s INVESTMENT SUMMARY <<<<<<'], style['bold'])
            row += 1
            ws.write_row(row, 0, ['Desc', 'Maturity', 'Value (Lacs)', 'Percent'], style['bold'])
            row += 2

            dfown = df.loc[df['Owner'] == owner]

            cnt = len(dfown)
            ncols = ['Desc', 'Maturity', 'Value']

            dfgroup = dfown[['Category', 'Value']]
            summary_own_cat = dfgroup.groupby('Category').agg('sum')
            summary_own_cat['Percent'] = summary_own_cat['Value'] / summary_own_cat['Value'].sum()
            #print(summary_own_cat)
            for cat in summary_own_cat.index:
                dfown_cat = dfown.loc[dfown['Category'] == cat]
                dfown_cat = dfown_cat.sort_values(by='Maturity', ascending=True, inplace=False)

                cnt = len(dfown_cat)        
                ws.write_row(row, 0, [cat + ' (' + str(cnt) + ')'], style['bold'])
                ws.write_row(row, 2, [summary_own_cat.loc[cat]['Value']], style['value-bold'])
                ws.write_row(row, 3, [summary_own_cat.loc[cat]['Percent']], style['percent-bold'])
                row += 1
        

                for i, x in dfown_cat.iterrows():
                    ws.write_row(row, 0, [x[y] for y in ncols])
                    #ws.write_row(row, len(ncols), [x['Percent']/100], style['percent'])
                    row += 1
                row+= 1
            row += 1

    if mfu:
        row += 4

        dfgroup = df[['Fund', 'Value', 'Percent']]
        summary_fund = dfgroup.groupby('Fund').agg('sum')
        # today split by fund name
        ws.write_row(row, 0, ['Fund', 'Value (L)', 'Percent'], style['bold'])
        row += 1
        numrows = 0
        funds = summary_fund.index.values
        for x in funds:
            ws.write_row(row, 0, [x])
            ws.write_row(row, 1, [summary_fund.loc[x]['Value']], style['value'])
            ws.write_row(row, 2, [summary_fund.loc[x]['Percent']/100], style['percent'])
            row += 1
            numrows += 1

        chart1 = wb.add_chart({'type': 'pie'})
        chart1.add_series({
            'name':       'Fund split',
            'categories': [wsname, row-numrows, 0, row-1, 0],
            'values':     [wsname, row-numrows, 1, row-1, 1],
            'data_labels':{'percentage':True,'category':True,'position':'outside_end'}
        })
        chart1.set_title({'name': ''})
        chart1.set_legend({'none': True})
        chart1.set_size({'width': 300, 'height': 250})
        chart1.set_style(10)
        ws.insert_chart('E'+str(row-numrows-2), chart1)
        row += 2

        dfgroup = df[['Category', 'Value']]
        summary_cat = dfgroup.groupby('Category').agg('sum')
        for cat in summary_cat.index:
            dfcat = df.loc[df['Category'] == cat].copy()
            dfcat['Percent'] = 100 * dfcat['Value'] / dfcat['Value'].sum()
            cnt = len(dfcat)
            ws.write_row(row, 0, [cat + ' (' + str(cnt) + ' funds)'], style['bold'])
            row += 2

            dfgroup = dfcat[['Classification', 'Value']]
            summary_class = dfgroup.groupby('Classification').agg('sum')
            for classif in summary_class.index:
                dfclass = dfcat.loc[df['Classification'] == classif]                
                dfclass = dfclass.sort_values(by='Value', ascending=False, inplace=False)
                cnt = len(dfclass)
                ws.write_row(row, 0, [classif + ' (' + str(cnt) + ' fund)  ' + 
                                      str(int(dfclass['Percent'].sum())) + '%'], style['bold'])
                row += 1

                for i, x in dfclass.iterrows():
                    ws.write_row(row, 0, [x[y] for y in cols])
                    ws.write_row(row, len(cols), [x['Percent']/100], style['percent'])
                    row += 1
                row += 1
            row += 1

def add_ws_crypto(wb, df, o, title, style, now):
    wsname = title
    print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)

    row = 0
    cols = ['Symbol', 'Desc', 'Units', 'Cost', 'NAVINR', 'NAV', 'USD', 'Value', 'ValueYF', 'Owner', 'Held in']
    ws.write_row(row, 0, cols+['Percent'], style['bold'])
    row += 2

    df['Subtype'] = df.apply (lambda row: label_subtype (row),axis=1)
    df['Type'] = df.apply (lambda row: label_type (row),axis=1)

    dfgroup = df[['Subtype', 'Value', 'ValueYF']]
    summary_cat = dfgroup.groupby('Subtype').agg('sum')

    for cat in summary_cat.index:
        dfcat = df.loc[df['Subtype'] == cat]
        dfcat = dfcat.sort_values(by='Value', ascending=False, inplace=False)
        cnt = len(dfcat)

        ws.write_row(row, 0, [cat + ' (' + str(cnt) + ')'], style['bold'])
        row += 1

        for i, x in dfcat.iterrows():
            ws.write_row(row, 0, [x[y] for y in cols])
            ws.write_row(row, len(cols), [x['Percent']/100], style['percent'])
            row += 1
        row += 1

    nowdate = time_str_date_utc(now - o*86400)
    ws.write_row(row, 0, 
                 ['NOTE: Data as of date ' + nowdate + ' (%d days old)' % o], 
                 style['ital'])
    row += 2
    ws.set_column(0, 0, 20)

    ws.write_row(row, 0, ['TOTAL: %4.2f Cr (%d funds)' % 
                          (summary_cat['Value'].sum()/100, len(df))], style['large-red'])

    # today split by symbol
    row += 2
    dfgroup = df[['Symbol', 'Value', 'Cost', 'Units', 'Percent']]
    summary_sym = dfgroup.groupby('Symbol').agg('sum')
    ws.write_row(row, 0, ['Symbol', 'Units', 'Cost', 'Value (L)', 'Allocation', 'Profit', 'Average'], style['bold'])
    row += 1
    numrows = 0
    syms = summary_sym.index.values
    for x in syms:
        cost = summary_sym.loc[x]['Cost']
        val = summary_sym.loc[x]['Value']
        profit = (val - cost)/cost
        units = summary_sym.loc[x]['Units']
        average = cost/units
        ws.write_row(row, 0, [x])
        ws.write_row(row, 1, [units])
        ws.write_row(row, 2, [cost], style['value'])
        ws.write_row(row, 3, [val], style['value'])
        ws.write_row(row, 4, [summary_sym.loc[x]['Percent']/100], style['percent'])
        ws.write_row(row, 5, [profit], style['percent'])
        ws.write_row(row, 6, [average])
        row += 1
        numrows += 1

    chart1 = wb.add_chart({'type': 'pie'})
    chart1.add_series({
        'name':       'Category split',
        'categories': [wsname, row-numrows, 0, row-1, 0],
        'values':     [wsname, row-numrows, 3, row-1, 3],
        'data_labels':{'percentage':True,'category':True,'position':'outside_end'}
    })
    chart1.set_title({'name': ''})
    chart1.set_legend({'none': True})
    chart1.set_size({'width': 300, 'height': 250})
    chart1.set_style(10)
    ws.insert_chart('I'+str(row-numrows-2), chart1)

    # today split by owner
    row += 2
    dfgroup = df[['Owner', 'Value', 'Cost', 'Percent']]
    summary_own = dfgroup.groupby('Owner').agg('sum')
    ws.write_row(row, 0, ['Owner', 'Cost', 'Value (L)', 'Allocation', 'Profit'], style['bold'])
    row += 1
    for x in summary_own.index.values:
        cost = summary_own.loc[x]['Cost']
        val = summary_own.loc[x]['Value']
        profit = (val - cost)/cost
        ws.write_row(row, 0, [x])
        ws.write_row(row, 1, [cost], style['value'])
        ws.write_row(row, 2, [val], style['value'])
        ws.write_row(row, 3, [summary_own.loc[x]['Percent']/100], style['percent'])
        ws.write_row(row, 4, [profit], style['percent'])
        row += 1

    # Add total, spread and profit
    row += 2
    totWX = summary_cat['Value'].sum()
    totYF = summary_cat['ValueYF'].sum()
    spread = (totWX - totYF)/totYF
    ws.write_row(row, 0, ['TOTAL WazirX', totWX])
    row += 1
    ws.write_row(row, 0, ['TOTAL Yahoo Finance', totYF])
    row += 1
    ws.write_row(row, 0, ['Spread', spread], style['percent'])

    print('\tCrypto total: WazirX %.1f, Yahoo %.1f, spread %.1f%%' % (totWX, totYF, spread*100))

    totCost = df['Cost'].sum()
    profit = (totWX-totCost)/totCost
    print('\tCrypto cost: %.1f lacs (Profit %.1f%%)' % (totCost, profit*100))

    row += 2
    ws.write_row(row, 0, ['TOTAL Cost', totCost])
    row += 1
    ws.write_row(row, 0, ['Profit', profit], style['percent'])

def add_ws_summary(wb, style, dfall, dffull, tl,
                   sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary, NUM_DAYS, todate):
    wsname = 'Summary'
    print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0
    
    ws.write_row(row, 0, ['Report generated on ' + todate], style['ital'])
    row += 2
    
    netw = (tl[0]/100) #type_summary['Value'].sum()/100
    print('\nNET WORTH: %4.2f Cr' % netw)
    if NUM_DAYS > 1: print('\tDAY   change: %+6.1f Lacs' % (tl[0] - tl[1]))
    if NUM_DAYS > 7: print('\tWEEK  change: %+6.1f Lacs' % (tl[0] - tl[7]))
    if NUM_DAYS > 30: print('\tMONTH change: %+6.1f Lacs' % (tl[0] - tl[30]))
    if NUM_DAYS > 180: print('\t6-MON change: %+6.1f Lacs' % (tl[0] - tl[180]))
    if NUM_DAYS > 365: print('\tYEAR  change: %+6.1f Lacs' % (tl[0] - tl[365]))

    if NUM_DAYS > 1:
        peak = max(tl[1:])
        peak_index = tl.index(peak)
        trough = min(tl[1:])
        trough_index = tl.index(trough)
        pch = tl[0] - peak
        lch = (tl[0] - trough)
        print('\tPEAK  change: %+6.1f Lacs (%d%% from %d days ago)' % (pch, 100*pch/peak, peak_index))
        print('\tLOW   change: %+6.1f Lacs (%d%% from %d days ago)' % (lch, 100*lch/trough if (trough!=0) else 100,  trough_index))
    print()

    ws.write_row(row, 0, ['NET WORTH: %4.2f Cr' % netw], style['large-red'])
    row += 2

    dfcon = dffull[dffull['Type']=='CONTINGENCY']
    contingency = dfcon['Value'].sum()
    print("PROPERTY: %4.2f Cr (%d%%)" % (contingency/100.0, contingency/netw))
    print("INVESTMENTS: %4.2f Cr\n" % (netw - contingency/100.0))

    dfnoncon = dffull[dffull['Type']!='CONTINGENCY']
    dfnoncon = dfnoncon[['Owner', 'Value']]
    own = dfnoncon.groupby('Owner').agg('sum')
    own['Percent'] = 100 * own['Value'] / own['Value'].sum()
    print(own)
    print()
    
    ws.write_row(row, 0, ["PROPERTY: %4.2f Cr (%d%%)\n" % (contingency/100.0, contingency/netw)], style['bold'])
    row += 1
    ws.write_row(row, 0, ["INVESTMENTS: %4.2f Cr\n" % (netw - contingency/100.0)], style['bold'])
    row += 2

    print("TOTAL INTEREST accrued = %4.1f lacs" % dfall['Interest'].sum())
    dffd = dfall[(dfall['Subtype'] == 'FD') | (dfall['Subtype'] == 'BOND')]
    dffd = dffd.sort_values(by=['Maturity'])
    print("Maturing next:")
    for i in range(len(dffd)):
        if i>1 and dffd['TTM'].iloc[i]>90: break
        print("\t%2d lacs for %14s on %s (%d days)" % (dffd['Value'].iloc[i], dffd['Desc'].iloc[i], 
            dffd['Maturity'].iloc[i], dffd['TTM'].iloc[i]))

    print("\n**** INVESTMENT SPLIT ****\n")
    ws.write_row(row, 0, ['**** INVESTMENT SPLIT ****'], style['bold'])
    row += 2

    # today split by type
    ws.write_row(row, 0, ['Type', 'Value (L)', 'Percent', 'Target', 'Adjustment'], style['bold'])
    row += 1
    numrows = 0
    types = type_summary.index.values
    for x in types:
        av = type_summary.loc[x]['Value']
        ap = type_summary.loc[x]['Percent']
        tp = targetType(x)
        tv = av * tp / ap
        dev = tv - av
        ws.write_row(row, 0, [x])
        ws.write_row(row, 1, [av], style['value'])
        ws.write_row(row, 2, [ap/100], style['percent'])
        ws.write_row(row, 3, [tp/100], style['percent'])
        ws.write_row(row, 4, [dev], style['value'])
        row += 1
        numrows += 1
        print("%6s: %4.1f%%  %4.1f%% (%4d lacs)" % (x, tp, ap, dev))
    print("")

    chart1 = wb.add_chart({'type': 'pie'})
    chart1.add_series({
        'name':       'Asset allocation',
        'categories': [wsname, row-numrows, 0, row-1, 0],
        'values':     [wsname, row-numrows, 1, row-1, 1],
        'data_labels':{'percentage':True,'category':True,'position':'outside_end'}
    })
    chart1.set_title({'name': 'Asset Allocation'})
    chart1.set_legend({'none': True})
    chart1.set_size({'width': 300, 'height': 300})
    chart1.set_style(10)
    ws.insert_chart('G2', chart1)
    
    # today split by owner
    row += 2
    ws.write_row(row, 0, ['Owner', 'Value (L)', 'Percent'], style['bold'])
    row += 1
    types = own_summary.index.values
    for x in types:
        ws.write_row(row, 0, [x])
        ws.write_row(row, 1, [own_summary.loc[x]['Value']], style['value'])
        ws.write_row(row, 2, [own_summary.loc[x]['Percent']/100], style['percent'])
        row += 1

    # today split by source
    row += 2
    ws.write_row(row, 0, ['Source', 'Value (L)', 'Percent'], style['bold'])
    row += 1
    types = ave_summary.index.values
    for x in types:
        ws.write_row(row, 0, [x])
        ws.write_row(row, 1, [ave_summary.loc[x]['Value']], style['value'])
        ws.write_row(row, 2, [ave_summary.loc[x]['Percent']/100], style['percent'])
        row += 1

    # today split by subtype
    row += 3
    ws.write_row(row, 0, ['Type', 'Subtype', 'Value (L)', 'Percent', 'Target', 'Adjustment'], style['bold'])
    row += 1
    for x in sub_summary.index.values:
        ws.write_row(row, 0, list(x))
        v = sub_summary.loc[x]['Value']
        ws.write_row(row, 2, [v], style['value'])
        a = sub_summary.loc[x]['Percent']
        ws.write_row(row, 3, [a/100], style['percent'])
        typ = x[0]
        subtype = x[1]
        t = target[subtype]
        ws.write_row(row, 4, [t/100], style['percent'])
        tv = v * t / a
        dev = tv - v
        print("%7s %7s %5.1f%% %5.1f%% (%4d lacs)" % (typ, subtype, t, a, dev))
        ws.write_row(row, 5, [dev], style['value'])
        row += 1
    print("")

    # today split by category
    row += 3
    ws.write_row(row, 0, ['Type', 'Subtype', 'Category', 'Value (L)', 'Percent'], style['bold'])
    row += 1
    for x in cat_summary.index.values:
        ws.write_row(row, 0, list(x))
        ws.write_row(row, 3, [cat_summary.loc[x]['Value']], style['value'])
        ws.write_row(row, 4, [cat_summary.loc[x]['Percent']/100], style['percent'])
        row += 1

    # today split by subtype - all items
    row += 2
    ws.write_row(row, 0, ['*'*80])
    row += 2
    cols = ['Type', 'Subtype', 'Desc', 'Value']
    ws.write_row(row, 0, cols + ['Percent'], style['bold'])
    row += 2

    # contingency details
    dfcon = dfcon.sort_values(by='Value', ascending=False, inplace=False)
    cnt = len(dfcon)
    ws.write_row(row, 0, ['CONTINGENCY' + ' (' + str(cnt) + ')  '], style['bold'])
    row += 1
    for i, x in dfcon.iterrows():
        ws.write_row(row, 0, [x[y] for y in cols])
        #ws.write_row(row, len(cols), [x['Percent']/100], style['percent'])
        row += 1
    row += 1

    # list all assets
    dfall['Percent'] = 100 * dfall['Value'] / dfall['Value'].sum()
    for tsub in sub_summary.index:
        sub = tsub[1]
        dfsub = dfall.loc[dfall['Subtype'] == sub]
        dfsub = dfsub.sort_values(by='Value', ascending=False, inplace=False)
        cnt = len(dfsub)

        ws.write_row(row, 0, [sub + ' (' + str(cnt) + ')  ' + str(round(sub_summary.loc[tsub]['Percent'], 1)) + '%'], style['bold'])
        row += 1

        for i, x in dfsub.iterrows():
            ws.write_row(row, 0, [x[y] for y in cols])
            ws.write_row(row, len(cols), [x['Percent']/100], style['percent'])
            row += 1
        row += 1
    row += 1

    # list FD/Bond ladder
    dftm = dfall.loc[(dfall['Subtype'] == 'TM')].copy()
 
    dftm['Rate'] = 7.5
    for i,x in dftm.iterrows():
        lwords = x['Desc'].split()
        year = '' 
        month = ''
        for word in lwords:
            if word.startswith('20') and len(word) == 4:
                year = word
                break
            else:
                month = word

        if year == '' or month == '':
            print('ERROR: Failed to extract month, year from %s' % x['Desc']);
        monthi = datetime.datetime.strptime(month, '%b').month
        yeari = int(year)
        #print(month, year, '=>', monthi, yeari)
        dftm.at[i, 'Maturity'] = datetime.datetime(yeari,monthi,1)

    dffixed = dfall.loc[(dfall['Subtype'] == 'FD') | (dfall['Subtype'] == 'BOND')].copy()
    dffixed = pd.concat([dffixed,dftm])
    #print(dffixed[['Desc', 'Maturity']])
    dffixed['Year'] = dffixed['Maturity'].dt.strftime('%Y')
    dffixed['Maturity'] = dffixed['Maturity'].dt.strftime('%Y-%m')
    dffixed = dffixed.infer_objects(copy=False).fillna('')
    cols = ['Category', 'Rate', 'Desc', 'Value', 'Maturity']

    ws.write_row(row, 0, ['*'*10 + '  FIXED INCOME LADDER  ' + '*'*10])
    row += 2
    ws.write_row(row, 0, cols, style['bold'])
    row += 1

    dffixed = dffixed.sort_values(by='Maturity')
    for i, x in dffixed.iterrows():
        ws.write_row(row, 0, [x[y] for y in cols])
        row += 1
    row += 1

    dffixed = dffixed[['Year', 'Value']]
    #print(dffixed)
    dfyear = dffixed.groupby('Year'). agg('sum')
    dfyear = dfyear.sort_values(by='Year')
    for i, x in dfyear.iterrows():
        ws.write_row(row, 0, [i, int(x['Value'])])
        row += 1

    ws.set_column(2, 2, 25)


def add_ws_trend(wb, style, stats_daily_typ, stats_daily_cat, NUM_DAYS):
    wsname = 'Trends'
    print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)

    cols = []
    for col in stats_daily_typ.columns:
        if col != 'Date': cols.append(col)

    row = 27
    ws.write_row(row, 0, ['Date'] + cols, style['bold'])
    row += 1

    colno = 1
    ws.write_column(row, 0, stats_daily_typ['Date'])
    for col in cols:
        ws.write_column(row, colno, stats_daily_typ[col])
        colno += 1        
    numrows = len(stats_daily_typ)
    row += numrows

    chart2 = wb.add_chart({'type': 'line'})
    i = 1
    for col in cols:
        chart2.add_series({
            'name':       col,
            'categories': [wsname, row-numrows, 0, row-1, 0],
            'values':     [wsname, row-numrows, i, row-1, i],
        })
        i += 1
    chart2.set_title({'name': 'Daily Trend'})
    chart2.set_size({'width': 1000, 'height': 500})
    ws.insert_chart('A1', chart2)

    # daily trend category
    cols = []
    for col in stats_daily_cat.columns:
        if col != 'Date': cols.append(col)

    row += 3
    ws.write_row(row, 0, ['Date'] + cols, style['bold'])
    row += 1

    colno = 1
    ws.write_column(row, 0, stats_daily_cat['Date'])
    for col in cols:
        ws.write_column(row, colno, stats_daily_cat[col])
        colno += 1        
    row += len(stats_daily_cat)
    ws.set_column(0, 0, 12)

    sdc = stats_daily_cat.head(2)
    sdc = sdc.drop('Date', axis=1)
    #print(sdc)
    delta = sdc.iloc[0] -  sdc.iloc[1]
    delta = delta.to_dict()
    #print(delta)
    delta.pop('Total')
    delta = sorted(delta.items(), key=lambda item: item[1])
    print('**** TOP LOSERS')
    for i in range(7):
        if abs(delta[i][1]) > 0.01: 
            print('%14s : %6.2f lacs' % delta[i])
        else:
            break
    print('**** TOP GAINERS')
    for i in range(7):
        if delta[-i-1][1] > 0.01: 
            print('%14s : %6.2f lacs' % delta[-i-1])
        else:
            break
    print('----------------------------')


def add_ws_trend_weekly(wb, style, stats_daily_typ, stats_daily_cat, NUM_WEEKS):
    wsname = 'Weekly Trends'
    print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)

    stats_daily_cat.fillna(0, inplace=True)
    stats_daily_typ.fillna(0, inplace=True)

    cols = []
    for col in stats_daily_typ.columns:
        if col != 'Date': cols.append(col)

    row = 27
    ws.write_row(row, 0, ['Date'] + cols, style['bold'])
    row += 1

    colno = 1
    ws.write_column(row, 0, stats_daily_typ['Date'])
    for col in cols:
        ws.write_column(row, colno, stats_daily_typ[col])
        colno += 1        
    numrows = len(stats_daily_typ)
    row += numrows

    chart2 = wb.add_chart({'type': 'line'})
    i = 1
    for col in cols:
        chart2.add_series({
            'name':       col,
            'categories': [wsname, row-numrows, 0, row-1, 0],
            'values':     [wsname, row-numrows, i, row-1, i],
        })
        i += 1
    chart2.set_title({'name': 'Weekly Trend'})
    chart2.set_size({'width': 1000, 'height': 500})
    ws.insert_chart('A1', chart2)

    # daily trend category
    cols = []
    for col in stats_daily_cat.columns:
        if col != 'Date': cols.append(col)

    row += 3
    ws.write_row(row, 0, ['Date'] + cols, style['bold'])
    row += 1

    colno = 1
    ws.write_column(row, 0, stats_daily_cat['Date'])
    for col in cols:
        ws.write_column(row, colno, stats_daily_cat[col])
        colno += 1        
    row += len(stats_daily_cat)
    ws.set_column(0, 0, 12)

        
def add_ws_trans(wb, style, df_daily, dfg_daily, NUM_DAYS, now):
    wsname = 'Transactions'
    print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0
    
    changes = changelog(df_daily, NUM_DAYS, now)
    ws.write_row(row, 0, ["Mutual Fund transactions (last %d days)" % NUM_DAYS], style['bold'])
    row += 2
    ws.write_row(row, 0, changes.columns, style['bold'])
    row += 1
    for i,x in changes.iterrows():
        ws.write_row(row, 0, x.values)
        row += 1        
    row += 2

    changes = changelog(dfg_daily, NUM_DAYS, now)
    ws.write_row(row, 0, ["Geojit transactions"], style['bold'])
    row += 2
    ws.write_row(row, 0, changes.columns, style['bold'])
    row += 1
    for i,x in changes.iterrows():
        ws.write_row(row, 0, x.values)
        row += 1        
    row += 2
    ws.set_column(0, 1, 15)
    ws.set_column(2, 5, 12)
    
def generate_report(tl, df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfall, dffull,
                    sub_summary, cat_summary, type_summary, 
                    ave_summary, dir_summary, own_summary,
                    stats_daily_typ, stats_daily_cat, now, NUM_DAYS,
                    stats_weekly_typ, stats_weekly_cat, NUM_WEEKS, owner):
    todate = time_str_date_utc(now)
    if owner != '':
        fname = 'REPORTS/report-'  + todate + '-' + owner + '.xlsx'
    else:
        fname = 'REPORTS/report-'  + todate + '.xlsx'
    wb = xlsxwriter.Workbook(fname)

    style = {}
    style['bold'] = wb.add_format({'bold': True})
    style['ital'] = wb.add_format({'italic': True})
    style['large-red'] = wb.add_format({'bold': True, 'font_color': 'red', 'font_size':15})

    style['percent'] = wb.add_format()
    style['percent'].set_num_format('0.0%') 
    style['percent-bold'] = wb.add_format({'bold': True})
    style['percent-bold'].set_num_format('0.0%') 

    style['value'] = wb.add_format()
    style['value'].set_num_format('0.0') 
    style['value2'] = wb.add_format()
    style['value2'].set_num_format('0.00') 
    style['value-bold'] = wb.add_format({'bold': True})
    style['value-bold'].set_num_format('0.0') 

    add_ws_summary(wb, style, dfall, dffull, tl,
                   sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary,
                   NUM_DAYS, todate)
    add_ws_trend(wb, style, stats_daily_typ, stats_daily_cat, NUM_DAYS)
    if NUM_WEEKS > 1: add_ws_trend_weekly(wb, style, stats_weekly_typ, stats_weekly_cat, NUM_WEEKS)
    #add_ws_trans(wb, style, df_daily, dfg_daily, NUM_DAYS, now)
    
    df, o = get_recent_df(df_daily, NUM_DAYS)
    dfg, og = get_recent_df(dfg_daily, NUM_DAYS)
    dfz, oz = get_recent_df(dfz_daily, NUM_DAYS)
    dfa, oa = get_recent_df(dfa_daily, NUM_DAYS)
    dfc, oc = get_recent_df(dfc_daily, NUM_DAYS)
    dfb, ob = get_recent_df(dfb_daily, NUM_DAYS)
    dfcm, ocm = get_recent_df(dfcm_daily, NUM_DAYS)

    add_ws(wb, df, o, 'MFU', style, now)
    add_ws(wb, dfg, og, 'Geojit', style, now)
    add_ws(wb, dfz, oz, 'Zerodha', style, now)
    add_ws(wb, dfa, oa, 'Others', style, now)
    add_ws_crypto(wb, dfc, oc, 'Crypto', style, now)
    #add_ws(wb, dfb, ob, 'IDFC', style, now)
    add_ws(wb, dfcm, ocm, 'Capitalmind', style, now)
    
    wb.close()
    print("Writing workbook to:", fname)
    
