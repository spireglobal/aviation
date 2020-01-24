#Calling AirSafe datastream using PyCurl library.

import pycurl
import json

#Connecting to endpoint below with a 30 second timeout. 

STREAM_PARAMETERS = ["https://api.airsafe.spire.com/targets", 30]

class Client:
  def __init__(self):
    self.buffer = ""
    self.conn = pycurl.Curl()
    self.conn.setopt(pycurl.URL, STREAM_PARAMETERS[0])
    self.conn.setopt(pycurl.HTTPHEADER, ['Authorization: tyCQAR7dW6h89ului0Ng2dDLL16JMFxR','Accept: application/json'])
    self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
    self.conn.setopt(pycurl.TIMEOUT, STREAM_PARAMETERS[1])
    self.conn.perform()

  def on_receive(self, data):
    print(data)

client = Client()
