import casparser
import pprint
import json
import argparse
import datetime
import os 
import time 
import operator
import requests

# -----------------------------------------------------------------------------

def get_default_owner():
    config = configparser.ConfigParser()
    config.read('config.ini')
    data = config['users']
    owners = [x.strip() for x in data['owners'].split(',')]
    #print(owners)
    return owners[0]

def url_get(s, url, verbose):
    if verbose: print("\nGETTING ...", url)
    r = s.get(url)#, verify=False)
    #print("STATUS =", r.status_code)
    if r.status_code != 200:
        print("Request failed")
        sys.exit(1)
    return r

def get_approx_date(date_str, dates):
    if date_str in dates: return date_str
    found = False
    date_approx = date_str
    find_range = 3
    date = datetime.datetime.strptime(date_str, "%d-%m-%Y")
    for i in range(find_range):
        date_approx = datetime.datetime.strftime(date - datetime.timedelta(days=i+1), '%d-%m-%Y')
        if date_approx in dates: 
            found = True
            break
        date_approx = datetime.datetime.strftime(date + datetime.timedelta(days=i+1), '%d-%m-%Y')
        if date_approx in dates: 
            found = True
            break
    if found:
        #print('Date %s data used (closest to %s)' % (date_approx, date_str))
        return date_approx
    
    print('*** WARNING **** No data within %d days of %s' % (find_range*2+1, date_str))
    return date_str

def get_date_diff(d1_str, d2_str):
    d1 = datetime.datetime.strptime(d1_str, "%d-%m-%Y")
    d2 = datetime.datetime.strptime(d2_str, "%d-%m-%Y")
    return (d1-d2).days

def get_nav_history(amfi, verbose):
    url = "https://api.mfapi.in/mf/" + amfi

    # initialize session
    s = requests.session()
    r = url_get(s, url, verbose)

    data = json.loads(r.content)
    #print(data.keys())
    #print(data['meta'])
    navlist = data['data']

    today = datetime.datetime.now()

    lastday_str = navlist[0]['date']
    lastday = datetime.datetime.strptime(lastday_str, '%d-%m-%Y')
    inactive = (today - lastday).days
    if (inactive > 6): print('*** WARNING *** Most recent data is too old %s (AMFI %s)' % (lastday_str, amfi))
    
    firstday_str = navlist[-1]['date']
    firstday = datetime.datetime.strptime(firstday_str, '%d-%m-%Y')
    age = (today - firstday).days

    back_12 = lastday - datetime.timedelta(days=365)
    back_6 = lastday - datetime.timedelta(days=180)
    back_3 = lastday - datetime.timedelta(days=90)
    back_1 = lastday - datetime.timedelta(days=30)

    back_12_str = datetime.datetime.strftime(back_12, '%d-%m-%Y')
    back_6_str = datetime.datetime.strftime(back_6, '%d-%m-%Y')
    back_3_str = datetime.datetime.strftime(back_3, '%d-%m-%Y')
    back_1_str = datetime.datetime.strftime(back_1, '%d-%m-%Y')

    #print("Last %s, 12mo back %s, 6mo back %s, 3mo back %s, 1mo back %s" % 
    #    (lastday_str, back_12_str, back_6_str, back_3_str, back_1_str))

    dates = [nav['date'] for nav in navlist]
    nav_on_date = {}
    for nav in navlist:
        nav_on_date[nav['date']] = nav['nav']

    nav_last = float(nav_on_date[lastday_str])

    back_12_str = get_approx_date(back_12_str, dates)
    if back_12_str not in dates: 
        nav_12 = 0
        xirr_12 = 0 
    else:
        days = get_date_diff(lastday_str, back_12_str)
        nav_12 = float(nav_on_date[back_12_str])
        xirr_12 = 100*(nav_last-nav_12)*365/(nav_12*days) if nav_12!=0 else 0

    back_6_str = get_approx_date(back_6_str, dates)
    if back_6_str not in dates: 
        nav_6 = 0
        xirr_6 = 0 
    else:
        days = get_date_diff(lastday_str, back_6_str)
        nav_6 = float(nav_on_date[back_6_str])
        xirr_6 = 100*(nav_last-nav_6)*365/(nav_6*days) if nav_6!=0 else 0

    back_3_str = get_approx_date(back_3_str, dates)
    if back_3_str not in dates: 
        nav_3 = 0
        xirr_3 = 0 
    else:
        days = get_date_diff(lastday_str, back_3_str)
        nav_3 = float(nav_on_date[back_3_str])
        xirr_3 = 100*(nav_last-nav_3)*365/(nav_3*days) if nav_3!=0 else 0

    back_1_str = get_approx_date(back_1_str, dates)
    if back_1_str not in dates: 
        nav_1 = 0
        xirr_1 = 0 
    else:
        days = get_date_diff(lastday_str, back_1_str)
        nav_1 = float(nav_on_date[back_1_str])
        xirr_1 = 100*(nav_last-nav_1)*365/(nav_1*days) if nav_1!=0 else 0


    return {'nav_1': nav_1,'nav_3': nav_3, 'nav_6': nav_6, 'nav_12': nav_12, 'nav_last': nav_last, 'lastday': lastday_str,
            'xirr_1': xirr_1,'xirr_3': xirr_3, 'xirr_6': xirr_6, 'xirr_12': xirr_12, 'inactive': inactive, 'age':age}


def get_nav_history_cache(amfi, force, verbose):
    age_too_old = 20
    age = age_too_old
    fname = 'scheme_cache/'+amfi+'.json'
    if os.path.isfile(fname):
        age = (time.time() - os.path.getmtime(fname))/(60*60)
        if verbose: 
            print("File %s exists (age %d hours)" % (fname, age))
    if (age < age_too_old) and not force:
        with open(fname, 'r') as file:
            res = json.load(file)
    else:
        res = get_nav_history(amfi, verbose)
        if verbose: 
            print("Saving scheme data to file %s ..." % fname)
        with open(fname, "w") as outfile:
            json.dump(res, outfile)
    return res

# ------------ EXCEL FUNCTIONS ------------------------------------------------

import xlsxwriter

def change_pdf_to_xlsx(fname):
    parts = fname.split('.')
    if parts[-1] != 'pdf': 
        print("File not pdf: %s" % fname)
        sys.exit(1)
    parts[-1] = 'xlsx'
    return '.'.join(parts)

def convert_to_str(sl):
    o = ''
    for s in sl:
        o += "(%s, %s, %s, %s) " % (s[0], s[1], s[2], s[3])
    return o

def convert_to_str_cg(cl):
    o = ''
    for c in cl:
        o += "(%d, %.1f) " % (c[0], c[1])
    return o

def add_ws_folio(wb, style, folio, verbose):
    wsname = folio['amc'].split(' ')[0] + '-' + folio['folio'].split('/')[0]
    if verbose:
        print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0

    for scheme in folio['schemes']:
        #print("****", scheme)    
        ws.write_row(row, 0, [scheme['scheme']], style['bold'])
        row += 2
        ws.write_row(row, 0, list(scheme['transactions'][0].keys()), style['bold'])
        row += 1
        for trans in scheme['transactions']:
            #print("--------", trans)
            #trans['date'] = trans['date'].strftime('%Y-%m-%d')
            trans['sold'] = convert_to_str(trans.get('sold', []))
            trans['bought'] = convert_to_str(trans.get('bought', []))
            ws.write_row(row, 0, list(trans.values()))
            row += 1
        row += 2
    ws.set_column(0, 0, 12)
    ws.set_column(1, 1, 25)
    ws.set_column(2, 5, 12)

def add_ws_summary(wb, style, folio_list):
    wsname = 'Summary'
    if args.verbose: print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0
    ws.write_row(row, 0, ['Scheme', 'Advisor', 'Type', 
        'Cur units', 'NAV', 'Value (lacs)', 
        'Last Date', 'Last NAV', 'Last Value (lacs)',
        'Age of oldest unsold', 'Age of newest unsold', 'no LT', 'Accrued (lacs)', 
        'AMFI', 'ISIN', 'XIRR_1', 'XIRR_3', 'XIRR_6', 'XIRR_12' ], style['bold'])
    row += 2

    tot_value = 0
    last_tot_value = 0
    tot_acc = 0
    for folio in folio_list:
        ws.write_row(row, 0, [folio['amc'] + ' : ' + folio['folio']], style['bold'])
        row += 1
        for scheme in folio['schemes']:
            tot_value += scheme['val']
            last_tot_value += scheme['last_val']
            tot_acc += scheme['accrued']
            ws.write_row(row, 0, [scheme['scheme'], scheme['advisor'], scheme['type'], 
                int(scheme['close']), scheme['nav'], round(scheme['val'], 1), 
                scheme['lastdate'], scheme['lastnav'], round(scheme['last_val'], 1),
                round(scheme['age'], 1), round(scheme['newest'], 1), scheme['noLT'], 
                round(scheme['accrued']/100000, 1), 
                scheme['amfi'], scheme['isin'], scheme['xirr_1'], scheme['xirr_3'], scheme['xirr_6'], scheme['xirr_12']])
            row += 1
        row += 1
    row += 1

    ws.write_row(row, 0, ['TOTAL', '', '', '', '', int(tot_value), '', '', int(last_tot_value), '', round(tot_acc/100000, 1)], style['bold'])
    row += 1
    print('$$$$ Total Value = %d lacs' % tot_value)
    ws.set_column(0, 0, 50)

def add_ws_equity(wb, style, folio_list):
    wsname = 'Equity'
    if args.verbose: print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0
    ws.write_row(row, 0, ['Scheme', 
        'Cur value (lacs)', 
        'Age of oldest unsold', 'Age of newest unsold',  'Accrued (lacs)', 
        'AMFI', 'ISIN', 'XIRR_1', 'XIRR_3', 'XIRR_6', 'XIRR_12' ], style['bold'])
    row += 2

    tot_value = 0
    tot_acc = 0
    scheme_list = []
    for folio in folio_list:
        for scheme in folio['schemes']:
            if scheme['type'] == 'Equity':
                scheme_list.append(scheme)
    scheme_list = sorted(scheme_list, key=operator.itemgetter('newest'))

    for scheme in scheme_list:
        tot_value += scheme['last_val']
        tot_acc += scheme['accrued']
        ws.write_row(row, 0, [scheme['scheme'], round(scheme['last_val'],1), 
            round(scheme['age'], 1), round(scheme['newest'], 1),  
            round(scheme['accrued']/100000, 1), 
            scheme['amfi'], scheme['isin'], scheme['xirr_1'], scheme['xirr_3'], scheme['xirr_6'], scheme['xirr_12']])
        row += 1
    row += 1

    ws.write_row(row, 0, ['TOTAL', int(tot_value), '', '', round(tot_acc/100000, 1)], style['bold'])
    row += 3


    scheme_list = sorted(scheme_list, key=operator.itemgetter('last_val'), reverse=True)

    for scheme in scheme_list:
        tot_value += scheme['last_val']
        tot_acc += scheme['accrued']
        ws.write_row(row, 0, [scheme['scheme'], round(scheme['last_val'],1), 
            round(scheme['age'], 1), round(scheme['newest'], 1), 
            round(scheme['accrued']/100000, 1), 
            scheme['amfi'], scheme['isin'], scheme['xirr_3'], scheme['xirr_6'], scheme['xirr_12']])
        row += 1
    row += 1

    ws.set_column(0, 0, 50)

def add_ws_debt(wb, style, folio_list):
    wsname = 'Debt'
    if args.verbose: print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0
    ws.write_row(row, 0, ['Scheme',  'Cur value (lacs)', 
        'Age of oldest unsold', 'Age of newest unsold', 'no LT', 'Accrued (lacs)', 
        'AMFI', 'ISIN', 'XIRR_1', 'XIRR_3', 'XIRR_6', 'XIRR_12' ], style['bold'])
    row += 2

    tot_value = 0
    tot_acc = 0
    scheme_list = []
    for folio in folio_list:
        for scheme in folio['schemes']:
            if scheme['type'] == 'Debt':
                scheme_list.append(scheme)
    scheme_list = sorted(scheme_list, key=operator.itemgetter('newest'))

    ws.write_row(row, 0, ['No LTCG ever'], style['bold'])
    row += 1
    section = 1
    for scheme in scheme_list:
        if (section == 1) and (scheme['newest_date'] < '2023-04-01'):
            row += 1
            ws.write_row(row, 0, ['No LTCG yet'], style['bold'])
            row += 1
            section = 2

        if (section == 2) and (scheme['newest'] >= 3):
            row += 1
            ws.write_row(row, 0, ['LTCG applicable'], style['bold'])
            row += 1
            section = 3

        tot_value += scheme['last_val']
        tot_acc += scheme['accrued']
        ws.write_row(row, 0, [scheme['scheme'],  round(scheme['last_val'],1), 
            round(scheme['age'], 1), round(scheme['newest'], 1), scheme['noLT'], 
            round(scheme['accrued']/100000, 1), 
            scheme['amfi'], scheme['isin'], scheme['xirr_1'], scheme['xirr_3'], scheme['xirr_6'], scheme['xirr_12']])
        row += 1
    row += 1

    ws.write_row(row, 0, ['TOTAL', int(tot_value), '', '', '', round(tot_acc/100000, 1)], style['bold'])
    row += 1

    ws.set_column(0, 0, 50)

def add_ws_cg(wb, year, style, folio_list):
    wsname = 'CG-'+year
    if args.verbose: print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)
    row = 0
    ws.write_row(row, 0, ['Scheme', 'Advisor', 'Type', 
        'Cur units', 'Cur NAV', 'Cur value (lacs)', 
        'Dated', 'Sold this year', 'Age of oldest unsold', 
        'STCG-debt', 'LTCG-debt', 'STCG_equity', 'LTCG_equity', 'CG Breakup'], style['bold'])
    row += 2

    tot_value = 0
    tot_sold = 0
    tot_stcg_debt = 0
    tot_ltcg_debt = 0
    tot_stcg_equity = 0
    tot_ltcg_equity = 0
    for folio in folio_list:
        ws.write_row(row, 0, [folio['amc'] + ' : ' + folio['folio']], style['bold'])
        row += 1
        for scheme in folio['schemes']:
            tot_value += scheme['nav']*scheme['close']
            if scheme['sold']: tot_sold += 1
            tot_stcg_debt += scheme['STCG_debt']
            tot_ltcg_debt += scheme['LTCG_debt']
            tot_stcg_equity += scheme['STCG_equity']
            tot_ltcg_equity += scheme['LTCG_equity']
            ws.write_row(row, 0, [scheme['scheme'], scheme['advisor'], scheme['type'], 
                int(scheme['close']), scheme['nav'], int(scheme['nav']*scheme['close']/100000), 
                scheme['date'], scheme['sold'], round(scheme['age'], 1), 
                scheme['STCG_debt'], scheme['LTCG_debt'], scheme['STCG_equity'], scheme['LTCG_equity'], convert_to_str_cg(scheme['CG'])])
            row += 1
        row += 1
    row += 1

    ws.write_row(row, 0, ['TOTAL', '', '', '', '', int(tot_value/100000), '', tot_sold, '', 
        tot_stcg_debt, tot_ltcg_debt, tot_stcg_equity, tot_ltcg_equity], style['bold'])
    row += 1

    tax_stcg_debt = max(tot_stcg_debt, 0) * 0.35
    tax_ltcg_debt = max(tot_ltcg_debt, 0) * 0.1 # need to apply indexation
    tax_stcg_equity = max(tot_stcg_equity, 0) * 0.15
    tax_ltcg_equity = max((tot_ltcg_equity - 100000), 0) * 0.1

    tot_tax  = tax_ltcg_equity + tax_stcg_equity + tax_stcg_debt + tax_ltcg_debt

    ws.write_row(row, 0, ['TAX', '', '', '', '', tot_tax, '', '', '', 
        tax_stcg_debt, tax_ltcg_debt, tax_stcg_equity, tax_ltcg_equity], style['bold'])

    ws.set_column(0, 0, 50)

def create_report(pdf_fname, folio_list, cur_fy_list, prev_fy_list, verbose):
    fname = change_pdf_to_xlsx(pdf_fname)
    #print("File name changed from %s to %s" % (args.file, fname))
    wb = xlsxwriter.Workbook(fname)

    style = {}
    style['bold'] = wb.add_format({'bold': True})
    style['ital'] = wb.add_format({'italic': True})
    style['large-red'] = wb.add_format({'bold': True, 'font_color': 'red', 'font_size':15})

    add_ws_summary(wb, style, folio_list)
    add_ws_debt(wb, style, folio_list)
    add_ws_equity(wb, style, folio_list)
    add_ws_cg(wb, 'curr', style, cur_fy_list)
    add_ws_cg(wb, 'prev', style, prev_fy_list)

    for folio in folio_list:
        add_ws_folio(wb, style, folio, verbose)

    wb.close()
    print("Writing workbook to: %s\n" % fname)

import configparser

def create_mfu(folio_lists, basemfparse):    
    now = time.time()
    nowstr = time.strftime('%Y-%m-%d_%H', time.gmtime(now))

    fname = basemfparse+nowstr+'.xlsx'
    wb = xlsxwriter.Workbook(fname)

    style = {}
    style['bold'] = wb.add_format({'bold': True})

    wsname = 'Summary'
    if args.verbose: print("Adding worksheet:", wsname)
    ws = wb.add_worksheet(wsname)

    row = 0
    ws.write_row(row, 0, ['Desc', 'Fund', 'Category', 'Folio#', 'Owner',
        'Units', 'NAV', 'Value', 
        'AMFI', 'ISIN', 'XIRR_1', 'XIRR_3', 'XIRR_6', 'XIRR_12' ], style['bold'])
    row += 1

    for owner in folio_lists.keys():
        folio_list = folio_lists[owner]
        for folio in folio_list:
            for scheme in folio['schemes']:
                ws.write_row(row, 0, [scheme['scheme'], folio['amc'],scheme['type'], folio['folio'], owner,
                    scheme['close'], scheme['lastnav'], scheme['last_val']*100000, 
                    scheme['amfi'], scheme['isin'], scheme['xirr_1'], scheme['xirr_3'], scheme['xirr_6'], scheme['xirr_12']])
                row += 1

    ws.set_column(0, 0, 50)

    wb.close()
    print("Writing workbook to: %s\n" % fname)


# ------------------------------ Other functions -----------------------------------------


def date2str(d):
	return d.strftime("%Y-%m-%d")

def str2date(d):
	return datetime.datetime.strptime(d, "%Y-%m-%d")

def strdate_diff(d1, d2):
	return str2date(d1)-str2date(d2)

def is_matching_purchase(trans_list, i, j):
    cur = trans_list[i]
    prev = trans_list[j]
    if ((float(cur['units']) + float(prev['units']) == 0) and 
        (float(cur['amount']) + float(prev['amount']) == 0) and 
        (cur['nav'] == prev['nav'])): 
        return True
    else:
        return False

def find_matching_purchase(trans_list, i):
    if is_matching_purchase(trans_list, i, i-1): return i-1
    if is_matching_purchase(trans_list, i, i-2): return i-2

def get_tbs_units(tbs_trans):
    tbs_units = float(tbs_trans['units']) if tbs_trans['units'] else 0
    if tbs_units > 0:
        for s in tbs_trans.get('sold', []):
            tbs_units -= s[0]
    return tbs_units

def compute_sold_on(trans_list, scheme_name):
    #pprint.pp(trans_list)
    tbs_index = 0
    for i, trans in enumerate(trans_list):
        units = float(trans['units']) if trans['units'] else 0
        nav = float(trans['nav']) if trans['nav'] else 0
        if units < 0:
            if 'Rejection' in trans['description']:
                j = find_matching_purchase(trans_list, i)
                j_nav = float(trans_list[j]['nav']) if trans_list[j]['nav'] else 0
                nav_delta = nav - j_nav
                yr_delta = strdate_diff(trans['date'], trans_list[j]['date'])/year
                trans_list[j]['sold'] = [(units, trans['date'], nav_delta, yr_delta)]
                trans_list[i]['bought'] = [(trans_list[j]['units'], trans_list[j]['date'], nav_delta, yr_delta)]
            else: # FIFO sale
                units_sold = -units
                while(units_sold > 0):
                    #print(f'{units_sold}, {tbs_index}')
                    if tbs_index >= len(trans_list):
                        if units_sold < 0.01:
                            #print("WARN: %f units remaining, index %d, ignoring (%s)" % (units_sold, tbs_index, scheme_name))
                            pass
                        else:
                            print("ERROR: %f units remaining, index %d (%s)" % (units_sold, tbs_index, scheme_name))
                            pprint.pprint(trans_list) 
                            sys.exit(1)
                        break
                    tbs_units = get_tbs_units(trans_list[tbs_index])
                    if tbs_units <= 0:
                        tbs_index += 1
                    else:
                        adjusted_units = min(tbs_units, units_sold)
                        units_sold -= adjusted_units
                        tbs_nav = float(trans_list[tbs_index]['nav']) if trans_list[tbs_index]['nav'] else 0
                        nav_delta = nav - tbs_nav
                        yr_delta = strdate_diff(trans['date'],trans_list[tbs_index]['date'])/year
                        if trans_list[tbs_index].get('sold', '') == '': trans_list[tbs_index]['sold'] = []
                        trans_list[tbs_index]['sold'].append((adjusted_units, trans['date'], nav_delta, yr_delta))
                        if trans_list[i].get('bought', '') == '': trans_list[i]['bought'] = []
                        trans_list[i]['bought'].append((adjusted_units, trans_list[tbs_index]['date'], nav_delta, yr_delta))
                        #print(f'{tbs_index}: {units_sold}, {tbs_units}, {adjusted_units}')

    # find oldest unsold block
    while tbs_index < len(trans_list):
        tbs_units = get_tbs_units(trans_list[tbs_index])
        if tbs_units > 0: break
        tbs_index += 1

    # find newest unsold block
    tbs_newest_index = len(trans_list) - 1
    while tbs_newest_index > tbs_index:
        tbs_units = get_tbs_units(trans_list[tbs_newest_index])
        if tbs_units > 0: break
        tbs_newest_index -= 1

    return trans_list, tbs_index, tbs_newest_index

def compute_CG(scheme, start, end):
    sold = False
    CG = []
    STCG_debt = 0
    LTCG_debt = 0
    STCG_equity = 0
    LTCG_equity = 0

    typ = scheme['type']
    for trans in scheme['transactions']:
        trans_date = str2date(trans['date'])
        units = float(trans['units']) if trans['units'] else 0
        if units >= 0 or trans_date < start or trans_date >= end or 'Rejection' in trans['description']: continue
        sold = True
        for b in trans['bought']:
            amount = b[0]*b[2]
            dur = b[3]
            CG.append((amount, b[3]))
            if typ == 'Debt':
                if dur < 3:
                    STCG_debt += amount
                else:
                    LTCG_debt += amount
            else: # 'Equity'
                if dur < 1:
                    STCG_equity += amount
                else:
                    LTCG_equity += amount
    return sold, CG, int(STCG_debt), int(LTCG_debt), int(STCG_equity), int(LTCG_equity)

def compute_accrued(scheme):
    tot_units = 0
    tot_cost = 0
    for trans in scheme['transactions']:
        units = get_tbs_units(trans) 
        if units <= 0: continue
        nav = float(trans['nav']) if trans['nav'] else 0
        tot_units += units
        tot_cost += units * nav
    return tot_units * float(scheme['nav']) - tot_cost

def sale_in(start, end, scheme):
    for trans in scheme['transactions']:
        trans_date = str2date(trans['date'])
        units = float(trans['units']) if trans['units'] else 0        
        if units < 0 and 'Rejection' not in trans['description'] and trans_date >= start and trans_date < end:
            return True
    return False

# ----------------------------------------------------------------------------

import sys
import glob

def get_latest_file(base, owner=None):
    if owner is None:
        fname = base + '202*.pdf'
    else:
        fname = base + '202*-' + owner + '.pdf'
    files = glob.glob(fname)
    if files == []: 
        print("get_latest_file: %s No files found %s" % (base, fname))
        return ""
    file = sorted(files)[-1]
    return file


def process_file(fname, passwd):
    # Get data in json format
    json_str = casparser.read_cas_pdf(fname, passwd, output="json")
    #pprint.pprint(json_str)
    data = json.loads(json_str)
    keys = data.keys()

    if args.verbose:
        print(keys)
        print(data['file_type'])
        print(data['investor_info'])
        print(data['statement_period'])

    owner_name = data['investor_info']['name']
    #print(owner_name)

    folio_list = data['folios']
    folio_num = len(folio_list)
    if args.verbose: print("Number of folios: %d" % folio_num)

    scheme_num_total = 0

    anomalies = 0
    segregated = 0
    new_folio_list = []
    cur_fy_list = []
    prev_fy_list = []

    for value in folio_list:
        #print("\t", value.keys())
        scheme_list = value['schemes']
        scheme_num =len(scheme_list)
        scheme_num_total += scheme_num
        if args.verbose: 
            print("\t%s %s (%s,%s,%s): %d schemes" % 
            (value['folio'], value['amc'], value['PAN'], value['KYC'], value['PANKYC'], scheme_num))

        cur_fy_folio = {}
        prev_fy_folio = {}
        new_folio = {}
        cur_fy_folio['folio'] = value['folio']
        prev_fy_folio['folio'] = value['folio']
        new_folio['folio'] = value['folio']
        cur_fy_folio['amc'] = value['amc']
        prev_fy_folio['amc'] = value['amc']
        new_folio['amc'] = value['amc']
        cur_fy_folio['schemes'] = []
        prev_fy_folio['schemes'] = []
        new_folio['schemes'] = []

        for scheme in scheme_list:
            #print("\t\t", scheme.keys())
            #print(scheme)
            scheme_name = scheme['scheme'].replace('\n', ' ')
            trans_list = scheme['transactions']
            trans_num = len(trans_list)
            last_trans_date = trans_list[-1]['date'] if trans_num > 0 else "1991-01-01" #datetime.date(1991, 1, 1)
            #print(last_trans_date, prev_fy_start_str)
            if last_trans_date < prev_fy_start_str and scheme['close'] == 0: continue
            # continue only if scheme is non-zero or had a transaction in last 2 FY

            if 'Segregated Portfolio' in scheme_name and trans_num>0:
                trans_list[0]['units'] = trans_list[0]['amount']
                trans_list[0]['amount'] = '0'
                segregated += 1

            if args.verbose:
                print("\t\t%s:%s (open %s close %s): %d transactions" % 
                (scheme['amfi'], scheme_name, scheme['open'], scheme['close'], trans_num))

            tot_units = 0
            for i, trans in enumerate(trans_list):
                # parsing error workaround
                if (trans['amount'] is None and trans['nav'] is None and trans['type'] == 'REDEMPTION'):
                    print(f'ERROR: trans {trans}, fixing')
                    trans_list[i]['amount'] = trans['units']
                    trans_list[i]['units'] = None

                units = float(trans['units']) if trans['units'] else 0
                balance = float(trans['balance']) if trans['balance'] else 0

                if i==0 and balance > 0 and units == 0:
                    print(f"ERROR: balance {trans['balance']} but units {trans['units']}, fixing")
                    trans_list[i]['units'] = trans_list[i]['balance']
                    units = balance
                tot_units += units

                trans_list[i]['sold'] = []
                trans_list[i]['bought'] = []
                
                    
            if abs(float(scheme['open']) + tot_units - float(scheme['close'])) > 1:
                anomalies += 1
                print("**** ANOMALY **** %s %d %s %s" % (scheme['open'], tot_units, scheme['close'],scheme_name))
                pprint.pprint([(x['units'], x['balance']) for x in trans_list])

            trans_list, tbs_index, tbs_newest_index = compute_sold_on(trans_list, scheme_name)
            
            new_scheme = {}
            new_scheme['scheme'] = scheme_name
            new_scheme['isin'] = scheme['isin']
            new_scheme['amfi'] = scheme['amfi']
            new_scheme['advisor'] = scheme['advisor']
            new_scheme['close'] = float(scheme['close'])
            new_scheme['nav'] = float(scheme['valuation']['nav'])
            new_scheme['date'] = scheme['valuation']['date']
            new_scheme['type'] = 'Debt' if any(x in scheme_name.lower() for x in 
                                ['income', 'debt', 'bond', 'liquid', 'ultra', 'sdl', 'gilt', 'sec', 'money']) else 'Equity'
            new_scheme['transactions'] = trans_list
            new_scheme['age'] = (today - str2date(trans_list[tbs_index]['date']))/year if tbs_index < len(trans_list) else 0        
            new_scheme['newest'] = (today - str2date(trans_list[tbs_newest_index]['date']))/year if tbs_newest_index < len(trans_list) else 0        
            new_scheme['noLT'] = True if trans_list[tbs_newest_index]['date'] > '2023-03-31' else False
            new_scheme['newest_date'] = trans_list[tbs_newest_index]['date']
            new_scheme['accrued'] = compute_accrued(new_scheme)
            new_scheme['val'] = new_scheme['nav']*new_scheme['close']/100000

            if new_scheme['close'] > 0: 
                nav_history = get_nav_history_cache(scheme['amfi'], False, args.verbose) if scheme['amfi'] else {}
                new_scheme['xirr_12'] = nav_history.get('xirr_12', 0)
                new_scheme['xirr_6'] = nav_history.get('xirr_6', 0)
                new_scheme['xirr_3'] = nav_history.get('xirr_3', 0)
                new_scheme['xirr_1'] = nav_history.get('xirr_1', 0)
                new_scheme['lastdate'] = nav_history.get('lastday', '')
                new_scheme['lastnav'] = float(nav_history.get('nav_last', 0))
                new_scheme['last_val'] = new_scheme['lastnav']*new_scheme['close']/100000

                new_folio['schemes'].append(new_scheme)
                
            if sale_in(cur_fy_start, today, new_scheme): 
                cur_scheme = new_scheme.copy()
                cur_scheme['sold'], cur_scheme['CG'], cur_scheme['STCG_debt'], cur_scheme['LTCG_debt'], \
                        cur_scheme['STCG_equity'], cur_scheme['LTCG_equity'] = compute_CG(cur_scheme, cur_fy_start, today)
                cur_fy_folio['schemes'].append(cur_scheme)
            if sale_in(prev_fy_start, cur_fy_start, new_scheme): 
                prev_scheme = new_scheme.copy()
                prev_scheme['sold'], prev_scheme['CG'], prev_scheme['STCG_debt'], prev_scheme['LTCG_debt'], \
                        prev_scheme['STCG_equity'], prev_scheme['LTCG_equity'] = compute_CG(prev_scheme, prev_fy_start, cur_fy_start)
                prev_fy_folio['schemes'].append(prev_scheme)
        
        if len(new_folio['schemes']) > 0: new_folio_list.append(new_folio)
        if len(cur_fy_folio['schemes']) > 0: cur_fy_list.append(cur_fy_folio)
        if len(prev_fy_folio['schemes']) > 0: prev_fy_list.append(prev_fy_folio)
           
    print("FOLIOS:%d, SCHEMES:%d, SEGREGATED:%d" % (folio_num, scheme_num_total, segregated))
    if args.verbose: print("Active: %d, CG-current: %d, CG-prev:%d" % (len(new_folio_list), len(cur_fy_list), len(prev_fy_list)))
    if anomalies > 0: print("\n******* CHECK OUT THE ANOMALIES = %d *******\n" % anomalies)

    create_report(fname, new_folio_list, cur_fy_list, prev_fy_list, args.verbose)
    return new_folio_list


# --------------------------- MAIN CODE -----------------------------------------------


P = argparse.ArgumentParser(description="__doc__")
P.add_argument("-f", "--file", type=str, default=None, help="File to process")
P.add_argument("-p", "--password", type=str, default=None, help="Password")
P.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
args = P.parse_args()

year = datetime.timedelta(days=365)
today = datetime.datetime.today()
#print(today.year, today.month, today.day)
if today.month >= 4: 
    cur_fy_start = datetime.datetime(today.year, 4, 1)
else: 
    cur_fy_start = datetime.datetime(today.year-1, 4, 1)
prev_fy_start = datetime.datetime(cur_fy_start.year-1, 4, 1)
#print(today, cur_fy_start, prev_fy_start)
prev_fy_start_str = date2str(prev_fy_start)

config = configparser.ConfigParser()
config.read('config.ini')
data = config['data']
basemfparse = data['basemfparse']
basecams = data['basecams']
owners = [x.split('-')[1] for x in config.sections() if x.startswith('cam-')]

if args.file is None:
    # if no file is passed, get latest CAM file for each owner
    new_folio_lists = {}
    for owner in owners:
        fname = get_latest_file(basecams, owner)
        if fname == '': 
            print('No file found', basecams, owner)
            sys.exit(1)

        print("\n**** Opening file %s for processing ..." % fname)

        cam = config['cam-'+owner]
        passwd = cam['pan']  

        print('Owner is:', owner, passwd)

        new_folio_lists[owner] = process_file(fname, passwd)
    create_mfu(new_folio_lists, basemfparse)
else:
    print("\nOpening file %s for processing ...\n" % args.file)
    
    owner = args.file.split('-')[-1].split('.')[0]
    if owner not in owners: owner = get_default_owner()

    if args.password is None:
        cam = config['cam-'+owner]
        args.password = cam['pan']  

    print('Owner is:', owner, args.password)
    process_file(args.file, args.password)

