import components
from pathlib import Path

from meltree import MelTree, render_template, emit

mt = MelTree()

lrp = components.LongRunningProcess()
mt.register_component(lrp)

pbar = components.ProgressBar()
mt.register_component(pbar)

mt.add_static("/static", Path(__file__).parent / "static")

@mt.get("/")
async def index(request):
    return render_template(
        template_name="index.html",
        request=request,
        context={
            "components": [lrp, pbar],
        },
    )


if __name__ == "__main__":
    mt.run()
