import logging

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')


def get_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    return stream_handler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_stream_handler())
    return logger
