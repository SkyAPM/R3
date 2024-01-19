#  Copyright 2024 SkyAPM org
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging

# The following is for performance,
# do not log debug messages if False
logger_debug_enabled = False


def get_logger(name=None):  # noqa
    _logger = logging.getLogger(name)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    _logger.addHandler(ch)
    _logger.propagate = False

    return _logger


def init_logger(logging_level='INFO', name=__name__):
    """
    Initialize the logger given a logging level and a name.
    :param name: name of the caller
    :param logging_level: level of the logger
    :return:
    >>> init_logger()
    <Logger logger (INFO)>
    """
    logger = get_logger(name=name)

    global logger_debug_enabled
    logging.addLevelName(logging.CRITICAL + 10, 'OFF')
    logger.setLevel(logging.getLevelName(logging_level))
    logger_debug_enabled = logger.isEnabledFor(logging.DEBUG)

    logger.info(f'Logger {name} initialized with level {logging_level}')
    return logger


if __name__ == '__main__':
    import doctest
    doctest.testmod()
