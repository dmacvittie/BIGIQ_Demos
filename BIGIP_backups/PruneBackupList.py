#!/usr/bin/env python
#
import requests
import json
import argparse
import sys
import time
from time import mktime
from datetime import datetime
import logging

# Start the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('biqbackup.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info('================Pruning log initialized.===================')

# Set up command line parser

parser = argparse.ArgumentParser(description="Get Backup List")

parser.add_argument('--address', required=True)
parser.add_argument('--user', required=True)
parser.add_argument('--password', required=True)
parser.add_argument('--age', required=False, default=30)

args = parser.parse_args()


ses = requests.Session()
ses.auth = (args.user, args.password)
ses.verify = False # don't validate certs

uri = 'https://{0}/mgmt/cm/system/backup-restore'.format(args.address)

try:
    r = ses.get(uri)
except requests.exceptions.RequestException as e:
    logger.error('Error getting list: {0}'.format(e.__class__))
    # Cannot continue without the list of backups, so exit
    logger.error('Exiting without pruning - check communications with BIG-IQ')
    exit()
    
if r.status_code != 200:
    logger.error('Status code {0} returned from BIG-IQ. Exiting.'.format(r.status_code))
    exit()
    
result = r.json()

items = result['items']
currentDateTime = time.localtime()

logger.info(time.strftime("Date/time: %c", currentDateTime))

for item in items:
    logger.info ('processing backup: {0}'.format(item['name']))

    # Used to control checking of request status on exceptions.
    errors = False

    # Get the task ID for the call to Delete
    taskID = item['id']

    # Get the date out of the date/time
    strDateTime = item['startTime'].split('T')
    logger.info('\tBackup Date: {0}'.format(strDateTime[0]))

    # Get the machine ID to uniquely ID device
    dev = item['device']
    
    # Convert dates and find age of backup
    bDate = time.strptime(strDateTime[0], "%Y-%m-%d")
    backupDate = datetime.fromtimestamp(mktime(bDate))
    todaysDate = datetime.fromtimestamp(mktime(currentDateTime))
    delta = todaysDate - backupDate
    logger.info('\tAge of Backup: {0} days'.format(delta.days))

    # Determine if backup is too old and delete if so
    if delta.days > int(args.age):

        uri = 'https://{0}/mgmt/cm/system/backup-restore/{1}'.format(args.address, taskID)
        try:
            r = ses.delete(uri)
        except requests.exceptions.RequestException as e:
            logger.error('Exception deleting backup {0}'.format(item['name']))
            errors = True

        if not errors:    
            if r.status_code == 200:
                logger.info('\tBackup {0} deleted successfully.'.format(item['name']))
            else:
                logger.error('\tBackup {0} deletion failed, status {1}.'.format(item['name'], r.status_code))
                logger.error('\tTask ID: _{0}_'.format(taskID))

logger.info('Backup pruning completed.')

