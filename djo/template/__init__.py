"""
Django's support for templates.

The djo.template namespace contains two independent subsystems:

1. Multiple Template Engines: support for pluggable template backends,
   built-in backends and backend-independent APIs
2. Django Template Language: Django's own template engine, including its
   built-in loaders, context processors, tags and filters.

Ideally these subsystems would be implemented in distinct packages. However
keeping them together made the implementation of Multiple Template Engines
less disruptive .

Here's a breakdown of which modules belong to which subsystem.

Multiple Template Engines:

- djo.template.backends.*
- djo.template.loader
- djo.template.response

Django Template Language:

- djo.template.base
- djo.template.context
- djo.template.context_processors
- djo.template.loaders.*
- djo.template.debug
- djo.template.defaultfilters
- djo.template.defaulttags
- djo.template.engine
- djo.template.loader_tags
- djo.template.smartif

Shared:

- djo.template.utils

"""

# Multiple Template Engines

from .engine import Engine 
from .utils import EngineHandler 

engines =EngineHandler ()

__all__ =("Engine","engines")


# Django Template Language

# Public exceptions
from .base import VariableDoesNotExist # NOQA isort:skip
from .context import Context ,ContextPopException ,RequestContext # NOQA isort:skip
from .exceptions import TemplateDoesNotExist ,TemplateSyntaxError # NOQA isort:skip

# Template parts
from .base import (# NOQA isort:skip
Node ,
NodeList ,
Origin ,
Template ,
Variable ,
)

# Library management
from .library import Library # NOQA isort:skip

# Import the .autoreload module to trigger the registrations of signals.
from .import autoreload # NOQA isort:skip


__all__ +=("Template","Context","RequestContext")
