import logging
from enum import Enum

import responses
from testfixtures import LogCapture

from client import Client, StreamConfig
from client import ContinueFromPositionToken, FilterMaxAge, FilterLatitude, FilterLate, \
    FilterLongitude, FilterCallSign, FilterAltitude, FilterAirline, FilterTailNumber, FilterIcaoAddress
from client import ErrInvalidToken, ErrServerDisconnected
from client import _STREAM_V2_URL


class T(Enum):
    args = 0
    want = 1
    err = 2


class TestStreamConfig(object):

    def test_add_get(self):
        """
        test_add_get tests the StreamConfig add+get cycle
        :return:
        """
        tests = [
            {
                T.args: [],
                T.want: {}
            }, {
                T.args: [ContinueFromPositionToken('BEGINNING'),
                         FilterMaxAge(15),
                         FilterLatitude(100.0, 120.0),
                         FilterLongitude(170.0, -170.0),
                         FilterLate(False),
                         FilterCallSign(["cs1", "cs2"]),
                         FilterAltitude(10000, 12000),
                         FilterAirline(["airline1", "airline2"]),
                         FilterTailNumber(["tail1", "tail2"]),
                         FilterIcaoAddress(["icao1", "icao2"]),
                         ],
                T.want: {"max_age": "15",
                         "latitude_between": "100.0,120.0",
                         "longitude_between": "170.0,-170.0",
                         "late_filter": "false",
                         "callsign": "cs1,cs2",
                         "altitude_between": "10000,12000",
                         "airline": "airline1,airline2",
                         "tail_number": "tail1,tail2",
                         "icao_address": "icao1,icao2",
                         "position_token": "BEGINNING",
                         }
            }
        ]

        for test in tests:
            cfg = StreamConfig()
            for arg in test[T.args]:
                cfg.add(arg)

            got = cfg.get()
            assert got == test[T.want]


class TestClient(object):
    class CallbackRecorder(object):
        """
        CallbackRecorder offers a callback that simply records all messages that are passed to it
        """
        def __init__(self):
            self.messages = []

        def callback(self, message):
            self.messages.append(message)

    @responses.activate
    def test_stream_unauthorized(self):
        """
        test_stream_unauthorized tests that unauthorized requests are handled correctly
        """
        responses.add(responses.GET, _STREAM_V2_URL, body='{}', status=401)

        c = Client("INVALID_TOKEN")
        r = self.CallbackRecorder()

        raised = False
        try:
            c.stream(r.callback)
        except ErrInvalidToken:
            raised = True

        assert raised

    @responses.activate
    def test_stream_status_callback(self):
        """
        test_stream_status_callback tests that the general callback logs status messages correctly
        """
        responses.add(responses.GET, _STREAM_V2_URL,
                      body="""\
{"status":{"timestamp":"2020-09-07T16:33:10Z","level":"INFO","message":"Welcome to Spire\'s /v2/target/stream","code":100}}
{"status":{"timestamp":"2020-09-07T16:41:12Z","level":"ERROR","message":"Error message","code":300}}
""",
                      status=200)

        with LogCapture() as lc:
            logger = logging.getLogger()

            c = Client("token", logger=logger)
            r = self.CallbackRecorder()

            try:
                c.stream(r.callback, status_message_callback=r.callback)
                assert False  # expected behavior is not to arrive here
            except ErrServerDisconnected:
                pass

            lc.check(
                ('root', 'DEBUG', 'attempting to connect to https://api.airsafe.spire.com/v2/targets/stream'),
                ('root', 'DEBUG', 'connection established'),
                ('root', 'INFO', 'status at 2020-09-07T16:33:10Z: Welcome to Spire\'s /v2/target/stream'),
                ('root', 'ERROR', 'status at 2020-09-07T16:41:12Z: Error message')
            )

    @responses.activate
    def test_stream_position_token_callback(self):
        """
        test_stream_position_token_callback tests that position tokens are handed to the position_token_callback
        """
        responses.add(responses.GET, _STREAM_V2_URL,
                      body='{"position_token":"the=token=="}',
                      status=200)

        with LogCapture() as lc:
            logger = logging.getLogger()

            c = Client("token", logger=logger)
            r = self.CallbackRecorder()

            try:
                c.stream(r.callback, position_token_callback=r.callback)
                assert False  # expected behavior is not to arrive here
            except ErrServerDisconnected:
                pass

            assert r.messages == ["the=token=="]

    @responses.activate
    def test_stream_target_callback(self):
        """
        test_stream_target_callback tests that target updates are handed correctly to the target_callback
        """
        responses.add(responses.GET, _STREAM_V2_URL,
                      body='{"target":{"icao_address": "ADB984"}}',
                      status=200)

        with LogCapture() as lc:
            logger = logging.getLogger()

            c = Client("token", logger=logger)
            r = self.CallbackRecorder()

            try:
                c.stream(r.callback)
                assert False  # expected behavior is not to arrive here
            except ErrServerDisconnected:
                pass

            assert r.messages == [{"icao_address": "ADB984"}]

    @responses.activate
    def test_stream_graceful_disconnect(self):
        """
        test_stream_graceful_disconnect tests that depending on the timeout and message order the client disconnects
        in a graceful or in a hard manner, and that actually no duplicate messages are handed over to the
        target_callback
        """
        tests = [{
            T.args: 0,
            T.want: {"msg": "hard timeout after", "n_targets": 1},
        }, {
            T.args: 1,
            T.want: {"msg": "graceful timeout after", "n_targets": 1}
        }]

        for test in tests:
            responses.add(responses.GET, _STREAM_V2_URL,
                          body="""{"target":{"icao_address": "ADB984"}}
    {"position_token":"the=token=="}
    {"target":{"icao_address": "ADB985"}}""",
                          status=200)

            with LogCapture() as lc:
                logger = logging.getLogger()

                c = Client("token", logger=logger)
                r = self.CallbackRecorder()

                try:
                    c.stream(r.callback, timeout=test[T.args])
                except ErrServerDisconnected:
                    assert False  # here we expect the client to disconnect, not the server
                    pass

                lc.check_present(
                    ('root', 'WARNING',
                     'timeout of {}s might be too low to gracefully time out; recommended values are > 30s'.format(test[T.args])))

                # check that we shut down gracefully
                last_but_one_entry = lc.actual()[-2]
                assert last_but_one_entry[1] == "INFO"
                assert test[T.want]["msg"] in last_but_one_entry[2]
                assert len(r.messages) == test[T.want]["n_targets"]
