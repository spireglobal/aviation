#Calling AirSafe datastream using PyCurl library.

import pycurl
import json

#Connecting to endpoint below with a 30 second timeout. 
#Integer 30 can be changed and reflects the number of seconds the stream will run for from the time of initial connection.
#Remember, you must replace spire-api-token with your own AirSafe Token for the request to occur successfully. 

STREAM_PARAMETERS = ["https://api.airsafe.spire.com/targets", 30]

class Client:
  def __init__(self):
    self.buffer = ""
    self.conn = pycurl.Curl()
    self.conn.setopt(pycurl.URL, STREAM_PARAMETERS[0])
    self.conn.setopt(pycurl.HTTPHEADER, ['Authorization: spire-api-token','Accept: application/json'])
    self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
    self.conn.setopt(pycurl.TIMEOUT, STREAM_PARAMETERS[1])
    self.conn.perform()

  def on_receive(self, data):
    print(data)
 
if __name__ == '__main__':
    client = Client()

