from collections import defaultdict
from multiprocessing import Process
import pytest

from servers.simple.results_manager import ProxyURIDrainResultsManager, URIDrainResults


def process_function(shared):
    # Access and modify the shared object
    shared.set_dict_field("test", ['a', 'b', 'c'])


def test_shared_object_basic():
    ProxyURIDrainResultsManager.register("URIDrainResults", URIDrainResults)

    manager = ProxyURIDrainResultsManager()
    manager.start()

    shared_object = manager.URIDrainResults()  # It's fine
    assert type(shared_object.get_value()) is defaultdict

    process = Process(target=process_function, args=(shared_object,))

    process.start()
    process.join()

    assert shared_object.get_value() == defaultdict(list, {'test': ['a', 'b', 'c']})

    manager.shutdown()


if __name__ == '__main__':
    pytest.main([__file__])
