import logging
import string


def get_log_level(log_level='DEBUG'):

    if log_level.upper() == 'INFO':
        level = logging.getLevelName('INFO')
    elif log_level.upper() == 'WARNING':
        level = logging.getLevelName('WARNING')
    elif log_level.upper() == 'ERROR':
        level = logging.getLevelName('ERROR')
    elif log_level.upper() == 'CRITICAL':
        level = logging.getLevelName('CRITICAL')
    else:
        level = logging.getLevelName('DEBUG')

    return level
