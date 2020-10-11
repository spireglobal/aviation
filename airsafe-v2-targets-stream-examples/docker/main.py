#!/usr/bin/env python

import logging
import os
import time
from glob import glob
from os import path
from typing import Optional

from client import Client, StreamConfig, ContinueFromPositionToken
from client import FilterLongitude, FilterLatitude


def must_getenv(key) -> str:
    """
    must_getenv raises an EnvironmentError if the environment variable is not set.
    :param key: The name of the environment variable, e.g. HOME
    :return: the value of the environment variable
    """
    result = os.environ[key]
    if result == "":
        raise EnvironmentError("could not find environment variable {}".format(key))
    return result


LAST_POSITION_TOKEN_LOCATION = path.join(must_getenv("HOME"), "position_tokens")


class TargetProcessor(object):
    """
    TargetProcessor contains all logic to forward, write or process the incoming target updates.
    No heavy processing should be done in this place though, since that might lead this /stream consumer
    to fall back in the data stream, which can lead to the server disconnecting.
    """

    def __init__(self, logger):
        self.n_messages = 0
        self.logger = logger

    def callback(self, target_update):
        """
        callback is the function that is passed to the /stream client, and that is called on every
        incoming target update.
        """
        self.logger.info(target_update)
        self.n_messages += 1


class PositionTokenProcessor(object):
    """
    PositionTokenProcessor contains the logic to read and write position tokens, necessary to allow reconnecting
    to /stream the respective point, as to not miss any target updates.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def read_last_position_token(self) -> Optional[str]:
        """
        read_last_position_token reads the last successfully written position_token. This function is relevant when
        reconnecting to /stream. If the previous disconnect was not right after the transmission of the read
        position_token duplicate delivery of some target updates is likely.
        :return: The position token as a string, or None if no token was found
        """
        try:
            tokens = glob(path.join(LAST_POSITION_TOKEN_LOCATION, "token.*.txt"))
            tokens = sorted(tokens)
            if len(tokens) == 0:
                raise Exception("no position tokens found")
            with open(tokens[-1], "r") as f:
                token = f.read()
            return token
        except Exception as e:
            self.logger.warning("could not get last position_token: {}".format(e))
            return None

    def write_last_position_token(self, token):
        """
        write_last_position_token writes the token to a directory of timestamped tokens, and trims old tokens
        from that directory.
        In case writing the token fails or is incomplete the previous token will be picked up by
        `read_last_position_token`, since the newly written token will be prepended to the files, and renamed
        (an atomic operation) when the write was successful.

        :param token: The token to be written to the directory of tokens
        """
        new_token_file_path = path.join(LAST_POSITION_TOKEN_LOCATION, "token.0.txt")
        try:
            with open(new_token_file_path, "w") as f:
                f.write(token)
            os.rename(new_token_file_path,
                      path.join(LAST_POSITION_TOKEN_LOCATION, "token." + str(time.time()) + ".txt"))
            tokens = glob(path.join(LAST_POSITION_TOKEN_LOCATION, "token.*.txt"))
            tokens = sorted(tokens)

            # Remove old tokens
            if len(tokens) > 5:
                for t in tokens[:-5]:
                    os.remove(t)

            self.logger.debug("updated last position_token to " + token)
        except Exception as e:
            self.logger.error("might not have succeeded writing last position_token: {}".format(e))


def main():
    """
    main reads the AirSafe 2 /stream token from the environment, creates a client and s StreamConfig to apply
    a filter around Atlanta Airport, reads the last position token in case of a restart, and starts the stream,
    passing in a TargetProcessor that logs all incoming target updates.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Retrieve the AirSafe2 token, and create a client
    AIRSAFE2_TOKEN = must_getenv("AIRSAFE2_TOKEN")

    c = Client(AIRSAFE2_TOKEN, logger=logger)

    # Filter for planes that depart or arrive in Atlanta
    cfg = StreamConfig()
    atlanta_lon = (-84.48, -84.38)
    atlanta_lat = (33.60, 33.67)
    cfg.add(FilterLongitude(*atlanta_lon))
    cfg.add(FilterLatitude(*atlanta_lat))

    # Restart the stream from it's last position, if this position is known
    ptp = PositionTokenProcessor(logger)
    last_position_token = ptp.read_last_position_token()

    if last_position_token is not None:
        logger.info("starting from position_token: {}".format(last_position_token))
        cfg.add(ContinueFromPositionToken(last_position_token))

    # Create the callback class and start the stream
    tp = TargetProcessor(logger)
    c.stream(tp.callback,
             position_token_callback=ptp.write_last_position_token,
             config=cfg)

    return 0


if __name__ == "__main__":
    main()
