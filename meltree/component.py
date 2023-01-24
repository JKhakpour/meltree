import sys
import uuid
from importlib.util import module_from_spec, spec_from_file_location
from itertools import groupby
from operator import itemgetter
import inspect
from pathlib import Path
import orjson
from bs4 import BeautifulSoup
from bs4.element import Tag
from bs4.formatter import HTMLFormatter
import jinja2
from wrapt import ObjectProxy


class ComponentProxy(ObjectProxy):
    """
    The meld Component class does most of the heavy lifting to handle data-binding,
    template context variable binding, template rendering and additional hooks.
    """

    def __init__(self, obj, template_path=None, **kwargs):
        self.__wrapped__ = obj
        self.errors = {}
        self._form = None
        self.template_path = template_path or self.template_path
        self.__dict__.update(**kwargs)
        self.cid = f"{ self.__class__.__name__ }:{ uuid.uuid4() }"

        if hasattr(self, "form"):
            self._bind_form(kwargs)

    def __repr__(self):
        return f"<meld.Component {self.__class__.__name__}>"

    def __getattribute__(self, name, **kwargs):
        attr = super(ComponentProxy, self).__getattribute__(name)
        return attr

    def _listeners(self):
        """
        Dictionary containing all listeners and the methods they call
        """
        functions = self._functions()
        listeners = [
            (event_name, func_name)
            for func_name, func in self._functions().items()
            if hasattr(func, "_meld_event_names")
            for event_name in func._meld_event_names
        ]

        return {
            event_name: [t[1] for t in group]
            for event_name, group in groupby(listeners, itemgetter(0))
        }

    def _attributes(self):
        """
        Get attributes that can be called in the component.
        """
        attributes = {}

        attributes_names = [
            attr
            for attr in dir(self.__wrapped__)
            if not callable(getattr(self, attr)) and not attr.startswith("_")
        ]
        for name in attributes_names:
            attributes[name] = getattr(self, name)

        return attributes

    def _functions(self):
        """
        Get methods that can be called in the component.
        """
        functions = {}

        function_list = [
            func
            for func in dir(self.__wrapped__)
            if callable(getattr(self.__wrapped__, func)) and not func.startswith("_")
        ]

        for func in function_list:
            functions[func] = getattr(self, func)

        return functions

    def __context__(self):
        """
        Collects every thing that could be used in the template context.
        """
        return {
            "attributes": self._attributes(),
            "methods": self._functions(),
        }

    def updated(self, name):
        """
        Hook that gets called when a component's data is about to get updated.
        """
        pass

    def _render_template(self, template_name: str, context_variables: dict):
        env = jinja2.Environment()
        with open(template_name) as f:
            f_str = f.read()
        template = env.from_string(f_str)
        return template.render(**context_variables)

    def render(self):
        data = self._attributes()
        context = self.__context__()
        context_variables = {}
        context_variables.update(context["attributes"])
        context_variables.update(context["methods"])
        context_variables.update({"form": self._form})

        template_path = (
            Path(sys.argv[0]).parent / "templates/meltree" / self.template_path
        )
        component_name = self.__class__.__name__
        rendered_template = self._render_template(str(template_path), context_variables)

        soup = BeautifulSoup(rendered_template, features="html.parser")
        root_element = self._get_root_element(soup)
        root_element["meld:id"] = str(self.cid)
        self._set_values(root_element, context_variables)

        script = soup.new_tag("script", type="module")
        init = {"id": str(self.cid), "name": component_name, "data": data}
        init_json = orjson.dumps(init).decode("utf-8")

        meld_import = 'import {Meld} from "/meltree_static/meld.js";'
        script.string = f"{meld_import} Meld.componentInit({init_json});"
        root_element.append(script)

        rendered_template = self._desoupify(soup)

        return rendered_template

    def _set_values(self, soup, context_variables):
        """
        Set the value on model fields
        """
        for element in soup.select("input,select,textarea"):
            model_attrs = [
                attr for attr in element.attrs.keys() if attr.startswith("meld:model")
            ]
            if len(model_attrs) > 1:
                raise Exception(
                    "Multiple 'meld:model' attributes not allowed on one tag."
                )

            for model_attr in model_attrs:
                value = context_variables[element.attrs[model_attr]]
                element.attrs["value"] = value
                if element.name == "select":
                    for e in element.find_all("option"):
                        if type(e) is Tag and e.attrs.get("value") == value:
                            e["selected"] = ""

                elif (
                    element.attrs.get("type")
                    and element.attrs.get("type") == "checkbox"
                    and value is True
                ):
                    element["checked"] = ""

    @staticmethod
    def _get_root_element(soup):
        for element in soup.contents:
            if element.name:
                return element

        raise Exception("No root element found")

    @staticmethod
    def _desoupify(soup):
        soup.smooth()
        return soup.encode(formatter=UnsortedAttributes()).decode("utf-8")


class UnsortedAttributes(HTMLFormatter):
    """
    Prevent beautifulsoup from re-ordering attributes.
    """

    def attributes(self, tag):
        for k, v in tag.attrs.items():
            yield k, v
