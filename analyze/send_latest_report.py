from analyze_util import *
from send_mail_util import *
import argparse

parser = argparse.ArgumentParser(description='Gap summary report')
args = parser.parse_args()

NUM_DAYS = 30
now = time.time()

rep = ''
img = ''
for offset in range(NUM_DAYS):
    rep = get_report_file(now, offset)
    if rep != '': 
        img = get_image_file(now, offset)
        break

print(rep, img)

import openpyxl

wb = openpyxl.load_workbook(rep)
sheet = wb.active
sub = sheet['A3'].value
print(sub)

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
mail = config['mail']
mail_from = mail['from']
mail_pwd = mail['passwd']
mail_to = mail['weekly_to']

send_mail(sub, "Latest net worth statement", mail_to, f'{rep},{img}', mail_from, mail_pwd)
