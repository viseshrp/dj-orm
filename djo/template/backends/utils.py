from djo .middleware .csrf import get_token 
from djo .utils .functional import lazy 
from djo .utils .html import format_html 
from djo .utils .safestring import SafeString 


def csrf_input (request ):
    return format_html (
    '<input type="hidden" name="csrfmiddlewaretoken" value="{}">',
    get_token (request ),
    )


csrf_input_lazy =lazy (csrf_input ,SafeString ,str )
csrf_token_lazy =lazy (get_token ,str )
