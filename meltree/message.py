import ast
import orjson
import asyncio
import functools
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(max_workers=5)


def make_async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.wrap_future(thread_pool.submit(func, *args, **kwargs))

    return wrapper


async def process_message(component, message):
    cid = message["id"]
    component_name = message["componentName"]
    action_queue = message["actionQueue"]
    render_dom = message.get("renderDOM", False)
    data = message["data"]

    return_data = None
    for action in action_queue:
        payload = action.get("payload", None)
        if "syncInput" in action["type"]:
            if hasattr(component, payload["name"]):
                setattr(component, payload["name"], payload["value"])
                if component._form:
                    field_name = payload.get("name")
                    if field_name in component._form._fields:
                        field = getattr(component._form, field_name)
                        component._set_field_data(field_name, payload["value"])
                        component.updated(field)
                        component.errors[field_name] = field.errors or ""
                else:
                    component.updated(payload["name"])

        elif "callMethod" in action["type"]:
            call_method_name = payload.get("name", "")
            method_name, params = parse_call_method_name(call_method_name)
            message = payload.get("message")

            if method_name is not None and hasattr(component, method_name):
                func = getattr(component, method_name)
                if not asyncio.iscoroutinefunction(func):
                    # make it awaitable function
                    func = make_async(func)

                if params:
                    return_data = await func(*params)
                elif message:
                    return_data = await func(**message)
                else:
                    return_data = await func()
                if component._form:
                    component._bind_form(component._attributes())
    res = {
        "id": cid,
        "data": orjson.dumps(component._attributes()).decode("utf-8")
        if component
        else {},
    }

    if render_dom:
        res["dom"] = component.render()

    if type(return_data) is web.Response and return_data.status_code == 302:
        res["redirect"] = {"url": return_data.location}
    return res


def parse_call_method_name(call_method_name: str):
    params = None
    method_name = call_method_name

    if "(" in call_method_name and call_method_name.endswith(")"):
        param_idx = call_method_name.index("(")
        params_str = call_method_name[param_idx:]

        # Remove the arguments from the method name
        method_name = call_method_name.replace(params_str, "")

        # Remove parenthesis
        params_str = params_str[1:-1]
        if params_str != "":
            try:
                params = ast.literal_eval("[" + params_str + "]")
            except (ValueError, SyntaxError):
                params = list(map(str.strip, params_str.split(",")))

    return method_name, params
