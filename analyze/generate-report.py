import argparse
import sys
from analyze_util import *

RET_CODE = 0
NUM_DAYS = 730
now = time.time()

args = argparse.ArgumentParser(description='Generate report')
args.add_argument('-o', '--owner', help='owner', type=str, default='')
args.add_argument('--num_days', '-n', help='position id to start from', type=int, default=NUM_DAYS)
args = args.parse_args()

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())
data = config['data']
basemfparse = data['basemfparse']
basemfu = data['basemfu']
basezerodha = data['basezerodha']
basecapitalmind = data['basecapitalmind']
basegeojit = data['basegeojit']
basebankhdfc = data['basebankhdfc']
basebankidfc = data['basebankidfc']
basebankaxis = data['basebankaxis']
baseothers = data['baseothers']
basecrypto = data['basecrypto']
basevested = data['basevested']

sources = ['AXIS', 'HDFC', 'MF', 'GEOJIT', 'ZERODHA', 'OTHER', 'CRYPTO', 'IDFC', 'CM', 'VESTED']
oldest = {}
recent = {}

for offset in range(args.num_days):
    df_hdfc = get_hdfc_df(now, offset, basebankhdfc)
    if not df_hdfc.empty: 
        recent['HDFC'] = offset
        for i, row in df_hdfc.iterrows():
            if (row['Amount'] < 7000) or \
                (not str(row['Account']).startswith('5010014') and row['Amount'] < 26000) or \
                (not str(row['Account']).startswith('550000') and row['Amount'] > 32000):
                print('\n** HDFC Acccount %s (%s) needs action, balance - %d\n' % (row['Account'], row['Name'], row['Amount']))
                RET_CODE = 1
        if offset > 8:
            print("\n** HDFC Bank summary is TOO old (%d days) **\n" % offset)
            RET_CODE = 1
        break

for offset in range(args.num_days):
    df_axis = get_axis_df(now, offset, basebankaxis)
    if not df_axis.empty: 
        recent['AXIS'] = offset
        for i, row in df_axis.iterrows():
            if (row['Amount'] < 25000 or row['Amount'] > 32000):
                print('\n** AXIS Acccount %s (%s) needs action, balance - %d\n' % (row['Account'], row['Name'], row['Amount']))
                RET_CODE = 1
        if offset > 8:
            print("\n** AXIS Bank summary is TOO old (%d days) **\n" % offset)
            RET_CODE = 1
        break

dfc = get_classifier_df()
dfic = get_isin_classifier_df()

print("Generating data frames for %d days" % args.num_days)

found = False
oldest['MF'] = 0
df_daily = {}
for offset in range(args.num_days):
    df_daily[offset] = get_funds_df(now, offset, basemfu, dfc, basemfparse, dfic)
    if df_daily[offset].empty: continue
    oldest['MF'] = offset
    if not found: 
        recent['MF'] = offset
        found = True

#print('Done getting MFU files')

found = False
oldest['GEOJIT'] = 0
dfg_daily = {}
for offset in range(args.num_days):
    dfg_daily[offset] = get_geojit_df(now, offset, basegeojit)
    if not dfg_daily[offset].empty: 
        oldest['GEOJIT'] = offset
        if not found: 
            recent['GEOJIT'] = offset
            found = True

#print('Done getting GEOJIT files')

found = False
oldest['ZERODHA'] = 0
dfz_daily = {}
for offset in range(args.num_days):
    dfz_daily[offset] = get_zerodha_df(now, offset, basezerodha)
    if not dfz_daily[offset].empty: 
        oldest['ZERODHA'] = offset
        if not found: 
            recent['ZERODHA'] = offset
            found = True

#print('Done getting ZERODHA files')
    
found = False
oldest['OTHER'] = 0 
dfa_daily = {}
for offset in range(args.num_days):
    dfa_daily[offset] = get_assets_df(now, offset, baseothers)
    if not dfa_daily[offset].empty: 
        oldest['OTHER'] = offset
        if not found: 
            recent['OTHER'] = offset
            found = True

#print('Done getting OTHER ASSET files')
    
found = False
oldest['CRYPTO'] = 0 
dfc_daily = {}
for offset in range(args.num_days):
    dfc_daily[offset] = get_crypto_df(now, offset, basecrypto)
    if not dfc_daily[offset].empty: 
        oldest['CRYPTO'] = offset
        if not found: 
            recent['CRYPTO'] = offset
            found = True

#print('Done getting CRYPTO files')

found = False
oldest['VESTED'] = 0 
dfv_daily = {}
for offset in range(args.num_days):
    dfv_daily[offset] = get_vested_df(now, offset, basevested)
    if not dfv_daily[offset].empty: 
        oldest['VESTED'] = offset
        if not found: 
            recent['VESTED'] = offset
            found = True

#print('Done getting VESTED files')

found = False
oldest['IDFC'] = 0 
dfb_daily = {}
for offset in range(args.num_days):
    dfb_daily[offset] = get_idfc_df(now, offset, basebankidfc)
    if not dfb_daily[offset].empty: 
        oldest['IDFC'] = offset
        if not found: 
            recent['IDFC'] = offset
            found = True
recent['IDFC'] = 0 # ignore IDFC staleness
#print('Done getting IDFC files')

found = False
oldest['CM'] = 0 
dfcm_daily = {}
for offset in range(args.num_days):
    dfcm_daily[offset] = get_cm_df(now, offset, basecapitalmind)
    if not dfcm_daily[offset].empty: 
        oldest['CM'] = offset
        if not found: 
            recent['CM'] = offset
            found = True

#print('Done getting CM files')

out = '\nOLDEST: '
for src in sources:
    if (oldest.get(src, 0) > 0):
        out += '%s %d, ' % (src, oldest.get(src, 0))
print(out)

out = 'STALE: '
missing = 'MISSING: '
for src in sources:
    if (recent.get(src, 0) > 0):
        out += '%s %d, ' % (src, recent.get(src, 0))
    if recent.get(src, -1) == -1:
        missing += '%s, ' % src
print(out)
#print(missing)
print('')

stale = any([x>14 for x in recent.values()])
if stale: 
    print("**** ACTION NEEDED To UPDATE STALE DATA ****\n")
    RET_CODE = 1

print("Generating summary")    
sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary, dfall, dffull = get_summary(df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfv_daily, args.num_days, args.owner)

print("Generating daily stats")
stats_daily_typ, stats_daily_cat, stats_weekly_typ, stats_weekly_cat, tl = get_daily_stats(df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfv_daily, args.num_days, now, args.owner)

generate_report(tl, df_daily, dfg_daily, dfz_daily, dfa_daily, dfc_daily, dfb_daily, dfcm_daily, dfall, dffull,
                sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary,
                stats_daily_typ, stats_daily_cat, now, args.num_days,
                stats_weekly_typ, stats_weekly_cat, args.num_days/7, args.owner)

