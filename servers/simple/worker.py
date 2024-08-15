#  Copyright 2023 SkyAPM org
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
import logger
import queue
import time
from collections import defaultdict

from models.uri_drain.persistence_handler import ServiceFilePersistenceHandler
from models.uri_drain.template_miner import TemplateMiner

logger = logger.init_logger(name=__name__)


def create_defaultdict_with_key(factory):
    class CustomDefaultDict(defaultdict):
        def __missing__(self, key):
            value = factory(key)
            self[key] = value
            return value

    return CustomDefaultDict(lambda key: factory(key))


def run_worker(uri_main_queue, shared_results_object, config, existing_miners):
    drain_instances = create_defaultdict_with_key(lambda key:  # URIDrain instances
                                                  TemplateMiner(ServiceFilePersistenceHandler(config.snapshot_file_dir,
                                                                                              key) if config.snapshot_file_dir else None,
                                                                config))
    for service in existing_miners:
        drain_instances[service] = existing_miners[service]

    counter = 0
    while True:
        try:
            uri_package = uri_main_queue.get()
            logger.info(
                f'currently have drain instances for {len(drain_instances)} services, drain_instances.keys() = {drain_instances.keys()}, '
                f'got uri package of length {len(uri_package[0])} for service <{uri_package[1]}>')
            uris, service = uri_package[0], uri_package[1]
            # print(uri_main_queue.get(timeout=1))
            start_time = time.time()
            for uri in uris:
                drain_instances[service].add_log_message(uri)
            logger.info(f'Processed {len(uris)} uris of service {service} in {time.time() - start_time} seconds')
            patterns = drain_instances[service].drain.cluster_patterns
            shared_results_object.set_dict_field(service=service, value=patterns)  # TODO add version
            # increment here
            counter += 1
        except Exception as e:
            logger.error(f"catch an unexpected error occurred: {e}")
        except queue.Empty:  # TODO Consider queue full
            pass
