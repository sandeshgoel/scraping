import argparse
import sys
from analyze_util import *
import configparser

def generate_summary(tl, dfall, dffull, sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary, now, owner):
    todate = time_str_date_utc(now)
    if owner != '':
        fname = 'SUMMARY/summary-' + todate + '-' + owner + '.xlsx'
    else:
        fname = 'SUMMARY/summary-' + todate + '.xlsx'
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
    style['value-bold'] = wb.add_format({'bold': True})
    style['value-bold'].set_num_format('0.0') 

    add_ws_summary(wb, style, dfall, dffull, tl,
                   sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary,
                   NUM_DAYS, todate)
    wb.close()
    print("Writing workbook to:", fname)

def get_target_allocation(type_summary, sub_summary, add_funds):
    print('\nTarget allocation after adding %d lacs\n' % add_funds)

    cur_total = type_summary['Value'].sum()
    new_total = cur_total + add_funds
    for x in type_summary.index.values:
        av = type_summary.loc[x]['Value']
        ap = type_summary.loc[x]['Percent']
        tp = targetType(x)
        tv = tp * new_total / 100
        dev = tv - av
        print("%6s: %4.1f%%  %4.1f%% (%4d lacs)" % (x, ap, tp, dev))
    print("")

    cur_total = sub_summary['Value'].sum()
    new_total = cur_total + add_funds
    for x in sub_summary.index.values:
        v = sub_summary.loc[x]['Value']
        a = sub_summary.loc[x]['Percent']
        typ = x[0]
        subtype = x[1]
        t = target[subtype]
        tv = t * new_total / 100
        dev = tv - v
        print("%7s %7s %5.1f%% %5.1f%% (%4d lacs)" % (typ, subtype, t, a, dev))

# ---------------------------------------------------------------------------

NUM_DAYS = 1
now = time.time()
todate = time_str_date_utc(now)

args = argparse.ArgumentParser(description='Generate report')
args.add_argument('-o', '--owner', help='owner', type=str, default='')
args.add_argument('-a', '--add', help='funds to add', type=int, default=0)
args = args.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())
data = config['data']
#basemfu = data['basemfu']
basemfparse = data['basemfparse']
basezerodha = data['basezerodha']
basecapitalmind = data['basecapitalmind']
basegeojit = data['basegeojit']
basebankhdfc = data['basebankhdfc']
basebankidfc = data['basebankidfc']
baseothers = data['baseothers']
basecrypto = data['basecrypto']
basevested = data['basevested']

dfc = get_classifier_df()
dfic = get_isin_classifier_df()

#filef = get_latest_file(basemfu)
filef = get_latest_file(basemfparse)
fileg = get_latest_file(basegeojit, ext='')
filez = get_latest_file(basezerodha)
filea = get_latest_file(baseothers)
filec = get_latest_file(basecrypto)
fileb = get_latest_file(basebankidfc)
filecm = get_latest_file(basecapitalmind)
filev = get_latest_file(basevested)

dff = file2df_mfparse(filef)
dff = pd.merge(dff, dfic, how='left', on='ISIN')
#dff = file2df_funds(filef)
#dff = pd.merge(dff, dfc, how='left', on='Code')
dff.fillna('unknown', inplace=True)
dff['Category'] = np.where(dff['Classification'] == 'unknown', dff['Category'], dff['Classification'])
#print(dff[['Fund', 'Category', 'Classification']])

dfg = file2df_geojit(fileg, basegeojit)
dfz = file2df_zerodha(filez, basezerodha)
dfa = file2df_assets(filea, baseothers)
dfc = file2df_crypto(filec, basecrypto)
dfb = file2df_idfc(fileb, basebankidfc)
dfcm = file2df_cm(filecm, basecapitalmind)
dfv = file2df_vested(filev, basevested)

df = dff.copy()
df = pd.concat([df, dfg, dfz, dfa, dfc, dfb, dfcm, dfv])

dfgroup = df[['Owner', 'Value']]
own = dfgroup.groupby('Owner').agg('sum')
own['Percent'] = 100 * own['Value'] / own['Value'].sum()
print(own)
print()

print("Generating summary")    
sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary, dfall, dffull = get_summary_from_combined(df, args.owner)

generate_summary([dffull['Value'].sum()], dfall, dffull, sub_summary, cat_summary, type_summary, ave_summary, dir_summary, own_summary, now, args.owner)

if (args.add > 0):
    get_target_allocation(type_summary, sub_summary, args.add)

print("")