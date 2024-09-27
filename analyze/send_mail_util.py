#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 12:59:58 2018

@author: sandeshgoel
"""

from os.path import basename
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

def send_mail(subject, text, to_mail, attach, from_mailid, from_passwd):
    to = (to_mail).split(",")
    if attach == '':
        files = []
    else:
        files = attach.split(",")

    header = 'To:' + ",".join(to) + '\n' + 'From: ' + from_mailid + '\n' + 'Subject: ' + subject + '\n'
    #print(header)
 
    msg = MIMEMultipart()
    msg['From'] = from_mailid
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    smtpserver = smtplib.SMTP('smtp.gmail.com:587')
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(from_mailid, from_passwd)

    print("Sending mail to", to)

    message = msg.as_string() 
    smtpserver.sendmail(from_mailid, to, message)
    smtpserver.close()
