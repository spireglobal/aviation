import os
import yaml
import requests
import json
import pandas as pd
from geopy import distance
from colorama import init, Fore, Style, Back
import reverse_geocoder as rg


if __name__ == "__main__":
    init()

    config = yaml.load(open("env.yaml"), Loader=yaml.FullLoader)
    os.environ.update(config)

    # Finding target updates around CDG airport
    print(Fore.YELLOW + f"Loading the datapoints at the airport ...")
    resp = requests.get(
        "https://api.airsafe.spire.com/v2/targets/history",
        params={
            "start": "2021-04-20T12:00:00Z",
            "end": "2021-04-20T18:30:00Z",
            # Coordinates around CDG airport
            "longitude_between": "2.481443,2.642431",
            "latitude_between": "48.970752,49.041694",
        },
        headers={"Authorization": f"Bearer {os.environ['AVIATION_TOKEN']}"},
    )

    if resp.status_code == 401:
        print(Style.RESET_ALL + Fore.RED + "invalid token.")
        exit()
    else:
        data = []
        for line in resp.iter_lines(decode_unicode=True):
            if line and '"target":{' in line:
                data.append(json.loads(line)["target"])
        df = pd.DataFrame(data)

    # Find a target update that fits the route we are interested in
    flight_analysed = df[
        (df.arrival_airport_iata == "CDG") & (df.departure_airport_iata == "LHR")
    ]

    # If we have a flight fitting the destination/arrival we want
    if not flight_analysed.empty:
        print(Fore.YELLOW + f"A flight has been found, loading flight path ...")
        print(
            Style.RESET_ALL + Fore.GREEN + f"Flight number:" + Style.RESET_ALL,
            Back.RED + f"{flight_analysed.iloc[0]['flight_number']}",
        )
        print(
            Style.RESET_ALL + Fore.GREEN + f"Flight from/to:" + Style.RESET_ALL,
            Back.RED
            + f"{flight_analysed.iloc[0]['departure_airport_iata']}/{flight_analysed.iloc[0]['arrival_airport_iata']}",
        )
        print(
            Style.RESET_ALL + Fore.GREEN + f"Flight scheduled time:" + Style.RESET_ALL,
            Back.RED
            + f"{flight_analysed.iloc[0]['departure_scheduled_time']} - {flight_analysed.iloc[0]['arrival_scheduled_time']}",
        )
        # Requesting flight path for the ICAO address during the specified flight period
        resp = requests.get(
            "https://api.airsafe.spire.com/v2/targets/history",
            params={
                "start": flight_analysed.iloc[0]["departure_scheduled_time"],
                "end": flight_analysed.iloc[0]["arrival_scheduled_time"],
                # Tracking the icao address of this aircraft only
                "icao_address": flight_analysed.iloc[0]["icao_address"],
            },
            headers={"Authorization": f"Bearer {os.environ['AVIATION_TOKEN']}"},
        )

        data = []
        for line in resp.iter_lines(decode_unicode=True):
            if line and '"target":{' in line:
                data.append(json.loads(line)["target"])
        df = pd.DataFrame(data)

        print(
            Style.RESET_ALL + Fore.GREEN + f"Datapoints found:" + Style.RESET_ALL,
            Back.RED + f"{len(df.index)}",
        )
        print(Style.RESET_ALL)
        print(
            f"Earliest point found at: {df['timestamp'].head(1).to_string(index=False)}"
        )
        print(
            f"Latest point found at: {df['timestamp'].tail(1).to_string(index=False)}"
        )

        total_distance_km = 0

        row_iterator = df.iterrows()
        _, last = next(row_iterator)
        coordinates = []
        for i, row in row_iterator:
            coord_last = (last["latitude"], last["longitude"])
            coordinates.append(coord_last)
            coord_current = (row["latitude"], row["longitude"])
            last = row
            # Using geopy and the geodesic distance between 2 points, we can calculate the total distance
            total_distance_km += distance.distance(coord_last, coord_current).km
        coordinates.append(coord_current)

        print(Style.RESET_ALL)
        # We can now check the countries flown by by using a reverse offline geocoder
        results = rg.search(coordinates)
        df = pd.DataFrame(results)
        print(Fore.GREEN + f"Countries flown:" + Style.RESET_ALL, df["cc"].unique())

        print(Style.RESET_ALL)
        print(
            Fore.GREEN + f"\bTotal distance flown:" + Style.RESET_ALL,
            Back.RED + f"{total_distance_km} km",
        )
    else:
        print(Style.RESET_ALL + Fore.RED + "Have not found the flight path.")
        exit()
