from meltree import emit
import asyncio
from meltree import MelTree
from pathlib import Path


class LongRunningProcess(object):

    template_path = Path(__file__).name.replace(".py", ".html")

    async def start(self):
        app = MelTree()
        self.value = 0
        sleep_time = 0.5
        step_size = 5
        while self.value < 100:
            await asyncio.sleep(sleep_time)
            self.value += step_size
            await app.sio_server.emit(
                "meld-event", {"event": "progress", "message": {"progress": self.value}}
            )
        await asyncio.sleep(5 * sleep_time)
        await app.sio_server.emit(
            "meld-event", {"event": "progress", "message": {"progress": 0}}
        )
