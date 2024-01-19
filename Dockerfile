# Copyright 2024 SkyAPM org
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Stage 1: Builder stage with full Python image
FROM python:3.11-slim as final

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the necessary files into the container
COPY . /app

# Build the project with make
RUN python3 -m pip install grpcio-tools packaging \
	&& python3 -m tools.grpc_gen \
    && python3 -m pip install .[all]


# Expose the gRPC service port
EXPOSE 17128

# Set the entrypoint to run the gRPC service
ENTRYPOINT ["python", "-m", "servers.simple.run"]
