import pytest
from common.handlers import (
    handle_ok,
    handle_idx_html_static,
    handle_idx_html_component,
    HTTP_TEST_CONSTS as HTTP_CONSTs,
)


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


def test_register_get(mt):
    mt.get("/")(handle_ok)
    assert mt.http_routes[1].path == "/"
    assert mt.http_routes[1].method == "GET"
    assert mt.http_routes[1].handler is handle_ok


@pytest.mark.parametrize("action", HTTP_CONSTs.actions)
async def test_register_action_direct_hello(action, mt, aiohttp_client):
    handler_registerer = getattr(
        mt.http_server.router,
        f"add_{action}",
    )
    handler_registerer("/", handler=handle_ok)
    cli = await aiohttp_client(mt.http_server)

    resp = await cli.request(action, "/")
    assert resp.status == 200
    text = await resp.text()
    assert HTTP_CONSTs.msg_ok == text
    await cli.close()


@pytest.mark.parametrize("action", HTTP_CONSTs.actions)
async def test_register_http_action_hello(action, mt, aiohttp_client):
    handler_registerer = getattr(mt, action)
    handler_registerer("/")(handle_ok)
    mt.http_server.add_routes(mt.http_routes)
    cli = await aiohttp_client(mt.http_server)

    resp = await cli.request(action, "/")
    assert resp.status == 200
    text = await resp.text()
    assert HTTP_CONSTs.msg_ok == text
    await cli.close()


@pytest.mark.parametrize("action", HTTP_CONSTs.actions)
async def test_register_wrong_action_hello(action, mt, aiohttp_client):
    registered_action = "post" if action == "get" else "get"
    handler_registerer = getattr(mt, registered_action)
    handler_registerer("/")(handle_ok)
    mt.http_server.add_routes(mt.http_routes)
    cli = await aiohttp_client(mt.http_server)

    resp = await cli.request(action, "/")
    assert resp.status == 405
    text = await resp.text()
    assert "Method Not Allowed" in text
    await cli.close()


@pytest.mark.parametrize("action", ["get"])
async def test_register_action_get_template(action, mt, aiohttp_client):
    handler_registerer = getattr(
        mt.http_server.router,
        f"add_{action}",
    )
    handler_registerer("/", handler=handle_idx_html_static)
    cli = await aiohttp_client(mt.http_server)

    resp = await cli.request(action, "/")
    assert resp.status == 200
    text = await resp.text()
    assert "<h1>index_html_ok_static</h1>" in text
    await cli.close()


@pytest.mark.parametrize("action", ["get", "post"])
async def test_register_action_get_template(action, mt, aiohttp_client):
    handler_registerer = getattr(
        mt.http_server.router,
        f"add_{action}",
    )
    handler_registerer("/", handler=handle_idx_html_component)
    cli = await aiohttp_client(mt.http_server)
    resp = await cli.request(action, "/")

    text = await resp.text()
    assert "<title>Meltree Samples</title>" in text
    await cli.close()
