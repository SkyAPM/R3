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
# CVE-2026-40226, CVE-2026-40228 (systemd), CVE-2025-6141 (ncurses), CVE-2026-5704 (tar)
# CVE-2026-2673, CVE-2026-28387, CVE-2026-28388 (openssl 3.5.5-1~deb13u2)
# CVE-2026-34183, CVE-2026-42769, CVE-2026-34181, CVE-2026-42768 (openssl 3.5.6-1~deb13u2)
# CVE-2026-63073, CVE-2026-63076, CVE-2026-63072, CVE-2026-54874, CVE-2026-63074,
# CVE-2026-14456, CVE-2026-63075, CVE-2026-56864, CVE-2026-75803 (openssl 3.5.7-1~deb13u2)
# CVE-2026-34743 (xz-utils/liblzma5 5.8.1-1+deb13u1)
# CVE-2026-13595, CVE-2026-27456, CVE-2026-53612, CVE-2026-53613, CVE-2026-53614,
# CVE-2026-53615 (util-linux family 2.41.5-0+deb13u1)
# CVE-2025-14104 (util-linux 2.41.3-1, already satisfied by 2.41.5-0+deb13u1)
# NOTE: `apt-get upgrade` only upgrades the packages explicitly named below, so every
# package that carries a security fix must be listed here.
RUN apt-get update && apt-get upgrade -y \
    openssl libssl3t64 openssl-provider-legacy liblzma5 \
    util-linux bsdutils libblkid1 liblastlog2-2 libmount1 libsmartcols1 libuuid1 login mount \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the necessary files into the container
COPY . /app

# Build the project with make
# Upgrade pip to >=26.2 to fix CVE-2026-6357, CVE-2026-8643, CVE-2026-13346
# Upgrade setuptools to >=83.0.0 to fix CVE-2025-47273 (path traversal in PackageIndex),
# CVE-2026-23949, CVE-2026-24049, CVE-2026-59890
# Upgrade click to >=8.3.3 to fix CVE-2026-7246
# Upgrade msgpack to >=1.2.1 to fix CVE-2026-57585, GHSA-6v7p-g79w-8964
RUN python3 -m pip install "pip>=26.2" "setuptools>=83.0.0" \
  && python3 -m pip install grpcio-tools==1.80.0 packaging \
	&& python3 -m tools.grpc_gen \
  && python3 -m pip install .[all] "click>=8.3.3" "msgpack>=1.2.1"

# Patch pip's internal vendor SBOM (bom.cdx.json) to reflect the upgraded setuptools version.
# pip bundles a CycloneDX SBOM of its vendored build dependencies; the base Python image ships
# pip with setuptools@70.3.0 recorded there. After upgrading setuptools above we update this
# metadata file so that vulnerability scanners (e.g. trivy) do not report the stale reference.
# This is purely a metadata patch — no functional code changes.
# Fixes: CVE-2025-47273 (setuptools < 78.1.1)
RUN python3 -c "\
import json, sys; \
bom_path = '/usr/local/lib/python3.13/site-packages/pip/_vendor/bom.cdx.json'; \
import importlib.metadata; \
v = importlib.metadata.version('setuptools'); \
data = json.loads(open(bom_path).read()); \
[c.update({'version': v, 'purl': f'pkg:pypi/setuptools@{v}', 'bom-ref': f'pkg:pypi/setuptools@{v}'}) or sys.stderr.write(f'Updated setuptools SBOM ref to {v}\n') for c in data.get('components', []) if c.get('name') == 'setuptools']; \
open(bom_path, 'w').write(json.dumps(data, separators=(',', ':')))"

# Expose the gRPC service port
EXPOSE 17128

# Set the entrypoint to run the gRPC service
ENTRYPOINT ["python", "-m", "servers.simple.run"]
