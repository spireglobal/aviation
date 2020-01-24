#This is an implementation of Spire's AirSafe datastream using the request module. 

import json
import requests
import time

#Stream parameters and API endpoint arguments for call. 
#Remember, you must replace spire-api-token with your own AirSafe Token for the request to occur successfully.
#In list paramaters, [1] index holds the timeout integer for a call and represents the connection time in seconds. 
#Client can change this input variable for however many seconds they want. 

STREAM_URL = "https://test.airsafe.spire.com/stream"
parameters = ['spire-api-token', 10]
headers = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(parameters[0])}

#Will connect to stream for 10 seconds and will print out target_updates to the Terminal for client to view.
def call(token, timeout):
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
    call(parameters[0], parameters[1)
    print('**stream finished!**')
