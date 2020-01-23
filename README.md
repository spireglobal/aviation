# Spire Airsafe

This repository hosts some sample programs to help you get up and running with Spire Airsafe APIs. 

Don't hesitate to consult our full API documentation as you go through these examples:

https://developer.airsafe.spire.com/get-started


## Dependencies: 

The example programs require the following libraries in a Python 3.x environment: 

```
1) requests 
2) json 
3) pycurl 
```

## cURL Command Line calling AirSafe datastream:  

Sample syntax for examples under Terminal on macOS systems: 

```
 curl --max-time 30 -H 'Authorization: spire-api-key=xxxxxxxxxxxxxxxxxxxxxxx' https://api.airsafe.spire.com/stream

```

In the example above, you would provide a Spire Airsafe API token in order to access the datastream. In addition, 
--max-time argument can be modified and is only there to show when the client disconnects from the server.  


## cURL Command Line calling AirSafe Historical API:

```
(1) curl -X PUT 'https://api.airsafe.spire.com/archive/job?time_interval=2019-08-12T00:00:00Z/2019-08-13T00:00:00Z' -H 'Authorization: spire-api-key=xxxxxxxxxxxxxxxxxxxxxxx'   -H 'Content-Length: 0'

(2) curl 'https://api.airsafe.spire.com/archive/job?job_id=HZwSA__CSV_0' -H 'Authorization: spire-api-key=xxxxxxxxxxxxxxxxxxxxxxx'

```

In the example above, the cURL query requests data for a one day period by submitting a PUT request. The response from the PUT request (1) returns a job_id. Use the job_id as a query parameter in (2), in our example it is HZwSA__CSV_0. Trigger a GET request and when the job has completed a set of URLs with download URLs is returned from which the data can be retrieved. 

## JSON return data structure of a single 'target_update': 

```
{
  "target": {
    "icao_address": "8007C9",
    "timestamp": "2019-12-03T06:17:58Z",
    "altitude_baro": 7000,
    "heading": 180,
    "speed": 250,
    "latitude": 22.701096,
    "longitude": 88.583213,
    "callsign": "IGO596",
    "vertical_rate": 0,
    "collection_type": "terrestrial",
    "ingestion_time": "2019-12-03T06:18:02Z",
    "tail_number": "VT-IFM",
    "icao_actype": "A320",
    "flight_number": "6E596",
    "origin_airport_icao": "VEGT",
    "destination_airport_icao": "VECC",
    "scheduled_departure_time_utc": "2019-12-03T02:20:00Z",
    "scheduled_departure_time_local": "2019-12-03T07:50:00",
    "scheduled_arrival_time_utc": "2019-12-03T03:50:00Z",
    "scheduled_arrival_time_local": "2019-12-03T09:20:00",
    "estimated_arrival_time_utc": "2019-12-03T06:31:00Z",
    "estimated_arrival_time_local": "2019-12-03T12:01:00"
  }
}

```

## Postman Collections 

Visit the following link to view a Postman Collections on a AirSafe Historical API call: https://www.getpostman.com/collections/b1049989ca7843b36bb4

## Support 

If you encounter any issue, or just want some questions answered, please contact our Customer Experience team at the following email: aviation@spire.com. 



