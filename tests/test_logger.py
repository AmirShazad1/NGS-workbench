from pipeline.utils.logger import setup_logger


def test_setup_logger_returns_logger_with_handler():
    logger = setup_logger("test.logger.one")
    assert len(logger.handlers) == 1


def test_setup_logger_does_not_duplicate_handlers():
    name = "test.logger.two"
    logger1 = setup_logger(name)
    logger2 = setup_logger(name)
    assert logger1 is logger2
    assert len(logger2.handlers) == 1
