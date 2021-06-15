"""
client is a wrapper around api.airsafe.spire.com/v2/targets/stream \
intended to make development of Airsafe stream applications easier.

It exposes certain failure modes via explicit errors, supports \
the creation of filters and makes reconnecting to streams easier.
"""

import http
import json
import logging
import math
import time
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from enum import Enum as _Enum
from typing import Optional, Callable, Dict, List

import requests

_STREAM_V2_URL = "https://api.airsafe.spire.com/v2/targets/stream"

_STATUS_LEVELS_MAP = {
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR
}
_max_time_between_position_tokens = 15
# _min_reasonable_timeout is set a few seconds higher than _max_time_between_position_tokens to ensure delivery of one
# last position token before gracefully timing out.
_min_reasonable_timeout = 2 * _max_time_between_position_tokens


class _StreamParameter(_ABC):
    @_abstractmethod
    def key(self) -> str:
        pass

    @_abstractmethod
    def value(self) -> str:
        pass


class _FilterString(_StreamParameter, _ABC):
    def __init__(self, value: str):
        self._value = value

    def value(self) -> str:
        return "{}".format(self._value)


class ContinueFromPositionToken(_FilterString):
    """
    ContinueFromPositionToken can be added to StreamConfig and implements filter parameter "position_token".
    The position token can take three values:
    - An actual position token that has recently been returned by a previous API call;
    - 'BEGINNING' to start from the oldest still available target update; or
    - 'LATEST' (default) to start receiving target updates as they become available.
    """

    def key(self) -> str:
        return "position_token"


class _FilterInt(_StreamParameter, _ABC):
    def __init__(self, value: int):
        self._value = value

    def value(self) -> str:
        return "{}".format(self._value)


class FilterMaxAge(_FilterInt):
    """
    FilterMaxAge can be added to StreamConfig and implements filter parameter "max_age"
    """

    def key(self) -> str:
        return "max_age"


class _FilterFloatRange(_StreamParameter, _ABC):
    def __init__(self, lower_bound: float, upper_bound: float):
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def value(self) -> str:
        return "{},{}".format(self._lower_bound, self._upper_bound)


class FilterLatitude(_FilterFloatRange):
    """
    FilterLatitude can be added to StreamConfig and implements filter parameter "latitude_between"
    """

    def key(self) -> str:
        return "latitude_between"


class FilterLongitude(_FilterFloatRange):
    """
    FilterLongitude can be added to StreamConfig and implements filter parameter "longitude_between"
    """

    def key(self) -> str:
        return "longitude_between"


class _FilterIntRange(_StreamParameter, _ABC):
    def __init__(self, lower_bound: int, upper_bound: int):
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def value(self) -> str:
        return "{},{}".format(self._lower_bound, self._upper_bound)


class FilterAltitude(_FilterIntRange):
    """
    FilterAltitude can be added to StreamConfig and implements filter parameter "altitude_between"
    """

    def key(self) -> str:
        return "altitude_between"


class _FilterBoolean(_StreamParameter, _ABC):
    def __init__(self, value: bool):
        self._value = value

    def value(self) -> str:
        return json.dumps(self._value)


class FilterLate(_FilterBoolean):
    """
    FilterLate can be added to StreamConfig and implements filter parameter "late_filter"
    """

    def key(self) -> str:
        return "late_filter"


class _FilterStringList(_StreamParameter, _ABC):
    def __init__(self, values: List[str]):
        self._values = values

    def value(self) -> str:
        return ",".join(self._values)


class FilterIcaoAddress(_FilterStringList):
    """
    FilterIcaoAddress can be added to StreamConfig and implements filter parameter "icao_address"
    """

    def key(self) -> str:
        return "icao_address"


class FilterTailNumber(_FilterStringList):
    """
    FilterTailNumber can be added to StreamConfig and implements filter parameter "tail_number"
    """

    def key(self) -> str:
        return "tail_number"


class FilterCallSign(_FilterStringList):
    """
    FilterCallSign can be added to StreamConfig and implements filter parameter "callsign"
    """

    def key(self) -> str:
        return "callsign"


class FilterAirline(_FilterStringList):
    """
    FilterAirline can be added to StreamConfig and implements filter parameter "airline"
    """

    def key(self) -> str:
        return "airline"


class StreamConfig(object):
    """
    StreamConfig is a container that collects all desired filter parameters.
    """

    def __init__(self):
        self._parameters: Dict[str, str] = dict()

    def add(self, parameter: _StreamParameter):
        """
        add adds stream parameters to the stream configuration
        Parameters can include
        - ContinueFromPositionToken; or
        - any class that is prefixed with 'Filter'
        :param parameter: the respective filter or configuration object
        """
        self._parameters[parameter.key()] = parameter.value()

    def get(self):
        """
        get returns the dictionary of all stream parameters
        :return:
        """
        return self._parameters


class _MessageKey(_Enum):
    POSITION_TOKEN = "position_token"
    TARGET = "target"
    STATUS = "status"


class _StatusFields(_Enum):
    TIMESTAMP = "timestamp"
    LEVEL = "level"
    MESSAGE = "message"


class ErrInvalidToken(Exception):
    """
    ErrInvalidToken is raised when the client token is rejected by the stream API (status 401)
    """
    pass


class ErrServerDisconnected(Exception):
    """
    ErrServerDisconnected is raised when the server disconnected the connection e.g. for maintenance events.
    """
    pass


class _Timer(object):
    class ErrTimerUp(Exception):
        pass

    def __init__(self, timeout: Optional[float]):
        self._start_time = time.perf_counter()
        self._timeout = timeout
        if timeout is None:
            self._timeout = math.inf

    def elapsed(self):
        return time.perf_counter() - self._start_time

    def remaining(self):
        return self._timeout - self.elapsed()

    def up(self) -> bool:
        return (time.perf_counter() - self._start_time) > self._timeout


class Client(object):
    """
    Client contains the Airsafe streaming client configuration and is used to call stream()
    """

    def __init__(self, token: str, logger: Optional[logging.Logger] = None, base_url: str = _STREAM_V2_URL):
        """

        :param token: The customer token, issued by the Spire sales team
        :param logger: The custom logger that is used to log debug statements, infos, warnings and errors
        :param base_url: The base url the client will attempt to connect to when stream() is called
        """
        self.token: str = token
        self.logger: logging.Logger = logging.getLogger()
        self.base_url: str = base_url
        if logger is not None:
            self.logger = logger

        self._last_position_token: Optional[str] = None
        self._last_message_type: Optional[_MessageKey] = None

    def _position_token_callback(self, token: str):
        self._last_message_type = _MessageKey.POSITION_TOKEN

        self._last_position_token = token
        self.logger.debug("position_token: {}".format(token))

    def _status_callback(self, status: Dict):
        self._last_message_type = _MessageKey.STATUS

        log_level = _STATUS_LEVELS_MAP[status[_StatusFields.LEVEL.value]]
        message = status[_StatusFields.MESSAGE.value]
        timestamp = status[_StatusFields.TIMESTAMP.value]
        self.logger.log(log_level, "status at {}: {}".format(timestamp, message))

    def _target_callback(self):
        self._last_message_type = _MessageKey.TARGET

    def _general_callback(self, t: _Timer):
        if t.up():
            self.logger.info("hard timeout after {}s".format(t.elapsed()))
            raise _Timer.ErrTimerUp
        if self._last_message_type is not None and \
                self._last_message_type == _MessageKey.POSITION_TOKEN and \
                t.remaining() < _min_reasonable_timeout:
            self.logger.info("graceful timeout after {}s".format(t.elapsed()))
            raise _Timer.ErrTimerUp

    def stream(self,
               target_callback: Callable,
               position_token_callback: Optional[Callable] = None,
               status_message_callback: Optional[Callable] = None,
               config: Optional[StreamConfig] = None,
               timeout: Optional[float] = None,
               graceful_timeout: bool = True) -> Optional[str]:
        """
        stream connects to the stream API, clearly exposes some common error modes, handles graceful timeout for use \
        cases where consumers want to deliberately disconnect, and calls the provided callbacks when the respective \
        messages arrive.
        The API behaviour is optionally configured via a StreamConfig object.
        Per default the client does not time out. If a timeout is provided, the stream attempts to gracefully \
        disconnect i.e. to disconnect right after a position token has been transmitted. This is to avoid the delivery \
        of duplicate messages. A graceful disconnect might not be possible when the timeout is lower than 20s.
        :param target_callback: The function that is called when a target update arrives.
        :param position_token_callback: The function that is called when a position token arrives.
        :param status_message_callback: The function that is called when a status message arrives.
        :param config: A StreamConfig object that defines server-side message filters and restart behavior.
        :param timeout: The timeout in seconds.
        :param graceful_timeout: If True, the client will attempt to disconnect right after a position_token message.
        :return: stream returns the last received position_token or None.
        """

        if timeout is not None and timeout < _min_reasonable_timeout and graceful_timeout:
            self.logger.warning("timeout of {}s might be too low to gracefully time out; "
                                "recommended values are > {}s".format(timeout, _min_reasonable_timeout))
        self.logger.debug("attempting to connect to {}".format(self.base_url))

        timer = _Timer(timeout)
        headers = {'Authorization': 'Bearer {0}'.format(self.token)}
        params = None
        if config is not None:
            params = config.get()
        # Timeout here is connect timeout + read-timeout
        # Read-timeout in this context is the wait-time between bytes sent from the server
        # Keep-alive status messages are sent every 15 seconds if no other messages are available.
        # If no data arrives for much longer than that something failed.
        try:
            with requests.get(self.base_url,
                              params=params,
                              headers=headers,
                              stream=True,
                              timeout=_min_reasonable_timeout) as r:
                if r.status_code == http.HTTPStatus.UNAUTHORIZED:
                    raise ErrInvalidToken(r.json())
                logging.debug("connection established")

                for line in r.iter_lines():
                    decoded_line = line.decode('utf-8')
                    data = json.loads(decoded_line)

                    if _MessageKey.TARGET.value in data.keys():
                        self._target_callback()
                        if target_callback is not None:
                            target_update = data[_MessageKey.TARGET.value]
                            target_callback(target_update)

                    elif _MessageKey.POSITION_TOKEN.value in data.keys():
                        token = data[_MessageKey.POSITION_TOKEN.value]
                        self._position_token_callback(token)
                        if position_token_callback is not None:
                            position_token_callback(token)

                    elif _MessageKey.STATUS.value in data.keys():
                        status = data[_MessageKey.STATUS.value]
                        self._status_callback(status)
                        if status_message_callback is not None:
                            status_message_callback(status)

                    else:
                        self.logger.error("unprocessable message: {}".format(decoded_line))

                    self._general_callback(timer)  # for client-side disconnect (graceful or hard timeout)

            raise ErrServerDisconnected

        except _Timer.ErrTimerUp:
            pass

        self.logger.info("last position_token: {}".format(self._last_position_token))
        return self._last_position_token
