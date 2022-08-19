"""Setup log
To save log to file, please setup OSCILOK_LOG_FILENAME environment variable

export OSCILOK_LOG_FILENAME=/tmp/oscilok.log

"""

import logging
import os
from logging import handlers


def setup_log(name=''):
    """Set up logger"""

    logger = logging.getLogger('oscilok.{}'.format(name))
    logger.setLevel(logging.DEBUG)
    filename = os.getenv('OSCILOK_LOG_FILENAME')
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s')

    try:
        handler = handlers.TimedRotatingFileHandler(filename, when='D', interval=7, backupCount=5)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        err = handlers.RotatingFileHandler(_err_filename(filename), maxBytes=1000000, backupCount=2)
        err.setLevel(logging.ERROR)
        err.setFormatter(formatter)

        logger.addHandler(handler)
        logger.addHandler(err)
    except TypeError:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except IsADirectoryError:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def _err_filename(filename: str) -> str:
    """Get error log filename"""

    if '.' in filename:
        ext = filename.rfind('.')
        return "{}-error{}".format(filename[:ext], filename[ext:])

    return "{}-error".format(filename)
