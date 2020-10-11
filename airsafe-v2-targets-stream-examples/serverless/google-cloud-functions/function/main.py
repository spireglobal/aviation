import logging
import os
from typing import Dict, Any, Optional

from google.cloud import storage
from client import Client, StreamConfig, ContinueFromPositionToken
from client import FilterLongitude, FilterLatitude

LAST_POSITION_TOKEN_KEY = "last_position_token"


class TargetProcessor(object):
    def __init__(self, logger):
        self.n_messages = 0
        self.logger = logger

    def callback(self, target_update):
        self.logger.info(target_update)
        self.n_messages += 1


def must_getenv(key) -> str:
    result = os.environ[key]
    if result == "":
        raise EnvironmentError("could not find environment variable {}".format(key))
    return result


def get_last_position_token(storage_client: storage.Client, bucket, key, logger) -> Optional[str]:
    try:
        bucket = storage_client.get_bucket(bucket)
        blob = bucket.get_blob(key)
        last_position_token = blob.download_as_string().decode("UTF-8")
        return last_position_token
    except Exception as e:
        logger.warning("could not get last position_token: {}".format(e))
        return None


def put_last_position_token(storage_client, bucket, key, token, logger):
    try:
        bucket = storage_client.bucket(bucket)
        blob = bucket.blob(key)
        blob.upload_from_string(token)
    except Exception as e:
        logger.warning("could not put last position_token: {}".format(e))


def handler(event: Dict[str, Any]):
    storage_client = storage.Client()
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
    logger.info("event:{}".format(event))

    # Retrieve the AirSafe2 token, and create a client
    TIMEOUT = int(must_getenv("TIMEOUT"))
    AIRSAFE2_TOKEN = must_getenv("AIRSAFE2_TOKEN")
    LAST_POSITION_TOKEN_BUCKET = must_getenv("LAST_POSITION_TOKEN_BUCKET")

    c = Client(AIRSAFE2_TOKEN, logger=logger)

    # Filter for planes that depart or arrive in Atlanta
    cfg = StreamConfig()
    atlanta_lon = (-84.48, -84.38)
    atlanta_lat = (33.60, 33.67)
    cfg.add(FilterLongitude(*atlanta_lon))
    cfg.add(FilterLatitude(*atlanta_lat))

    # Restart the stream from it's last position, if this position is known
    last_position_token = get_last_position_token(storage_client, LAST_POSITION_TOKEN_BUCKET, LAST_POSITION_TOKEN_KEY,
                                                  logger)
    if last_position_token is not None:
        logger.info("starting from position_token: {}".format(last_position_token))
        cfg.add(ContinueFromPositionToken(last_position_token))

    # Create the callback class and start the stream
    tp = TargetProcessor(logger)
    last_position_token = c.stream(tp.callback, config=cfg, timeout=TIMEOUT)

    put_last_position_token(storage_client, LAST_POSITION_TOKEN_BUCKET, LAST_POSITION_TOKEN_KEY, last_position_token,
                            logger)

    return last_position_token
