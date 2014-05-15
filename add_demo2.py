#!/usr/bin/env python
#
# This module takes a subnet, BIG-IQ information, and a BIG-IQ Group name,
# then tries to add any BIG-IP devices discovered on the subnet to the BIG-IQ.
#
# Usage examples:
# ./add_demo.py --bigiq-address 172.27.96.186 --group cm-cloud-managed-devices --subnet 192.168.42.0 --user admin -password admin
# ./add_demo.py --bigiq-address 172.27.96.186 --group cm-cloud-managed-devices --subnet 192.168.42.0 --user admin -password admin --timeout=2

import urllib
import urllib2
import httplib
import json
import socket
import base64
import gc
import argparse

# module variables
add_bip_data = '{{ "address" : "{0}", "userName" : "{1}", "password" : "{2}" }}'

HTTP_AUTHORIZATION_HEADER = 'Authorization'
HTTP_CONTENT_TYPE_HEADER = 'Content-Type'
HTTP_CONTENT_TEXT = 'text/html'
HTTP_CONTENT_XML = 'application/xml'
HTTP_CONTENT_JSON = 'application/json'

#
#
#
# look_for_big_ip(addr, name, passw)
# addr = IP address of device to check.
# name = default user name to use for authentication of BIG-IP API
# passw = default password to use for authentication of BIG-IP API
# Given an IP, a user name, and a password, check to see if it is a BIG-IP by calling the "get modules"
# BIG-IP function. If the error is an F5 auth error, call check_if_big_iq() on that address to see
# if it is a BIG-IQ. Returns 1 if the addr is a BIG-IP, 0 otherwise.
# NOTE: Uses timeout value to limit length of time waiting for response. If a known BIG-IP doesn't get
# added, change timeout value and try again.
#######################################################################
def look_for_big_ip(auth_handler, addr, name, passw, timeout):

    # let's just set up URI here so we can use it in add_password and urlopen both.
    uri = 'https://{0}/mgmt/tm/ltm'.format(addr)
    
    # Add our login information.
    auth_handler.add_password(realm='Enterprise Manager',
                          uri=uri,
                          user='admin',
                          passwd='admin')
        
    try:    
        ret = urllib2.urlopen(uri, timeout=timeout)
    except IOError as e:
        if hasattr(e, 'code'):
            if e.code != 401:
                # print (e, addr, name, passw)
                print ('IO Err', addr, e.reason)
                return(0)
            else:
                # print (addr, e.code, name, passw)
                print ('401 Err', addr, e.reason)
                if('F5 Auth' in str(e.reason)):
                    print('Checking for BIG-IQ')
                    if(check_if_big_iq(auth_handler, addr, name, passw)):
                        return(0)
                    else:
                        print ('Got One!')
                        return(1) # Obviously F5 device, not BIG-IQ.
                
                return(0)
        else:
            if(hasattr(e, 'reason')):
                print(addr, name, passw, e.reason)
            else:
                print('Time out', addr, name, passw, e)
            return(0)
    except socket.error as e:
        print('Socket Error', addr, name, passw)
        return(0)
    except httplib.BadStatusLine as e:
        print('Bad status line', addr, name, passw)
        return(0)
    
    print('GOT ONE!')
    return 1


#
#
#
# check_if_big_iq(addr, name, passw)
# addr = IP address of device to check.
# name = default user name to use for authentication of BIG-IQ API
# passw = default password to use for authentication of BIG-IQ API
# Given an IP, a user name, and a password, check to see if it is a BIG-IQ by calling the
# "get tenants" BIG-IQ function. Returns 1 if the addr is a BIG-IQ, 0 otherwise.
# NOTE: Uses timeout value to limit length of time waiting for response. If a known BIG-IP doesn't get
# added, change timeout value and try again.
#######################################################################
def check_if_big_iq(auth_handler, addr, name, passw):

    # Add our login information.
    auth_handler.add_password(realm='Big-IQ',
                              uri='https://{0}/mgmt/cm/cloud/tenants'.format(addr),
                              user=name,
                              passwd=passw)

    # Now try to open the url..
    try:
     r = urllib2.urlopen('https://{0}/mgmt/cm/cloud/tenants'.format(addr))
    except IOError as e:
        return(0)
    except socket.error as e:
         # print('Socket Error', addr, name, passw)
         return(0)
    except httplib.BadStatusLine as e:
         # print('Bad status line', addr, name, passw)
         return(0)

    print('Found BIG-IQ, not adding.')
    return(1)



#
#
#
# add_big_ip(addr, name, passw, toaddr, touser, topassw, group)
# addr = IP address of device to check.
# name = default user name to use for authentication of BIG-IP API
# passw = default password to use for authentication of BIG-IP API
# toaddr = BIG-IQ to add this BIG-IP to
# touser = username on BIG-IQ
# topassw = password on BIG-IQ
# group = the BIG-IQ group. command line defaults this to "cm-cloud-managed-devices"
#
# Given an IP, a user name, and a password for a BIG-IP, and an IP, username, password, plus
# group on a BIG-IQ, add the BIG-IP to the list of BIG-IQ managed devices by calling the
# "add device" BIG-IQ function. Returns 1 on success, 0 otherwise.
# NOTE: Uses timeout value to limit length of time waiting for response. If a known BIG-IP doesn't get
# added, change timeout value and try again.
#######################################################################
def add_big_ip(auth_handler, ipaddr, name, passw, toaddr, touser, topassw, group):

    print('adding device: {0}'.format(ipaddr))

    # format the request URI with our IP
    request = 'https://{0}/mgmt/shared/resolver/device-groups/{1}/devices'.format(toaddr, group)

    # fill in the request payload with values passed in.
    request_json = add_bip_data.format(ipaddr, name, passw)

    # make the headers 
    headers = {}
    headers[HTTP_CONTENT_TYPE_HEADER] = HTTP_CONTENT_JSON

    # Add our login information.
    auth_handler.add_password(realm='Big-IQ',
                          uri=request,
                          user=touser,
                          passwd=topassw)
    
    # build the request out of the URL, the payload, and the headers.
    urlrequest = urllib2.Request(request, request_json, headers)

    # tell it which HTTP method we're calling.
    urlrequest.get_method = lambda: 'POST'
    ret = None  
    
    # Now try to open the url..
    try:
     ret = urllib2.urlopen(urlrequest, timeout=10)
    except IOError as e:
        if hasattr(e, 'code'):
            if e.code != 401:
                # print ('We got another error')
                # print ('Not 401: ', e.code, e.errno, e.reason)
                if(e.code == 400):
                    print('Found BIG-IP already under management: {0}'.format(ipaddr))
                else:
                    print('Failed to add BIG-IP. Code: {0}'.format(e.code))
                return(0)
            else:
                # print ('Not Authorized', e.code)
                # print (e.headers['www-authenticate'])
                return(0)
        else:
            # print(e.errno, e.reason)
            return(0)
    except socket.error as e:
        # print('Time out on socket')
        return(0)
    except httplib.BadStatusLine as e:
        # print('Invalid server response')
        return(0)
    return(1)



#
#
#
# Main routine
# 1. Get the command line parameters
# 2. Set up our global auth handler (were auth info will be set up for each BIG-IP)
# 3. Loop through the subnet and build a list of known BIG-IPs
# 4. Add each element in the list to the BIG-IQ
# 5. Celebrate!
#############################################################################

## 1. Set up argument parser and validate inputs.
parser = argparse.ArgumentParser(description="Demonstrates finding and adding BIG-IPs to BIG-IQ in release 4.2")
    
# parser.add_argument('-v', '--verbose', action='store_true', default=False)
# parser.add_argument('-m', '--demo-mode', action='store_true', default=False)
    
parser.add_argument('--bigiq_address', required=True)
parser.add_argument('--bigiq_user', required=True)
parser.add_argument('--bigiq_password', required=True)
parser.add_argument('--bigip_user', required=True)
parser.add_argument('--bigip_password', required=True)
parser.add_argument('--subnet', required=True)
parser.add_argument('--timeout', default=1)
parser.add_argument('--group', default='autodeploy-all-devices')
    
args = parser.parse_args()

if((args.subnet[-1] != '0') | (args.subnet[-2] !='.')):
    print('Error - subnet must be of the form a.b.c.0')
    exit(-1)
else:
    subnet = args.subnet[0:-1] + '{0}'

## 2. Set up auth handler for use in all connections through urllib2
    
# get an authorization object.
auth_handler = urllib2.HTTPBasicAuthHandler()

# have it built for us to always use our login info on that URI.
opener = urllib2.build_opener(auth_handler)

# ...and install it globally so it can be used with urlopen.
urllib2.install_opener(opener)

## 3. Traverse the subnet, looking for BIG-IPs.

print('beginning scanning on subnet', args.subnet)
print('This will take approximately {0} minutes'.format(4.26*int(args.timeout)))

#  Build a list of BIG-IPs on the subnet
bigip_list = []

for x in range(1,255):
    ip_string = subnet.format(x)
    if(look_for_big_ip(auth_handler, ip_string, args.bigip_user, args.bigip_password, int(args.timeout))):
	bigip_list.append(ip_string)

## 4. Add the list to the BIG-IQ
if(len(bigip_list)):
    print('Attempting to add {0} BIG-IPs to the BIG-IQ'.format(len(bigip_list)))

counter = 0
for bigip in bigip_list:
        print('Adding: ', bigip)
        success = add_big_ip(auth_handler, bigip, args.bigip_user, args.bigip_password, args.bigiq_address, args.bigiq_user, args.bigiq_password, args.group)
        if(success):
            counter+=1
if(counter):            
    print('Done! Added {0} BIG-IPs!'.format(counter))	
else:
    print('Done. No BIG-IPs found.')
