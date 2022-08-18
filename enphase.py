import requests
import json
import base64
import sys
import random
import time
from datetime import datetime
import datetime
import variables

def count_API():
    '''refresh existing token for a new one'''
    now = datetime.datetime.now()
    timing = now.strftime("%d-%m-%Y,%H:%M")
    counter = {}

    try:
        with open(variables.API_settings, 'r') as f:
            counter = json.load(f)
        try:
            if counter[timing] > 0:
                counter[timing]+=1
            else:
                counting[timing] = 1
                print("It should not end here")
        except:
            counter[timing] = 1
    except:
        counter[timing] = 1

    if counter[timing] > variables.API_limit:
        sleeptime = 60 - datetime.datetime.now().second
        print('Sleeping for', sleeptime,'seconds (Count_API)')
        time.sleep(sleeptime)
        count_API()
        return

    with open(variables.API_settings, 'w') as f:
        json.dump(counter, f, indent=4)

def get_micro(micros,start_at):
    """
    """
    for micro in micros:
        fetch_micro(micro=micro, start_at=start_at)

def load_token():
    """
    """
    global headers

    with open(variables.credentials, 'r') as f:
        creds = json.load(f)

    access_token = creds['access_token']
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': f'Bearer {access_token}'
        }

    # return headers

def get_system(start_at=False):
    """
    """
    file = f'{variables.data_path}/enphase.json'
    base_url = f'https://{variables.DOMAIN}'
    url = f"{base_url}/api/v4/systems/{variables.system_id}/telemetry/production_micro"
    fetch_data(url=url,file=file,start_at=start_at)

def fetch_data(url,file,start_at=False):
    count_API()
    if start_at:
        data = {'key': variables.api_key,
                'start_at': start_at,
                'granularity': 'week'
                }
    else:
        data = {'key': variables.api_key,
                # 'start_at': start_at,
                # 'granularity': 'week'
                }
    r = requests.get(url, headers=headers, data=data)
    if r.status_code == 401:
        print('Trying a token refresh')
        refresh_token()
        r = requests.get(url, headers=headers, data=data)

    if r.status_code == 401:
        print('Authentication failed after token refresh')
        print(r.json())

    if r.status_code == 429:
        sleeptime = 60 - datetime.datetime.now().second
        print('Sleeping for', sleeptime,'seconds (is your enphase limit configured correctly?!)')
        time.sleep(sleeptime)
        r = requests.get(url, headers=headers, data=data)

    if r.status_code == 200:
        response = r.json()
        print(f"Saving output to: {file}")
        with open(file, 'w') as f:
            json.dump(response, f, indent=4)
    else:
        print("Sorry, I have no clue what happened, hereby the response")
        print(r.json())

    time.sleep(0.1)

def fetch_micro(micro=variables.all_micros[0], start_at=False):
    file = f'{variables.data_path}/{micro}'
    base_url = f'https://{variables.DOMAIN}'
    url = f"{base_url}/api/v4/systems/{variables.system_id}/devices/micros/{micro}/telemetry"
    fetch_data(url=url,file=file,start_at=start_at)

def refresh_token():
    '''refresh existing token for a new one'''
    with open(variables.credentials, 'r') as f:
        creds = json.load(f)

    refresh_token = creds['refresh_token']

    base64_encoded_clientid_clientsecret = base64.b64encode(str.encode(f'{variables.CLIENT_ID}:{variables.CLIENT_SECRET}'))  # concatenate with : and encode in base64
    base64_encoded_clientid_clientsecret = base64_encoded_clientid_clientsecret.decode('ascii')  # turn bytes object into ascii string
    base_url = f'https://{variables.DOMAIN}'
    url = f"{base_url}/oauth/token"
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': f'Basic {base64_encoded_clientid_clientsecret}'
        }

    data = {'grant_type': 'refresh_token',
            'redirect_uri': variables.REDIRECT_URI,
            'refresh_token': refresh_token,
            'code': variables.auth_code
            }

    count_API()
    r = requests.post(url, headers=headers, data=data)
    response = r.json()

    if response.get('access_token'):
        # don't store creds in plaintext in a real app obviously
        with open(variables.credentials, 'w') as f:
            json.dump(response, f, indent=4)
        load_token()
    else:
        print('There was an error refreshing your access token')
        print(r.text)

def main():
    """
    Examples: 
    to get data of specific micro's:
    enphase.py getmicro <timestamp>(non-optional) serial1 serial2 serial3
    To get data of all micro's and the complete system:
    enphase.py getall <timestamp>(optional, defaults to False)
    To fetch all data of last hour
    enphase.py getall lh 
    Get the system total values of the last hour
    enphase.py getsystem lh 

    """
    args = sys.argv[1:]

    if args[0] == 'refresh_token':
        refresh_token()

    if len(args) > 1:
        if (args[1] == 'lh' or args[1] == 'lasthour' ):
            now = datetime.datetime.now()
            args[1] = int((datetime.datetime.timestamp(now)) - (60*70))
        start_at = args[1]
    else:
        start_at = False

    if len(args) > 2 and args[0] == 'getmicro':
        print(args)
        load_token()
        args.pop(0)
        args.pop(0)
        get_micro(args,start_at)

    elif args[0] == 'getmicros':
        load_token()
        get_micro(variables.all_micros,start_at)

    elif args[0] == 'getsystem':
        load_token()
        get_system(start_at=start_at)

    elif args[0] == 'getall':
        load_token()
        get_system(start_at=start_at)
        get_micro(variables.all_micros,start_at)

    else:
        print("What did you expect?")

if __name__ == '__main__':
    main()  