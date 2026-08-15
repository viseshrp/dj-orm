"\nDjango's support for templates.\n\nThe djorm.template namespace contains two independent subsystems:\n\n1. Multiple Template Engines: support for pluggable template backends,\n   built-in backends and backend-independent APIs\n2. Django Template Language: Django's own template engine, including its\n   built-in loaders, context processors, tags and filters.\n\nIdeally these subsystems would be implemented in distinct packages. However\nkeeping them together made the implementation of Multiple Template Engines\nless disruptive .\n\nHere's a breakdown of which modules belong to which subsystem.\n\nMultiple Template Engines:\n\n- djorm.template.backends.*\n- djorm.template.loader\n- djorm.template.response\n\nDjango Template Language:\n\n- djorm.template.base\n- djorm.template.context\n- djorm.template.context_processors\n- djorm.template.loaders.*\n- djorm.template.debug\n- djorm.template.defaultfilters\n- djorm.template.defaulttags\n- djorm.template.engine\n- djorm.template.loader_tags\n- djorm.template.smartif\n\nShared:\n\n- djorm.template.utils\n\n"

# Multiple Template Engines

from .engine import Engine
from .utils import EngineHandler

engines = EngineHandler()

__all__ = ("Engine", "engines")


# Django Template Language

# Public exceptions
from .base import VariableDoesNotExist  # NOQA isort:skip
from .context import Context, ContextPopException, RequestContext  # NOQA isort:skip
from .exceptions import TemplateDoesNotExist, TemplateSyntaxError  # NOQA isort:skip

# Template parts
from .base import (  # NOQA isort:skip
    Node,
    NodeList,
    Origin,
    Template,
    Variable,
)

# Library management
from .library import Library  # NOQA isort:skip

# Import the .autoreload module to trigger the registrations of signals.
from . import autoreload  # NOQA isort:skip

__all__ += ("Template", "Context", "RequestContext")
