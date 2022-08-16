"""Setup log"""

import logging
import os

def setup_log(name=''):
    """Set up logger"""

    logger = logging.getLogger('oscilok.{}'.format(name))
    logger.setLevel(level=logging.INFO)
    filename = os.getenv('OSCILOK_LOG_FILENAME')

    try:
        handler = logging.FileHandler(filename)
    except TypeError:
        handler = logging.StreamHandler()
    except IsADirectoryError:
        handler = logging.StreamHandler()

    fmt = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    return logger
