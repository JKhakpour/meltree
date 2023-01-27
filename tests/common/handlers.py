import pytest
from aiohttp import web
from .components.calculator import Calculator
from meltree import MelTree, render_template, emit


class HTTP_TEST_CONSTS:
    msg_ok = "ok"
    actions = ["get", "post", "patch", "delete", "options"]


class ComponentTest:
    attr1 = "test"

    def emiting(self):
        emit("event1", {"foo": "bar"})


async def handle_ok(request):
    return web.Response(text=HTTP_TEST_CONSTS.msg_ok)


async def handle_idx_html_static(request):
    return render_template(
        template_name="index_html_ok_static.html",
        request=request,
        context={
            "components": [],
        },
    )


async def handle_idx_html_component(request):
    calc = Calculator()
    mt = MelTree()
    mt.register_component(calc)

    return render_template(
        template_name="index_http_component.html",
        request=request,
        context={
            "components": [calc],
        },
    )
