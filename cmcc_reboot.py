#!/usr/bin/env python3

# for the variables
#https://github.com/e13olf/Huawei-EchoLife-Router-Reboot/blob/main/Huawei_Echolife_reboot.py
# for the script
#https://github.com/mcxiaoke/python-labs/blob/master/labs/cmcc_reboot.py

# Works with HG8145V5

import os
import sys
import re
import codecs
import base64
import requests
import pickle

reboot_me = True
HOST='192.168.0.1'
PROT='https'
GATEWAY_URL = PROT + '://' + HOST + '/'
RAND_COUNT_URL = PROT + '://' + HOST + '/asp/GetRandCount.asp'
LOGIN_URL = PROT + '://' + HOST + '/login.cgi'
DEVICE_URL = PROT + '://' + HOST + '/html/ssmp/reset/reset.asp'
REBOOT_URL = PROT + '://' + HOST + '/html/ssmp/devmanage/set.cgi'

REBOOT_PARAMS = {'x': 'InternetGatewayDevice.X_HW_DEBUG.SMP.DM.ResetBoard',
                 'RequestFile': 'html/ssmp/reset/reset.asp'}

HW_TOKEN_PATTERN = r'id="hwonttoken" value="(\w+)">'

COOKIE_DEFAULT = {'Cookie': 'body:Language:english:id=1'}

#####  use pickle to stash the password because importing a config file does not work.
#####import pickle
#####u = 'admin'
#####p = 'password'
#####
###### Saving the objects:
#####with open('cmcc_reboot_vars', 'wb') as f:
#####    pickle.dump([u,p], f)

# Getting back the objects:
with open('/home/ansible/ansible/cmcc_reboot_vars', 'rb') as f:
    _user, _pass = pickle.load(f)

ADMIN_USER = _user
ADMIN_PASS = _pass

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel) AppleWebKit/537.36 Chrome/77.0.3865.90 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*',
    'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7',
    'Referer': PROT + '://' + HOST + '/index.asp',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1'
}


def cGet(url, params=None, **kwargs):
    return requests.get(url, params, headers=HEADERS, timeout=10, **kwargs)


def cPost(url, data=None, **kwargs):
    return requests.post(url, data, headers=HEADERS, timeout=10, **kwargs)

# get hw token param from server


def getToken():
    r = cPost(RAND_COUNT_URL, verify=False, cookies=COOKIE_DEFAULT)
    if r.ok and r.text:
        return r.text[3:]
    else:
        print('Failed to get token, reason:', r.status_code)


# login and get cookies
def login(user, passwd, token):
    username = user
    password = base64.b64encode(passwd.encode('utf-8')).decode("utf-8")
    print('Login using account:', username, password)
    r = cPost(LOGIN_URL, verify=False, data={
        'UserName': username,
        'PassWord': password,
        'x.X_HW_Token': token
    }, cookies=COOKIE_DEFAULT)
    if r.ok and r.cookies:
        return r.cookies
    else:
        print('Failed to login, reason:', r.status_code)


# get hw token param
def getHWToken(cookies):
    r = cGet(DEVICE_URL, verify=False, cookies=cookies)
    # print(r.request.headers)
    if r.ok:
        print('hwonttoken' in r.text)
        m = re.search(HW_TOKEN_PATTERN, r.text)
        if m and m.group(1):
            return m.group(1)
        else:
            print('Failed to get hw token, reason:', r.status_code)


# reboot devie using cookies and hw token
def reboot(cookies, token):
    try:
        r = cPost(REBOOT_URL, verify=False, params=REBOOT_PARAMS, data={
            'x.X_HW_Token': token}, cookies=cookies)
        print(r.request.url)
        print(r.request.body)
        print(r.status_code)
        if r.ok:
            print('Device will reboot now.')
        else:
            print('Failed to reboot device.')
    except requests.exceptions.ReadTimeout as e:
        print('Device will reboot now.')
    except Exception as e:
        print('Failed to reboot device, reason:', e)

# get all done


def doReboot():
    token = getToken()
    if not token:
        print('no token, abort')
        return
    print('get token result:', token)
    cookies = login(ADMIN_USER, ADMIN_PASS, token)
    print('get cookies result:', cookies)
    if not cookies:
        print('no cookies, abort')
        return
    token = getHWToken(cookies)
    print('get hwToken result:', token)
    if not token:
        print('no hw token, abort')
        return
    if reboot_me:
        reboot(cookies, token)
        print('reboot executed.')
    else:
        print('reboot canceled.')


if __name__ == "__main__":
    doReboot()
