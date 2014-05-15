#!/usr/bin/env python
# This sample shows how to gather the statistics for a given tenant's applications
# from the BIG-IQ. It is implemented using urllib and urllib2, if your environment
# supports it, the code could be greatly simplified by switching to the requests
# package

# NOTE: This sample written and tested with BIG-IQ version 4.3 and Python 2.75.

import urllib2
import urllib
import json
import argparse

#
# Function getAppHealth takes the IP of the BIG-IQ, the name of a valid tenant
# on the BIG-IQ, and the name of an app belonging to the tenant. It queries the
# health of the app, then selects the most important of the responses to display
# it displays that app's health using the selected values, and then returns.
# This function assumes that username and password have already been used to
# set the global URL opener.

def getAppHealth(ip, tenantName, appName):
    try:
     r = urllib2.urlopen('https://{0}/mgmt/cm/cloud/tenants/{1}/services/iapp/{2}/stats'.format(ip, tenantName, appName))
    except IOError as e:
        if hasattr(e, 'code'):
            if e.code != 401:
                print ('We got another error')
                print (e.code)
            else:
                print (e.headers)
                print (e.headers['www-authenticate'])
                exit(0)

    status = r.getcode()
    result = r.read()
    string_result=result.decode('utf-8')
    response = json.loads(string_result)
    
    healthList = response["entries"]
    healthSummary = healthList["health.summary"]
    status = healthSummary["description"]
    print(status)

#
# Function appListForTenant gets the list of apps the tenant has deployed.
# Since this is a straight-forward demo, it then calls getAppHealth() on each
# of the tenant's apps. In a more complex scenario, it should just return the
# list of apps to provide for portability.
def appListForTenant(ip, tenantName):
    try:
     r = urllib2.urlopen('https://{0}/mgmt/cm/cloud/tenants/{1}/services/iapp'.format(args.address, tenantName))
    except IOError as e:
        if hasattr(e, 'code'):
            if e.code != 401:
                print ('We got another error')
                print (e.code)
            else:
                print (e.headers)
                print (e.headers['www-authenticate'])
                exit(0)

    result = r.read()
    string_result=result.decode('utf-8')
    response = json.loads(string_result)

    # Build app-id list
    appList = response["items"]
    print len(appList)
    if len(appList) == 0:
        print('No apps deployed for Tenant {0}'.format(tenantName))
        return
    for x in range(0, len(appList)):
        app = appList[x]
        appName = app["name"]
        print ('\nAPP NAME:\t{0}'.format(appName))
        getAppHealth(ip, tenantName, appName)


# Main routine.
# The main routine looks up the identifier of the tenant passed on the command
# line, then uses that ID to call AppListForTenant()

# Set up the parser
parser = argparse.ArgumentParser(description="Demonstrates generating statistics by Application and Owner in BIG-IQ release 4.2")
    
parser.add_argument('--address', required=True)
parser.add_argument('--user', required=True)
parser.add_argument('--password', required=True)
    
args = parser.parse_args()


# get an authorization object.
auth_handler = urllib2.HTTPBasicAuthHandler()

# Add our login information.
auth_handler.add_password(realm='Big-IQ',
                          uri='https://{0}/mgmt/cm/cloud/tenants'.format(args.address),
                          user=args.user,
                          passwd=args.password)

# have it built for us to always use our login info.
opener = urllib2.build_opener(auth_handler)

# ...and install it globally so it can be used with urlopen.
urllib2.install_opener(opener)

# Now try to open the url that returns the tenant list..
try:
 r = urllib2.urlopen('https://{0}/mgmt/cm/cloud/tenants'.format(args.address))
except IOError as e:
    if hasattr(e, 'code'):
        if e.code != 401:
            print ('We got another error')
            print (e.code)
        else:
            print (e.headers)
            print (e.reason)
            # print (e.headers['www-authenticate'])
            exit(0)

# show the status and headers for debugging purposes
status = r.getcode()
print('http status: ', status)
result = r.read()
string_result = result.decode('utf-8')
                              
# Put it into the JSON decoder
response = json.loads(string_result)

# Walk through tenant-id list
tenantList = response["items"]
for x in range(0, len(tenantList)):
    tenant = tenantList[x]
    tenantName = tenant["name"]
    print ('\nTENANT NAME:\t{0}'.format(tenantName))
    # Now go get each app for each tenant...
    appListForTenant(args.address, tenantName)
    


