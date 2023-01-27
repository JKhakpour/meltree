import os
import logging
import socketio
import aiohttp
import asyncio
from uuid import uuid4
from pathlib import Path

from functools import partial
from meltree.tag import MeldTag
from meltree.message import process_message
from jinja2 import FileSystemLoader

from aiohttp_jinja2 import (
    template,
    setup as aio_jinja_setup,
)
from meltree.component import ComponentProxy


class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, app_name="MelTree", *args, **kwargs):
        key = tuple(app_name, *args)
        try:
            return self.cache[key]
        except KeyError:
            value = self.func(*args, **kwargs)
            self.cache[key] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args, **kwargs)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)


class MelTreeHTTP(object):
    """
    A superclass of MelTree for handling HTTP calls.

    Attributes
    ----------
    logger :
        logger instance.
    http_server :
        AIOHTTP HTTP Server class
    """

    http_server = None
    http_routes = None
    logger = None
    _name = None
    __cache = {}

    def __init__(self, app_name="MelTree", *args, **kwargs):
        self._name = app_name
        self._gen_http_srv()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(name=app_name)

    def get(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP GET decorator for specified `path`
        """
        return self.http_routes.get(path, **kwargs)

    def head(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP HEAD decorator for specified `path`
        """
        return self.http_routes.head(path, **kwargs)

    def post(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP POST decorator for specified `path`
        """
        return self.http_routes.post(path, **kwargs)

    def put(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP PUT decorator for specified `path`
        """
        return self.http_routes.post(path, **kwargs)

    def patch(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP PATCH decorator for specified `path`
        """
        return self.http_routes.patch(path, **kwargs)

    def delete(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP DELETE decorator for specified `path`
        """
        return self.http_routes.delete(path, **kwargs)

    def options(self, path, **kwargs):
        """
        AIOHTTP Servers HTTP OPTIONS decorator for specified `path`
        """
        return self.http_routes.options(path, **kwargs)

    def add_static(self, prefix, path, **kwargs):
        """
        Add static folders relative `path` to match with `prefix` in url path
        """
        self.http_routes.static(prefix, path, **kwargs)

    def _gen_http_srv(self):
        """
        called on object init. creates AIOHTTP web application and configures it
        """
        self.http_server = aiohttp.web.Application()
        self.http_routes = aiohttp.web.RouteTableDef()

        self.add_static(
            "/meltree_static", Path(__file__).parent / "static/meltree_static"
        )

        aio_jinja_setup(
            self.http_server,
            loader=FileSystemLoader(Path(os.getcwd()) / "templates"),
            extensions=[MeldTag(self)],
        )

    def run(self, log_level=None, presenter=("eel",)):
        """
        Run this object as a web application.

        Parameters
        ----------
        log_level : int
            logging log level items
        presenter : list[str]
            list of viewers to try loading the gui
        """
        self.log_level = log_level
        if log_level is not None:
            self.logger.setLevel(log_level)

        self.http_server.add_routes(self.http_routes)
        presenter = presenter or []
        if "eel" in presenter:
            try:
                import eel

                # open browser. we have to make a small hack into eel
                # and prevent it's local web server running
                eel._start_args.update({"size": (300, 500), "port": 8080})
                eel.show("")
            except Exception as e:
                self.logger.exception(e)

        aiohttp.web.run_app(self.http_server)


class MelTree(MelTreeHTTP):
    """
    MelTree object to use for generating the gui
    """

    sio_server = None
    sid = None
    _components = None

    def __init__(self, app_name="MelTree", *args, **kwargs):
        super(BaseComponents.MelTree, self).__init__(app_name=app_name)
        self._gen_sio_srv()
        self._components = {}
        self.sio_server.attach(self.http_server)
        self.loop = asyncio.get_event_loop()

        self.http_server.on_shutdown.append(self.on_shutdown)

    def emit(self, event_name: str, **kwargs):
        """
        Emit a custom event which will call any Component methods with the `@listen`
        decorator that are listening for the given event. Keyword arguments to this
        function are passed as keyword arguments to each of the decorated methods.

        Params:
            event_name (str): The name of the custom event to emit.
            **kwargs: Arguments to be passed as keyword arguments to the listening
                methods.
        """

        async def _emit():
            await sio_server.emit(
                "meld-event", {"event": event_name, "message": kwargs}
            )

        sio_server = self.sio_server
        self.loop.call_soon_threadsafe(_emit)

    def on_event(self, event, handler=None, namespace=None):
        """
        listen for SocketIO `event` name
        """
        return self.sio_server.on(event=event, handler=handler, namespace=namespace)

    def get_component(self, cid):
        """
        Get a component class based on a component name.
        """
        try:
            return self._components[cid]
        except KeyError as err:
            self.logger.exception(err)

    def register_component(self, obj, cid=None):
        component = ComponentProxy(obj)

        if cid is None:
            cid = uuid4()
        cid = f"{ obj.__class__.__name__ }:{ cid }"
        component.cid = cid

        obj_id = id(obj)
        self._components[cid] = self._components[obj_id] = component

    def _gen_sio_srv(self):
        """
        Called on object init. Creates SocketIO handler for the object
        """
        self.sio_server = socketio.AsyncServer(
            async_mode="aiohttp",
            logger=self.logger,
            # engineio_logger=True, ##TODO: INFO floods the log api
            always_connect=True,
        )

        @self.on_event("meld-message")
        async def meld_message(sid, message):
            """handle meld-message events on SocketIO channel"""
            component = self.get_component(message["id"])
            result = await process_message(component, message)
            self.logger.debug("meld-message ready to send in session %s" % sid)
            await self.sio_server.emit("meld-response", result)

        @self.on_event("meld-init")
        async def meld_init(sid, cid):
            """
            handle meld-init events on SocketIO channel.
            called once on object initialization on the GUI.
            """
            self.logger.debug("meld-init event for component %s received" % cid)
            component = self.get_component(cid)
            return component._listeners()

    async def on_shutdown(self, app):
        """
        Handles on shutdown cleanups.
        """
        if not self.sio_server:
            return
        for ws in self.sio_server.eio.sockets.values():
            await ws.close(abort=True)

        # self.loop.call_soon_threadsafe(self.loop.stop)


def listen(*event_names: str, app_name: str = None):
    """
    Decorator to indicate that the decorated method should listen for custom events.
    It can be called using `flask_meld.emit`. Keyword arguments from `flask_meld.emit`
    will be passed as keyword arguments to the decorated method.

    Params:
        *event_names (str): One or more event names to listen for.
    """

    def dec(func):
        func._meld_event_names = event_names
        return func

    return dec


def emit(event_name: str, app_name="MelTree", **kwargs):
    """
    Emit a custom event which will call any Component methods with the `@listen`
    decorator that are listening for the given event. Keyword arguments to this
    function are passed as keyword arguments to each of the decorated methods.

    Params:
        event_name (str): The name of the custom event to emit.
        **kwargs: Arguments to be passed as keyword arguments to the listening
            methods.
    """
    if app_name:
        app = MelTree(app_name=app_name)
    else:
        app = MelTree()
    sio_server = app.sio_server

    async def _emit():
        await sio_server.emit("meld-event", {"event": event_name, "message": kwargs})

    sio_server.start_background_task(_emit)


class BaseComponents:
    MelTree = MelTree
    MelTreeHTTP = MelTreeHTTP


MelTreeHTTP = memoized(BaseComponents.MelTreeHTTP)
MelTree = memoized(BaseComponents.MelTree)
