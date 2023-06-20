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

import asyncio
from concurrent import futures

import grpc
from google.protobuf.empty_pb2 import Empty

from servers.protos.generated import ai_http_uri_recognition_pb2
from servers.protos.generated import ai_http_uri_recognition_pb2_grpc
from servers.protos.generated.ai_http_uri_recognition_pb2 import Pattern


class HttpUriRecognitionServicer(ai_http_uri_recognition_pb2_grpc.HttpUriRecognitionServiceServicer):
    """
    Algorithm is server side

    TODO: SOREUSEPORT for load balancing? << NOT going to work, its stateful
    """

    def __init__(self, uri_main_queue, shared_results_object):
        super().__init__()
        self.shared_results_object = shared_results_object
        self.uri_main_queue = uri_main_queue

    async def fetchAllPatterns(self, request, context):
        print('-================-')
        print(
            f'> Received fetchAllPatterns request for service <{request.service}>, '
            f'oap side version is: {request.version}')

        version = str(self.shared_results_object.get_version(service=request.service))
        if version == '0':
            version = 'NULL'  # Expected on OAP side, temp fix

        # https://github.com/apache/skywalking/blob/master/oap-server/ai-pipeline/src/main/java/org
        # /apache/skywalking/oap/server/ai/pipeline/services/HttpUriRecognitionService.java#LL39C32-L39C32
        if version == request.version:  # Initial version is NULL
            print('Version match, returning empty response')
            return ai_http_uri_recognition_pb2.HttpUriRecognitionResponse(patterns=[], version=version)

        print(f'Version do not match, local:{version} vs oap:{request.version}')

        patterns = [Pattern(pattern=cluster) for cluster in self.shared_results_object.get_dict_field(request.service)]
        print(f'Returning {len(patterns)} patterns')

        print('-================-')

        return ai_http_uri_recognition_pb2.HttpUriRecognitionResponse(patterns=patterns, version=version)

    async def feedRawData(self, request, context):
        """
        Offload CPU intensive work to a separate process via a queue
        """
        print(f'> Received feedRawData request for service {request.service}')
        uris = [str(uri.name) for uri in request.unrecognizedUris]
        service = str(request.service)
        self.uri_main_queue.put((uris, service))
        return Empty()


async def serve(uri_main_queue, shared_results_object):
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

    ai_http_uri_recognition_pb2_grpc.add_HttpUriRecognitionServiceServicer_to_server(
        HttpUriRecognitionServicer(uri_main_queue=uri_main_queue, shared_results_object=shared_results_object), server)

    server.add_insecure_port('[::]:17128')  # TODO: change to config injection

    await server.start()

    print('Server started!')

    await server.wait_for_termination()  # timeout=5


def run_server(uri_main_queue, shared_results_object):
    asyncio.run(serve(uri_main_queue=uri_main_queue, shared_results_object=shared_results_object))


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
