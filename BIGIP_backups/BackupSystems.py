#!/usr/bin/env python
#
#
#
#

# BackupSystems.py -- Sample of backing up all devices under management of a BIG-IQ device.
# This system calls the BIG-IQ to get a list of devices it currently has under management
# and then directs the BIG-IQ to back each one up.

# VERSION:              1.0 Written/Tested on BIG-IQ 4.3
# Date last modified:   03 APR 2014


import requests
import json
import argparse
import sys
from datetime import date 
import logging

# Start the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('biqbackup.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info('================Backup log initialized.===================')

# Set up command line parser

parser = argparse.ArgumentParser(description="Get Backup List")

parser.add_argument('--address', required=True)
parser.add_argument('--user', required=True)
parser.add_argument('--password', required=True)
parser.add_argument('--group', required=False, default='cm-autodeploy-group-manager-autodeployment')

args = parser.parse_args()


ses = requests.Session()
ses.auth = (args.user, args.password)
ses.verify = False # don't validate certs

uri = 'https://{0}/mgmt/shared/resolver/device-groups/{1}/devices'.format(args.address, args.group)

# print uri

try:
    r = ses.get(uri)
except requests.exceptions.RequestException as e:
    # ConnectionError does not have a __name__ on __class__ so using uglier "__class__" alone.
    logger.info('-- {0} on {1} --'.format(e.__class__))
    # Cannot continue without the list of devices, so exit.
    logger.error('Backups not performed. Check communications with BIG-IQ')
    exit()

if r.status_code != 200:
    logger.error('Status code {0} returned from BIG-IQ. Exiting without backing up.'.format(r.status_code))
    exit()
    

result = r.json()

items = result['items']

logger.info('Have obtained list with {0} devices in it'.format(len(items)))


today = date.today() # Used to generate daily unique filenames
desc = 'Automated backup -- {0}'.format(today)


for item in items:
    errors = False # Used to track if we hit an exception in each backup.
    name = '{0}{1}.ucs'.format(item['hostname'], today)
    
    if item['product'] == 'BIG-IP':
        devRef = {'link':'https://{0}/mgmt/shared/resolver/device-groups/cm-autodeploy-group-manager-autodeployment/devices/{1}'.format(args.address, item['uuid'])}
        params = {'name':name, 'description':desc, 'deviceReference':devRef}
        uri = 'https://{0}/mgmt/cm/system/backup-restore'.format(args.address)
        try:
            r = ses.post(uri, data=json.dumps(params))
        except requests.exceptions.RequestException as e:
            logger.info('-- {0} on {1} --'.format(e.__class__.__name__))
            errors = True
            
        if not errors:
            # BIG-IQ returns a 400 response code if the file name already exists.
            # Here we use that to determine that the backup (formatted name + date)
            # has already been run today. for testing it might be viable to change
            # this code to modify the filename and try again.
            if r.status_code == 400:
                logger.info('\tBackup {0} already performed today, skipping.'.format(name))
            else:
                logger.info('Backup {0} kicked off.'.format(name))
            # For simplicity, this demo does not poll to await completion
            # If using in a production environment, check the documentation of the API
            # /mgmt/cm/system/backup-restore/{taskID} for polling.
        
    elif item['product'] == 'BIG-IQ':
        params = {'file':name, 'action':'BACKUP'}
        uri = 'https://{0}/mgmt/tm/shared/sys/backup'.format(args.address)
        try: 
            r = ses.post(uri, data=json.dumps(params))
        except requests.exceptions.RequestException as e:
            logger.info('-- {0} on {1} --'.format(e.__class__.__name__))
            Errors = True

        # Note that the API to back up BIG-IQ does not halt on duplicate filename,
        # So any BIG-IQs in the list will correctly show as backing up in the logs.
        if not errors:
            logger.info('BIG-IQ backup {0} kicked off.'.format(name))
            
        # Again, for simplicity this sample does not copy files off the BIG-IQ -
        # meaning that the BIG-IQ has a backup... on the BIG-IQ. Not a production
        # ready scenario. check the iControl REST API /mgmt/shared/file-transfer/ucs-downloads
        # or download them using a method such as ftp or scp.
    else:
        logger.info('Did not back up device {0} because it is not a BIG-IQ or BIG-IP.'.format(item['hostname']))

logger.info('Backup completed.')
