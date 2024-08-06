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
import multiprocessing
import os
from os.path import dirname

from models.uri_drain.template_miner import load_existing_miners
from models.uri_drain.template_miner_config import TemplateMinerConfig
from servers.simple.results_manager import ProxyURIDrainResultsManager, URIDrainResults
from servers.simple.server import run_server
from servers.simple.worker import run_worker


def run():
    print('Starting server from entrypoint...')
    ProxyURIDrainResultsManager.register("URIDrainResults", URIDrainResults)

    manager = ProxyURIDrainResultsManager()
    manager.start()

    # Load config
    config = TemplateMinerConfig()
    config_file = os.path.join(dirname(__file__), "uri_drain.ini")
    print(f'Searching for config file at {config_file}')
    config.load(config_filename=config_file)  # change to config injection from env or other

    # SET DEBUG HERE! < TODO CONFIG FILE
    shared_results_object = manager.URIDrainResults(debug=False)  # noqa
    uri_main_queue = multiprocessing.Queue()

    # Load existing miner and clusters
    miners = load_existing_miners(config)
    for service in miners:
        shared_results_object.set_dict_field(service=service, value=miners[service].drain.cluster_patterns)

    producer_process = multiprocessing.Process(target=run_server, args=(uri_main_queue, shared_results_object))
    consumer_process = multiprocessing.Process(target=run_worker, args=(uri_main_queue, shared_results_object, config, miners))

    producer_process.start()
    consumer_process.start()

    producer_process.join()
    consumer_process.join()

    manager.shutdown()


if __name__ == "__main__":
    run()
