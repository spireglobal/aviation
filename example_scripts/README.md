# Explanation of Airsafe Scripts above

## historicalapi.py

Users can pull this file onto their local machines and enact calls to our Airsafe API out of the box. The only change needed is in line 16 where a valid spire-api-token must be encoded. 

## Flight_tracking.py 

This is a complete client that allows users to connect to our Airsafe Flight Tracking API. The client runs for a specified time N denoted by the user and collects all target_updates for that given time. At the end of the call, the user can see a print out of the target_updates collected and has an option of downloading the return objects as a JSON and/or CSV output file to their local machine. 
