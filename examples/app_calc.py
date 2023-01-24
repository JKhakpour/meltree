from meltree import MelTree, render_template, emit
import components

mt = MelTree()

calc = components.Calculator()
mt.register_component(calc)

sio_server = mt.sio_server


@mt.get("/")
async def index(request):
    return render_template(
        template_name="index.html",
        request=request,
        context={
            "components": [calc],
        },
    )


if __name__ == "__main__":
    mt.run()
