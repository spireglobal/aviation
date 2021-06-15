import os
import yaml
import json
import requests
import csv

if __name__ == "__main__":
    config = yaml.load(open("env.yaml"), Loader=yaml.FullLoader)
    os.environ.update(config)

    response = requests.get(
        "https://api.airsafe.spire.com/v2/targets/history",
        params={
            "longitude_between": "0.9008789062499999,3.8452148437499996",
            "latitude_between": "48.122101028190805,49.5822260446217",
            "start": "2021-05-21T12:00:00Z",
            "end": "2021-05-21T15:59:59Z",
        },
        headers={"Authorization": f"Bearer {os.environ['AVIATION_TOKEN']}"},
    )

    data_file = open("data.csv", "w")

    # create the csv writer object
    csv_writer = csv.writer(data_file)

    data = []
    for line in response.iter_lines(decode_unicode=True):
        if line:
            data.append(json.loads(line)["target"])
    most_keys = max(data, key=lambda item: len(item.keys()))
    csv_writer.writerow(most_keys.keys())
    for elem in data:
        csv_writer.writerow(map(lambda key: elem.get(key, ""), most_keys.keys()))
    data_file.close()
