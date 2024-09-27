import argparse
from send_mail_util import *

parser = argparse.ArgumentParser(description='Gap summary report')
parser.add_argument('-s', '--subject', type=str, help='email subject (default test)', default='test')
parser.add_argument('-m', '--message', type=str, help='email message (default test)', default='test')
parser.add_argument('-f', '--filename', type=str, help='file containing email message')
parser.add_argument('-a', '--attach', type=str, help='file to send as attachment', default='')
args = parser.parse_args()

if args.filename is None:
    message = args.message
else:
    file = open(args.filename, 'r')
    message = file.read()
    file.close()

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
mail = config['mail']
mail_from = mail['from']
mail_pwd = mail['passwd']
mail_to = mail['daily_to']

send_mail(args.subject, message, mail_to, args.attach, mail_from, mail_pwd)
