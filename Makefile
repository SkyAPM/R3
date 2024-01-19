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

VERSION ?= next

# determine host platform
ifeq ($(OS),Windows_NT)
    OS := Windows
else ifeq ($(shell uname -s),Darwin)
    OS := Darwin
else
    OS := $(shell sh -c 'uname 2>/dev/null || echo Unknown')
endif

.PHONY: all
gen:
	poetry run python -m tools.grpc_gen

.PHONY: env
env: poetry gen
	poetry install --all-extras
	poetry run pip install --upgrade pip

.PHONY: poetry poetry-fallback
# poetry installer may not work on macOS's default python
# falls back to pipx installer
poetry-fallback:
	python3 -m pip install --user pipx
	python3 -m pipx ensurepath
	pipx install poetry
	pipx upgrade poetry

poetry:
ifeq ($(OS),Windows)
	-powershell (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
	poetry self update
else
	-curl -sSL https://install.python-poetry.org | python3 -
	export PATH="$HOME/.local/bin:$PATH"
	poetry self update || $(MAKE) poetry-fallback
endif

.PHONY: gen-basic
gen-basic:
	python3 -m pip install grpcio-tools packaging
	python3 -m tools.grpc_gen

.PHONY: install
install: gen-basic
	python3 -m pip install --upgrade pip
	python3 -m pip install .[all]

.PHONY: lint
# flake8 configurations should go to the file setup.cfg E1101 must be checked in future (need upstream change of DrainBase)
lint: clean
	poetry run flake8 models/uri_drain
	poetry run pylint --disable=all --enable=E0602,E0603 models deploy benchmarks tests

.PHONY: fix
# fix problems described in CodingStyle.md - verify outcome with extra care
fix:
	poetry run unify -r --in-place .
	poetry run flynt -tc -v .

.PHONY: license
license: clean
	docker run -it --rm -v $(shell pwd):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:20da317d1ad158e79e24355fdc28f53370e94c8a header check

.PHONY: package
package: clean gen
	poetry build

.PHONY: upload-test
upload-test: package
	poetry run twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: upload
upload: package
	poetry run twine upload dist/*

.PHONY: clean
# FIXME change to python based so we can run on windows
clean:
ifeq ($(OS),Windows)
	if exist rd /s /q dist build
	if exist rd /s /q r3*.tgz*
	for /r %%G in (__pycache__) do @if exist "%%G" rd /s /q "%%G"
	for /r %%G in (.pytest_cache) do @if exist "%%G" rd /s /q "%%G"
	for /r %%G in (*.pyc) do @if exist "%%G" del /q "%%G"
else
	rm -rf dist build
	rm -rf r3*.tgz*
	find . -name "__pycache__" -exec rm -r {} +
	find . -name ".pytest_cache" -exec rm -r {} +
	find . -name "*.pyc" -exec rm -r {} +
endif