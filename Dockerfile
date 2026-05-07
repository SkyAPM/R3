# Copyright 2023 SkyAPM org
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
FROM python:3.13-slim as final

ENV PYTHONUNBUFFERED=1

# Upgrade OS packages to pick up security patches:
# CVE-2025-15281, CVE-2026-0861, CVE-2026-0915 (glibc), CVE-2026-2219 (dpkg), CVE-2025-7709 (libsqlite3)
# CVE-2026-40226, CVE-2026-40228 (systemd), CVE-2026-27456 (util-linux), CVE-2025-6141 (ncurses), CVE-2026-5704 (tar)
# CVE-2026-2673, CVE-2026-28387, CVE-2026-28388 (openssl 3.5.5-1~deb13u2), CVE-2026-34743 (xz-utils 5.8.3)
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the necessary files into the container
COPY . /app

# Build the project with make
# Upgrade pip to >=26.1 to fix CVE-2026-6357
RUN python3 -m pip install "pip>=26.1" \
  && python3 -m pip install grpcio-tools==1.80.0 packaging \
	&& python3 -m tools.grpc_gen \
  && python3 -m pip install .[all]

# Expose the gRPC service port
EXPOSE 17128

# Set the entrypoint to run the gRPC service
ENTRYPOINT ["python", "-m", "servers.simple.run"]
