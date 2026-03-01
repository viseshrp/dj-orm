from djo .utils .version import get_version 

VERSION =(5 ,2 ,12 ,"alpha",0 )

__version__ =get_version (VERSION )


def setup (set_prefix =True ):
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    Set the thread-local urlresolvers script prefix if `set_prefix` is True.
    """
    from djo .apps import apps 
    from djo ._ext .setup_helpers import set_script_prefix_if_available 
    from djo .conf import settings 
    from djo .utils .log import configure_logging 

    configure_logging (settings .LOGGING_CONFIG ,settings .LOGGING )
    if set_prefix :
        set_script_prefix_if_available (settings .FORCE_SCRIPT_NAME )
    apps .populate (settings .INSTALLED_APPS )
