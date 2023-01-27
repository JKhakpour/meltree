from meltree import listen
from pathlib import Path


class ProgressBar(object):
    progress = 0
    template_path = Path(__file__).name.replace(".py", ".html")

    @listen("progress")
    def set_progress(self, progress):
        self.progress = progress
