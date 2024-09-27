#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 12:53:37 2018

@author: sandeshgoel
"""

from analyze_util import *
from send_mail_util import *
import argparse

parser = argparse.ArgumentParser(description='Gap summary report')
parser.add_argument('-r', '--recipient', type=str, help='recipient(s) of message, comma separated list (default sandesh@gmail.com)', default='sandesh@gmail.com')
args = parser.parse_args()

NUM_DAYS = 30
now = time.time()

rep = ''
for offset in range(NUM_DAYS):
    rep = get_report_file(now, offset)
    if rep != '': break

print(rep)

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

send_mail(sub, "Latest net worth statement", args.recipient, rep, mail_from, mail_pwd)
