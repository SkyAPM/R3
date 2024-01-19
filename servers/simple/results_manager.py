# Copyright 2024 SkyAPM org
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This is a shared drain3 results manager with proxy class.

This probably should be replaced with redis or memcached in serious use cases.
"""
from collections import defaultdict
import multiprocessing.managers as m

import logger


class URIDrainResults:
    """
    https://stackoverflow.com/questions/26499548/accessing-an-attribute-of-a-multiprocessing-proxy-of-a-class
    """

    def __init__(self, debug=False):
        self.results = defaultdict(list)
        self.versions = defaultdict(int)
        self.logger = logger.init_logger(logging_level='DEBUG' if debug else 'INFO', name='URIDrainResults')

    def get_value(self):
        return self.results

    def set_value(self, value):
        self.results = value

    def get_dict_field(self, service):
        return self.results[service]

    def set_dict_field(self, service, value):
        if not self.is_the_same(service, value):

            self.versions[service] += 1
            self.results[service] = value

    def get_version(self, service):
        return self.versions[service]

    def is_the_same(self, service, new_results):
        """
        This is symmetric difference between old and new results
        if the difference set is empty set, then the results are the same
        """
        if logger.logger_debug_enabled:
            self.logger.debug(f'old : {self.results[service]}')
            self.logger.debug(f'new : {new_results}')
            self.logger.debug(f'diff : {set(self.results[service]) ^ set(new_results)}')

        return set(self.results[service]) ^ set(new_results) == set()


class ProxyURIDrainResultsManager(m.BaseManager):
    """Required to create a proxy class for the shared object"""
    pass
