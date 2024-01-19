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
import logging
import os
import time

import grpc
from google.protobuf.empty_pb2 import Empty

from servers.protos.generated import ai_http_uri_recognition_pb2
from servers.protos.generated import ai_http_uri_recognition_pb2_grpc
from servers.protos.generated.ai_http_uri_recognition_pb2 import HttpUriRecognitionRequest, HttpRawUri

os.environ['PYTHONDEVMODE'] = '1'

"""
-------------- WAITING FOR SENDING 1000 SERVICES ---------------
Sending mock data size = 3000, from service = test_service_0
Sending mock data size = 3000, from service = test_service_1
Sending mock data size = 3000, from service = test_service_2
Sending mock data size = 3000, from service = test_service_3
Sending mock data size = 3000, from service = test_service_4
Sending mock data size = 3000, from service = test_service_5
Sending mock data size = 3000, from service = test_service_6
Sending mock data size = 3000, from service = test_service_7
Sending mock data size = 3000, from service = test_service_8
Sending mock data size = 3000, from service = test_service_9
Sending mock data size = 3000, from service = test_service_10
Sending mock data size = 3000, from service = test_service_11
Sending mock data size = 3000, from service = test_service_12
Sending mock data size = 3000, from service = test_service_13
Sending mock data size = 3000, from service = test_service_14
Sending mock data size = 3000, from service = test_service_15
Sending mock data size = 3000, from service = test_service_16
Sending mock data size = 3000, from service = test_service_17
Sending mock data size = 3000, from service = test_service_18
Sending mock data size = 3000, from service = test_service_19
Sending mock data size = 3000, from service = test_service_20
Sending mock data size = 3000, from service = test_service_21
Sending mock data size = 3000, from service = test_service_22
Sending mock data size = 3000, from service = test_service_23
Sending mock data size = 3000, from service = test_service_24
Sending mock data size = 3000, from service = test_service_25
Sending mock data size = 3000, from service = test_service_26
Sending mock data size = 3000, from service = test_service_27
Sending mock data size = 3000, from service = test_service_28
Sending mock data size = 3000, from service = test_service_29
Sending mock data size = 3000, from service = test_service_30
Sending mock data size = 3000, from service = test_service_31
Sending mock data size = 3000, from service = test_service_32
Sending mock data size = 3000, from service = test_service_33
Sending mock data size = 3000, from service = test_service_34
Sending mock data size = 3000, from service = test_service_35
Sending mock data size = 3000, from service = test_service_36
Sending mock data size = 3000, from service = test_service_37
Sending mock data size = 3000, from service = test_service_38
Sending mock data size = 3000, from service = test_service_39
Sending mock data size = 3000, from service = test_service_40
Sending mock data size = 3000, from service = test_service_41
Sending mock data size = 3000, from service = test_service_42
Sending mock data size = 3000, from service = test_service_43
Sending mock data size = 3000, from service = test_service_44
Sending mock data size = 3000, from service = test_service_45
Sending mock data size = 3000, from service = test_service_46
Sending mock data size = 3000, from service = test_service_47
Sending mock data size = 3000, from service = test_service_48
Sending mock data size = 3000, from service = test_service_49
Sending mock data size = 3000, from service = test_service_50
Sending mock data size = 3000, from service = test_service_51
Sending mock data size = 3000, from service = test_service_52
Sending mock data size = 3000, from service = test_service_53
Sending mock data size = 3000, from service = test_service_54
Sending mock data size = 3000, from service = test_service_55
Sending mock data size = 3000, from service = test_service_56
Sending mock data size = 3000, from service = test_service_57
Sending mock data size = 3000, from service = test_service_58
Sending mock data size = 3000, from service = test_service_59
Sending mock data size = 3000, from service = test_service_60
Sending mock data size = 3000, from service = test_service_61
Sending mock data size = 3000, from service = test_service_62
Sending mock data size = 3000, from service = test_service_63
Sending mock data size = 3000, from service = test_service_64
Sending mock data size = 3000, from service = test_service_65
Sending mock data size = 3000, from service = test_service_66
Sending mock data size = 3000, from service = test_service_67
Sending mock data size = 3000, from service = test_service_68
Sending mock data size = 3000, from service = test_service_69
Sending mock data size = 3000, from service = test_service_70
Sending mock data size = 3000, from service = test_service_71
Sending mock data size = 3000, from service = test_service_72
Sending mock data size = 3000, from service = test_service_73
Sending mock data size = 3000, from service = test_service_74
Sending mock data size = 3000, from service = test_service_75
Sending mock data size = 3000, from service = test_service_76
Sending mock data size = 3000, from service = test_service_77
Sending mock data size = 3000, from service = test_service_78
Sending mock data size = 3000, from service = test_service_79
Sending mock data size = 3000, from service = test_service_80
Sending mock data size = 3000, from service = test_service_81
Sending mock data size = 3000, from service = test_service_82
Sending mock data size = 3000, from service = test_service_83
Sending mock data size = 3000, from service = test_service_84
Sending mock data size = 3000, from service = test_service_85
Sending mock data size = 3000, from service = test_service_86
Sending mock data size = 3000, from service = test_service_87
Sending mock data size = 3000, from service = test_service_88
Sending mock data size = 3000, from service = test_service_89
Sending mock data size = 3000, from service = test_service_90
Sending mock data size = 3000, from service = test_service_91
Sending mock data size = 3000, from service = test_service_92
Sending mock data size = 3000, from service = test_service_93
Sending mock data size = 3000, from service = test_service_94
Sending mock data size = 3000, from service = test_service_95
Sending mock data size = 3000, from service = test_service_96
Sending mock data size = 3000, from service = test_service_97
Sending mock data size = 3000, from service = test_service_98
Sending mock data size = 3000, from service = test_service_99
feedRawData Time = 0.4846012592315674 seconds
-------------- WAITING FOR FETCHING PATTERN ---------------
FetchAllPatterns Total Time = 3.1104543209075928 seconds
-------------- Done ---------------

Process finished with exit code 0

"""


async def run() -> None:
    async with grpc.aio.insecure_channel('localhost:17128') as channel:
        stub = ai_http_uri_recognition_pb2_grpc.HttpUriRecognitionServiceStub(channel)

        from dataset_constructor import get_mock_data

        start_time = time.time()
        print('-------------- WAITING FOR SENDING 1000 SERVICES ---------------')

        for i in range(10):
            mock_data_list = get_mock_data()
            unrecognized_uris = [HttpRawUri(name=uri) for uri in mock_data_list]
            mock_service_list = f'test_service_{i}'
            mock_data = HttpUriRecognitionRequest(
                service=mock_service_list,
                unrecognizedUris=unrecognized_uris,
            )
            print(f'Sending mock data size = {len(mock_data_list)}, from service = {mock_data.service}')
            res = await stub.feedRawData(mock_data)
            assert type(res) == Empty
        print(f'feedRawData Time = {time.time() - start_time} seconds')

        print('-------------- WAITING FOR FETCHING PATTERN ---------------')
        time.sleep(1)
        start = time.time()
        for i in range(10):
            request = ai_http_uri_recognition_pb2.HttpUriRecognitionSyncRequest(
                service=f'test_service_{i}',
                version='NULL',
            )
            response = await stub.fetchAllPatterns(request=request)
            assert hasattr(response, 'patterns') is True
            if response.version == 'NULL':
                await asyncio.sleep(0.1)
                await stub.fetchAllPatterns(request=request)
            # print(f'FetchAllPatterns Response for service {i} = {response}')

        print(f'FetchAllPatterns Total Time = {time.time() - start} seconds')

        print('-------------- Done ---------------')


async def main():
    task1 = asyncio.create_task(
        run())

    await task1


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
