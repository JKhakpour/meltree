import pytest
import asyncio
from meltree import MelTree


@pytest.fixture(autouse=True)
def async_manager():
    print("setup")
    yield "async_manager"

    loop = asyncio.get_event_loop()
    pending = asyncio.all_tasks(loop=loop)
    for task in pending:
        print("cancellingg", task)
        task.cancel()
    group = asyncio.gather(*pending, return_exceptions=True)
    loop.run_until_complete(group)


@pytest.fixture
def mt():
    MelTree.cache = {}
    return MelTree()


@pytest.fixture
def mt_singleton():
    return MelTree()
