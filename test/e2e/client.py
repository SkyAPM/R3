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
"""
Run this file to get a web demo of the URI Drain algorithm.
"""
import sys

import grpc
import yaml

from servers.protos.generated.ai_http_uri_recognition_pb2 import HttpUriRecognitionRequest, HttpRawUri
from servers.protos.generated.ai_http_uri_recognition_pb2_grpc import HttpUriRecognitionServiceStub

mode = sys.argv[1]
service_name = sys.argv[2]

channel = grpc.insecure_channel('localhost:17128')
stub = HttpUriRecognitionServiceStub(channel)


def feed_data():
    file_path = sys.argv[3]
    with open(file_path, 'r') as file:
        urls = file.readlines()
    stub.feedRawData(
        HttpUriRecognitionRequest(service=service_name, unrecognizedUris=list(map(lambda x: HttpRawUri(name=x), urls))))
    print("ok")


def fetch_data():
    patterns = stub.fetchAllPatterns(HttpUriRecognitionRequest(service=service_name))
    print(yaml.dump(HTTPUriRecognitionResp(sorted([p.pattern for p in patterns.patterns]), patterns.version), Dumper=NoTagDumper))


class HTTPUriRecognitionResp:

    def __init__(self, patterns, version):
        self.patterns = patterns
        self.version = version


class NoTagDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def remove_representer(dumper, data):
    return dumper.represent_dict(data.__dict__)


yaml.add_representer(HTTPUriRecognitionResp, remove_representer, Dumper=NoTagDumper)

if __name__ == '__main__':
    if mode == 'feed':
        feed_data()
    elif mode == 'fetch':
        fetch_data()
