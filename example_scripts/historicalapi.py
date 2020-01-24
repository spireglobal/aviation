#This example script is to demonstrate a call to the AirSafe Historical API and will output a CSV file with the query 
#paramaters defined in variable URL. 

import requests
import time
import json

#calling Spire historical api, we must do a PUT request and then a GET request.

def putRequest():

    #Remember, you must replace spire-api-token with your own AirSafe Token for the request to occur successfully.
    
    url = 'https://api.airsafe.spire.com/archive/job?time_interval=2019-09-01T00:00:00Z/2019-09-01T00:02:00Z&out_format=CSV'
    api_token =  'spire-api-token'
    headers = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(api_token)}

    #getting job_id for current call using put request
    response = requests.put(url, headers = headers)
    putRes = response.content
    data = json.loads(putRes)
    job_id = data['job_id']
    job_state = data['job_state']
    print('API job id:', job_id)
    return [job_state, job_id, api_token, headers]

def getRequest():

    #using job_id from function above, and waiting until server resource sends back 'DONE'
    dataget = putRequest()
    data1 = dataget[0]
    job_id = dataget[1]
    wait_time = 0

    while data1 != 'DONE':
        wait_time += 15
        time.sleep(wait_time)
        url_get = 'https://api.airsafe.spire.com/archive/job?job_id=' + job_id
        headers_get = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(dataget[2])}
        response_get = requests.get(url_get, headers = dataget[3])
        data = json.loads(response_get.text)
        data1 = data['job_state']
        print('Job State: ', data1)
    #With the returned URL, send a GET request to download data
        if data1 == 'DONE':
            dataurl = data['download_urls']
            dl_url = dataurl[0]
            print(dataurl)
            print(dataurl[0])
    #Get request to download data from URL and output it to a CSV file in current working directory.
            r = requests.get(dl_url, allow_redirects=True)
            file = open('spiredatatest.csv', 'wb').write(r.content)

if __name__ == '__main__':
    getRequest()
    f = open('spiredatatest.csv', 'r')
    print('Filename:', f.name)
