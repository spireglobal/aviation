#This is an implementation of Spire's AirSafe datastream using the request module. The client will printout 
# satellite and terrestrial target_updates in real-time as ingested into Spire's own data store. 

import json
import requests
import time

#Stream paramters and API endpoint arguments for call. 
STREAM_URL = "https://test.airsafe.spire.com/stream"
parameters = ['spire-api-key', 10]
headers = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(parameters[0])}

#Will connect to stream for 10 seconds and will print out target_updates to the Terminal for client to view.
def call(timeout):
    try:
        timeout = time.time() + timeout
        with requests.get(STREAM_URL, headers=headers, stream=True) as r:
            for line in r.iter_lines(decode_unicode=True):
                if time.time() < timeout:
                    msg = json.loads(line)
                    print(msg)
                else:
                    r.close()
    except AttributeError:
        pass

if __name__ == '__main__':
    call(parameters[1)
    print('**stream finished!**')
