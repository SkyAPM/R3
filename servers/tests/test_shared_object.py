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

from collections import defaultdict
from multiprocessing import Process
import pytest

from servers.simple.results_manager import ProxyURIDrainResultsManager, URIDrainResults


def process_function(shared):
    # Access and modify the shared object
    shared.set_dict_field("test", ['a', 'b', 'c'])


def test_shared_object_basic():
    ProxyURIDrainResultsManager.register("URIDrainResults", URIDrainResults)

    manager = ProxyURIDrainResultsManager()
    manager.start()

    shared_object = manager.URIDrainResults()  # It's fine
    assert type(shared_object.get_value()) is defaultdict

    process = Process(target=process_function, args=(shared_object,))

    process.start()
    process.join()

    assert shared_object.get_value() == defaultdict(list, {'test': ['a', 'b', 'c']})

    manager.shutdown()


if __name__ == '__main__':
    pytest.main([__file__])
