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
import multiprocessing

from servers.simple.worker import run_worker
from servers.simple.server import run_server
from servers.simple.results_manager import ProxyURIDrainResultsManager, URIDrainResults


def run():
    print('Starting server from entrypoint...')
    ProxyURIDrainResultsManager.register("URIDrainResults", URIDrainResults)

    manager = ProxyURIDrainResultsManager()
    manager.start()

    # SET DEBUG HERE! < TODO CONFIG FILE
    shared_results_object = manager.URIDrainResults(debug=False)  # noqa
    uri_main_queue = multiprocessing.Queue()

    producer_process = multiprocessing.Process(target=run_server, args=(uri_main_queue, shared_results_object))
    consumer_process = multiprocessing.Process(target=run_worker, args=(uri_main_queue, shared_results_object))

    producer_process.start()
    consumer_process.start()

    producer_process.join()
    consumer_process.join()

    manager.shutdown()


if __name__ == "__main__":
    run()
