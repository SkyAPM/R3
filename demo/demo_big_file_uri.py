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

import json
import logging
import random
import sys
import time
from os.path import dirname
from models.uri_drain.template_miner import TemplateMiner
from models.uri_drain.template_miner_config import TemplateMinerConfig
import tracemalloc

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')

in_log_file = "Endpoint100_trivial.txt"
in_log_file = "Endpoint100_trivial_3k_repeat.txt"
in_log_file = "Endpoint100_trivial_500k_perf_bench.txt"
in_log_file = 'Endpoint200_hard.txt'
config = TemplateMinerConfig()
config.load(dirname(__file__) + "/uri_drain.ini")
config.profiling_enabled = True
template_miner = TemplateMiner(config=config)


def run():
    line_count = 0

    with open(in_log_file) as f:
        lines = f.readlines()
        print('shuffle')
        random.seed(42)
        random.shuffle(lines)

    start_time = time.time()
    batch_start_time = start_time
    batch_size = 10000

    for line in lines:
        line = line.rstrip()
        result = template_miner.add_log_message(line)
        line_count += 1
        if line_count % batch_size == 0:
            time_took = time.time() - batch_start_time
            rate = batch_size / time_took
            logger.info(f"Processing line: {line_count}, rate {rate:.1f} lines/sec, "
                        f"{len(template_miner.drain.clusters)} clusters so far.")
            batch_start_time = time.time()
        if result["change_type"] != "none":
            result_json = json.dumps(result)
            logger.info(f"Input ({line_count}): " + line)
            logger.info("Result: " + result_json)


# starting the memory monitoring
tracemalloc.start()

run()

# displaying the memory
print(tracemalloc.get_traced_memory())
print(f'Memory used by the profiler: peak {tracemalloc.get_traced_memory()[1] / 10 ** 6} MB, '
      f'current {tracemalloc.get_traced_memory()[0] / 10 ** 6}')

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:5]:
    print(stat)

tracemalloc.stop()

sorted_clusters = sorted(template_miner.drain.clusters, key=lambda it: it.size, reverse=True)
print(f'Got {len(sorted_clusters)} clusters')
for cluster in sorted_clusters:
    print(cluster)
    extracted_regex = template_miner._get_template_parameter_extraction_regex(
        cluster.get_template(), exact_matching=True)
    print(f'regex extracted {extracted_regex}')
print("Prefix Tree:")
template_miner.drain.print_tree(max_clusters=1000)

template_miner.profiler.report(0)
