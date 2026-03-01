from .messages import (
CRITICAL ,
DEBUG ,
ERROR ,
INFO ,
WARNING ,
CheckMessage ,
Critical ,
Debug ,
Error ,
Info ,
Warning ,
)
from .registry import Tags ,register ,run_checks ,tag_exists 
from importlib import import_module


def _maybe_import (path ):
    try :
        import_module (path )
    except ImportError :
        return 


# Import these to force registration of checks
_maybe_import ("djo.core.checks.async_checks")
_maybe_import ("djo.core.checks.caches")
_maybe_import ("djo.core.checks.commands")
_maybe_import ("djo.core.checks.compatibility.django_4_0")
_maybe_import ("djo.core.checks.database")
_maybe_import ("djo.core.checks.files")
_maybe_import ("djo.core.checks.model_checks")
_maybe_import ("djo.core.checks.security.base")
_maybe_import ("djo.core.checks.security.csrf")
_maybe_import ("djo.core.checks.security.sessions")
_maybe_import ("djo.core.checks.templates")
_maybe_import ("djo.core.checks.translation")
_maybe_import ("djo.core.checks.urls")


__all__ =[
"CheckMessage",
"Debug",
"Info",
"Warning",
"Error",
"Critical",
"DEBUG",
"INFO",
"WARNING",
"ERROR",
"CRITICAL",
"register",
"run_checks",
"tag_exists",
"Tags",
]
