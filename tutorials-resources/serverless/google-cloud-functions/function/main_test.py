import logging


class TestHandler(object):

    def test_imports(self):
        """
        test_imports tests if all necessary packages are installed
        :return:
        """
        import main
        logger = logging.getLogger()
        _ = main.TargetProcessor(logger)
        _ = main.Client("asdf", logger=logger)
