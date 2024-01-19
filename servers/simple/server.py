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

import asyncio
import sys
from collections import defaultdict
from concurrent import futures

import grpc
from google.protobuf.empty_pb2 import Empty

from servers.protos.generated import ai_http_uri_recognition_pb2
from servers.protos.generated import ai_http_uri_recognition_pb2_grpc
from servers.protos.generated.ai_http_uri_recognition_pb2 import Pattern

# put into config file
GRPC_R3_PORT = 17128

class HttpUriRecognitionServicer(ai_http_uri_recognition_pb2_grpc.HttpUriRecognitionServiceServicer):
    """
    Algorithm is server side

    TODO: SOREUSEPORT for load balancing? << NOT going to work, its stateful
    """

    def __init__(self, uri_main_queue, shared_results_object):
        super().__init__()
        self.shared_results_object = shared_results_object
        self.uri_main_queue = uri_main_queue
        self.known_services = defaultdict(int)  # service_name: received_count

    async def fetchAllPatterns(self, request, context):
        # TODO OAP SIDE OR THIS SIDE must save the version, e.g. oap should check if version is > got version,  since
        #  this is a stateful service and it may crash and restart
        print('-================-')
        version = str(self.shared_results_object.get_version(service=request.service))

        print(
            f'> Received fetchAllPatterns request for service {request.service}, '
            f'oap side version is: {request.version}, r3 side version is: {version}')

        if version == '0':
            version = 'NULL'  # OAP side is NULL, so we must not return NULL otherwise it will always be NULL

        # https://github.com/apache/skywalking/blob/master/oap-server/ai-pipeline/src/main/java/org
        # /apache/skywalking/oap/server/ai/pipeline/services/HttpUriRecognitionService.java#LL39C32-L39C32
        if version == request.version:  # Initial version is NULL
            print('Versions match, returning empty response since OAP is already at latest')
            return ai_http_uri_recognition_pb2.HttpUriRecognitionResponse(patterns=[], version=version)

        print(f'Versions not match, local version:{version} vs OAP version:{request.version}, requiring sync')

        cluster_candidates = self.shared_results_object.get_dict_field(request.service)
        patterns = []
        for cluster in cluster_candidates:
            if '{var}' in cluster:
                patterns.append(Pattern(pattern=cluster))
            else:  # TODO this is for post processing feature to be added
                print("Skipping pattern \"{cluster}\" without any \{var\}, OAP won't need this. Check this carefully and see if algorithm is working properly.")
        print(f'Returning {len(patterns)} patterns')

        print('-========Full List of Patterns========-')
        print(p) for p in patterns

        return ai_http_uri_recognition_pb2.HttpUriRecognitionResponse(patterns=patterns, version=version)

    async def feedRawData(self, request, context):
        """
        Offload CPU intensive work to a separate process via a queue

        There will always be a User service, its in topology, but it will not call fetchAllPatterns
        """
        print(f'> Received feedRawData request for service {request.service}, the <User> service will be ignored')
        if request.service == 'User':
            # It should not be called
            return Empty()

        uris = [str(uri.name) for uri in request.unrecognizedUris]
        service = str(request.service)

        # This is an experimental mechanism to avoid identifying non-restful uris unnecessarily.
        self.known_services[service] += len(set(uris))
        if self.known_services[service] < 20:  # This hard-coded as 20 in SkyWalking UI as a heuristic
            print(f'Unique Uri count too low (<20 unique uris) for service {service}, skipping to prevent inaccurate results')
            return Empty()
        print(f'Sending Uris to processing queue, uris {uris}')
        self.uri_main_queue.put((uris, service))
        return Empty()


async def serve(uri_main_queue, shared_results_object):
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

    ai_http_uri_recognition_pb2_grpc.add_HttpUriRecognitionServiceServicer_to_server(
        HttpUriRecognitionServicer(uri_main_queue=uri_main_queue, shared_results_object=shared_results_object), server)


    server.add_insecure_port(f'[::]:{GRPC_R3_PORT}')  # TODO: change to config injection

    await server.start()

    print(f'R3 server started on port {GRPC_R3_PORT}!')

    await server.wait_for_termination()  # timeout=5


def run_server(uri_main_queue, shared_results_object):
    loop = asyncio.get_event_loop()
    try:
        # Here `amain(loop)` is the core coroutine that may spawn any
        # number of tasks
        sys.exit(loop.run_until_complete(serve(uri_main_queue, shared_results_object)))
    except KeyboardInterrupt:
        # Optionally show a message if the shutdown may take a while
        print("Attempting graceful shutdown, press Ctrl+C again to exit…", flush=True)

        quit()
        # TODO Handle interrupt and gracefully shutdown
        """
        Learn from this
        https://stackoverflow.com/questions/30765606/whats-the-correct-way-to-clean-up-after-an-interrupted-event-loop
        """
        # Do not show `asyncio.CancelledError` exceptions during shutdown
        # (a lot of these may be generated, skip this if you prefer to see them)
        def shutdown_exception_handler(loop, context):
            if "exception" not in context \
                    or not isinstance(context["exception"], asyncio.CancelledError):
                loop.default_exception_handler(context)

        loop.set_exception_handler(shutdown_exception_handler)

        # Handle shutdown gracefully by waiting for all tasks to be cancelled
        tasks = asyncio.gather(*asyncio.all_tasks(loop=loop), return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()

        # Keep the event loop running until it is either destroyed or all
        # tasks have really terminated
        while not tasks.done() and not loop.is_closed():
            loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == '__main__':
    run_server(uri_main_queue=None, shared_results_object=None)

# TODO Handle interrupt and gracefully shutdown
"""
try:
    loop.run_forever()
except KeyboardInterrupt:  # pragma: no branch
    pass
finally:
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(app.shutdown())
    loop.run_until_complete(handler.finish_connections(shutdown_timeout))
    loop.run_until_complete(app.cleanup())
loop.close()
"""
