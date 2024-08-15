# SPDX-License-Identifier: MIT
import base64
import os
from abc import ABC, abstractmethod
from pathlib import Path


class PersistenceHandler(ABC):

    @abstractmethod
    def save_state(self, state):
        pass

    @abstractmethod
    def load_state(self):
        pass

    @abstractmethod
    def get_service(self):
        pass


class ServiceFilePersistenceHandler(PersistenceHandler):

    def __init__(self, base_dir, service):
        self.service_name = service
        self.file_path = os.path.join(base_dir, 'services', base64.b64encode(service.encode('utf-8')).decode('utf-8'))
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def save_state(self, state):
        with open(self.file_path, 'wb') as file:
            file.write(state)

    def load_state(self):
        with open(self.file_path, 'rb') as file:
            return file.read()

    def get_service(self):
        return self.service_name


class ServicePersistentLoader:

    def __init__(self, base_dir):
        self.file_path = os.path.join(base_dir, 'services')

    def load_services(self):
        services = []
        if os.path.isdir(self.file_path):
            for entry in os.listdir(self.file_path):
                if os.path.isfile(os.path.join(self.file_path, entry)):
                    services.append(base64.b64decode(entry.encode('utf-8')).decode('utf-8'))
        return services
