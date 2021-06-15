import logging


class TestHandler(object):

    def test_imports(self):
        """
        test_imports tests if all necessary packages are installed
        :return:
        """
        import handler
        logger = logging.getLogger()
        tp = handler.TargetProcessor(logger)
        _ = handler.Client("asdf", logger=logger)
