import os
import yaml
import logging
from datetime import datetime, timedelta
import sys
import copy
import json
import csv
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from requests.packages.urllib3.util.retry import Retry

import time

from apscheduler.schedulers.background import BackgroundScheduler
from exceptions import MaxRetries, ConnectionLost

log = logging.getLogger(__name__)

target_updates = []
time_from = None


def reset_bucket():
    global target_updates

    target_updates = []


def export_to_csv_job():
    global time_from
    global target_updates
    # Do the CSV export here

    to_proccess = copy.deepcopy(target_updates)
    old_time_from = copy.deepcopy(time_from)
    time_from = datetime.now()
    reset_bucket()
    if len(to_proccess) > 0:
        print(to_proccess[0])
        data_file = open(
            f"data_{old_time_from.strftime('%m_%d_%Y_%H_%M_%S')}_{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.csv",
            "w",
        )

        # create the csv writer object
        csv_writer = csv.writer(data_file)

        most_keys = max(to_proccess, key=lambda item: len(item.keys()))
        csv_writer.writerow(most_keys.keys())
        for elem in to_proccess:
            csv_writer.writerow(map(lambda key: elem.get(key, ""), most_keys.keys()))
        data_file.close()


def listen_to_stream(timeout=None):
    global time_from
    reset_bucket()
    if timeout is not None:
        timeout = datetime.now() + timedelta(0, timeout)

    scheduler = BackgroundScheduler()
    retry_strategy = Retry(
        # 10 retries before throwing exception
        total=10,
        backoff_factor=3,
        status_forcelist=[429, 500, 502, 503, 504, 422],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    try:
        response = http.get(
            "https://api.airsafe.spire.com/v2/targets/stream?compression=none",
            params={
                "longitude_between": "0.9008789062499999,3.8452148437499996",
                "latitude_between": "48.122101028190805,49.5822260446217",
            },
            headers={"Authorization": f"Bearer {os.environ['AVIATION_TOKEN']}"},
            stream=True,
        )
    except RetryError:
        log.warn(RetryError)
        raise MaxRetries()
    if response.status_code == 401:
        print("Unauthorized, token might be invalid")
        sys.exit()

    try:
        scheduler.add_job(
            export_to_csv_job,
            "cron",
            minute="*/30",
            id="airsafe_stream_csv",
        )
        time_from = datetime.now()
        scheduler.start()
    except Exception as e:
        log.warn(e)
        print("failed to start scheduler")
        raise ConnectionLost()

    try:
        for line in response.iter_lines(decode_unicode=True):
            if timeout is not None and datetime.now() >= timeout:
                scheduler.remove_job("airsafe_stream_csv")
                scheduler.shutdown()
                export_to_csv_job()
                response.close()
                sys.exit()
            if line and '"target":{' in line:
                target = json.loads(line)["target"]
                target_updates.append(target)
    except Exception as e:
        log.warn(e)
        scheduler.remove_job("airsafe_stream_csv")
        scheduler.shutdown()
        export_to_csv_job()
        raise ConnectionLost()


def connection_manager():
    try:
        # If you wish to listen for a specific time:
        # listen_to_stream(70) will listen for 70 seconds
        listen_to_stream()
    except MaxRetries:
        print("stream failed to connect multiple times, will retry in 30mn")
        time.sleep(60 * 30)
        connection_manager()
    except ConnectionLost:
        print("Connection was lost retrying now ...")
        connection_manager()


if __name__ == "__main__":
    config = yaml.load(open("env.yaml"), Loader=yaml.FullLoader)
    os.environ.update(config)

    connection_manager()
