import logging


def setup_logger(name):
    """Get (or create) a logger configured with a single stream handler.

    Guards against duplicate handlers: calling this more than once for the
    same logger name (e.g. module re-import in tests) must not double up
    log lines.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
