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
import os
from collections import Counter

# Construct a dataset from an endpoints file
script_dir = os.path.dirname(os.path.abspath(__file__))


def get_mock_data():
    in_file = 'Endpoint100_trivial_3k_repeat.txt'
    with open(os.path.join(script_dir, in_file)) as f:
        endpoints = f.read().splitlines()
        # counter = Counter(endpoints)

        # counter_list = list(counter.keys())
        # print(f'count of counter_list: {len(counter_list)}')
    return endpoints


if __name__ == '__main__':
    get_mock_data()
