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
import functools
import time
import queue
import os
from collections import defaultdict
from os.path import dirname

from models.uri_drain.template_miner_config import TemplateMinerConfig
from models.uri_drain.template_miner import TemplateMiner


def run_worker(uri_main_queue, shared_results_object):
    config = TemplateMinerConfig()
    config_file = os.path.join(dirname(__file__), "uri_drain.ini")
    print(f'Searching for config file at {config_file}')
    config.load(config_filename=config_file)  # change to config injection from env or other
    drain_instances = defaultdict(functools.partial(TemplateMiner, None, config))  # URIDrain instances

    counter = 0
    while True:
        try:
            uri_package = uri_main_queue.get()
            print('====================')
            print(f'currently have drain instances for {len(drain_instances)} services')
            print(f'drain_instances.keys() = {drain_instances.keys()}')
            print('-================-')
            uris, service = uri_package[0], uri_package[1]
            # print(uri_main_queue.get(timeout=1))
            print(f'Got uri package of count {len(uri_package[0])} for service {uri_package[1]}')
            start_time = time.time()
            for uri in uris:
                drain_instances[service].add_log_message(uri)
            print(f'Processed {len(uris)} uris in {time.time() - start_time} seconds')
            drain_clusters = drain_instances[service].drain.clusters
            sorted_drain_clusters = sorted(drain_clusters, key=lambda it: it.size, reverse=True)

            drain_clusters_templates = [cluster.get_template() for cluster in sorted_drain_clusters]
            shared_results_object.set_dict_field(service=service, value=drain_clusters_templates)
            # increment here
            counter += 1
            print('-================-')
        except queue.Empty:  # TODO Consider queue full
            pass
