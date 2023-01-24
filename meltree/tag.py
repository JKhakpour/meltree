# from component import get_component_class

from jinja2_simple_tags import StandaloneTag
from meltree.component import ComponentProxy


def MeldTag(manager):
    tag_class = type(
        f"{manager._name}_MeldTag", BaseMeldTag.__bases__, dict(BaseMeldTag.__dict__)
    )
    tag_class.session_manager = manager
    return tag_class


class BaseMeldTag(StandaloneTag):
    tags = {"meld"}
    session_manager = None

    def render(self, obj, **kwargs):
        # mn = MeldNode(component)
        # return mn.render(**kwargs)
        # import pdb; pdb.set_trace()

        # component = self.session_manager.get_component(obj.cid)
        # import pdb; pdb.set_trace()
        component = self.session_manager.get_component(id(obj))  # TODO: refactor
        rendered_component = component.render()

        return rendered_component


# class MeldNode:
#     def __init__(self, component):
#         self.component = component

#     def render(self, **kwargs):
#         import pdb; pdb.set_trace()
#         # Component = get_component_class(self.component_name)
#         # component = Component(**kwargs)
#         # rendered_component = self.component.render(self.component_name)
#         rendered_component = self.component.render()

#         return rendered_component
