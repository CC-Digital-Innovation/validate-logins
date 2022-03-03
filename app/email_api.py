import configparser
import json
from pathlib import Path

import requests
from loguru import logger

# read and parse config file
config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['email']['token']
ID = config['email']['id']
SENDER = config['email']['sender']
RECIPIENTS = config['email']['recipients']
CC = config['email']['cc']
BCC = config['email']['bcc']
SUBJECT = config['email']['subject']
BODY = config['email']['body']
REPORT_NAME = config['email']['report_name']
TABLE_TITLE = config['email']['table_title']
API = config['email']['api']

def send_report(result):
    logger.debug('Creating dump file...')
    with open('data-dump.json', 'w') as fp:
        json.dump(result, fp)
    logger.debug('Dump file created.')
    logger.debug('Using email API to send report...')
    try:
        with open('data-dump.json', 'rb') as fp:
            email(fp)
        logger.debug('Returned from email-api')
    finally:
        logger.debug('Deleting dump file...')
        Path('data-dump.json').unlink(missing_ok=True)
        logger.debug('Dump file deleted.')

def email(file):
    url = API
    data = {
        'Token': TOKEN,
        'ID': ID,
        'sender': SENDER,
        'subject': SUBJECT,
        'to': RECIPIENTS,
        'cc': CC,
        'bcc': BCC,
        'body': BODY,
        'report_name': REPORT_NAME,
        'table_title': TABLE_TITLE
    }
    response = requests.post(url, data=data, files={'file': file})
    response.raise_for_status()
