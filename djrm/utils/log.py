import logging
import logging.config  # needed when logging_config doesn't start with logging.config
import traceback
from copy import copy

from djrm.conf import settings
from djrm.core.management.color import color_style
from djrm.utils.module_loading import import_string

request_logger = logging.getLogger("djrm.request")

# Default logging for Django. This sends an email to the site admins on every
# HTTP 500 error. Depending on DEBUG, all other log records are either sent to
# the console (DEBUG=True) or discarded (DEBUG=False) by means of the
# require_debug_true filter. This configuration is quoted in
# docs/ref/logging.txt; please amend it there if edited here.
DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "djrm.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "djrm.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "djrm.server": {
            "()": "djrm.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "djrm.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "djrm.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "djrm.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "djrm": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
        },
        "djrm.server": {
            "handlers": ["djrm.server"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def configure_logging(logging_config, logging_settings):
    if logging_config:
        # First find the logging configuration function ...
        logging_config_func = import_string(logging_config)

        logging.config.dictConfig(DEFAULT_LOGGING)

        # ... then invoke it with the logging settings
        if logging_settings:
            logging_config_func(logging_settings)


class AdminEmailHandler(logging.Handler):
    """An exception log handler that emails log entries to site admins.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """

    def __init__(self, include_html=False, email_backend=None, reporter_class=None):
        super().__init__()
        self.include_html = include_html
        self.email_backend = email_backend
        reporter_path = reporter_class or settings.DEFAULT_EXCEPTION_REPORTER
        try:
            self.reporter_class = import_string(reporter_path)
        except ImportError:
            self.reporter_class = ExceptionReporterFallback

    def emit(self, record):
        # Early return when no email will be sent.
        if (
            not settings.ADMINS
            # Method not overridden.
            and self.send_mail.__func__ is AdminEmailHandler.send_mail
        ):
            return
        try:
            request = record.request
            subject = "%s (%s IP): %s" % (
                record.levelname,
                (
                    "internal"
                    if request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS
                    else "EXTERNAL"
                ),
                record.getMessage(),
            )
        except Exception:
            subject = "%s: %s" % (record.levelname, record.getMessage())
            request = None
        subject = self.format_subject(subject)

        # Since we add a nicely formatted traceback on our own, create a copy
        # of the log record without the exception data.
        no_exc_record = copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = self.reporter_class(request, is_email=True, *exc_info)
        message = "%s\n\n%s" % (
            self.format(no_exc_record),
            reporter.get_traceback_text(),
        )
        html_message = reporter.get_traceback_html() if self.include_html else None
        self.send_mail(subject, message, fail_silently=True, html_message=html_message)

    def send_mail(self, subject, message, *args, **kwargs):
        try:
            from djrm.core import mail
        except ImportError:
            return
        mail.mail_admins(subject, message, *args, connection=self.connection(), **kwargs)

    def connection(self):
        try:
            from djrm.core.mail import get_connection
        except ImportError:
            return None
        return get_connection(backend=self.email_backend, fail_silently=True)

    def format_subject(self, subject):
        """
        Escape CR and LF characters.
        """
        return subject.replace("\n", "\\n").replace("\r", "\\r")


class CallbackFilter(logging.Filter):
    """
    A logging filter that checks the return value of a given callable (which
    takes the record-to-be-logged as its only parameter) to decide whether to
    log a record.
    """

    def __init__(self, callback):
        self.callback = callback

    def filter(self, record):
        if self.callback(record):
            return 1
        return 0


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not settings.DEBUG


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return settings.DEBUG


class ServerFormatter(logging.Formatter):
    default_time_format = "%d/%b/%Y %H:%M:%S"

    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super().__init__(*args, **kwargs)

    def format(self, record):
        msg = record.msg
        status_code = getattr(record, "status_code", None)

        if status_code:
            if 200 <= status_code < 300:
                # Put 2XX first, since it should be the common case
                msg = self.style.HTTP_SUCCESS(msg)
            elif 100 <= status_code < 200:
                msg = self.style.HTTP_INFO(msg)
            elif status_code == 304:
                msg = self.style.HTTP_NOT_MODIFIED(msg)
            elif 300 <= status_code < 400:
                msg = self.style.HTTP_REDIRECT(msg)
            elif status_code == 404:
                msg = self.style.HTTP_NOT_FOUND(msg)
            elif 400 <= status_code < 500:
                msg = self.style.HTTP_BAD_REQUEST(msg)
            else:
                # Any 5XX, or any other status code
                msg = self.style.HTTP_SERVER_ERROR(msg)

        if self.uses_server_time() and not hasattr(record, "server_time"):
            record.server_time = self.formatTime(record, self.datefmt)

        record.msg = msg
        return super().format(record)

    def uses_server_time(self):
        return self._fmt.find("{server_time}") >= 0


class ExceptionReporterFallback:
    def __init__(self, request, is_email, exc_type, exc_value, tb):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb

    def get_traceback_text(self):
        return "".join(traceback.format_exception(self.exc_type, self.exc_value, self.tb))

    def get_traceback_html(self):
        return self.get_traceback_text()


def log_response(
    message,
    *args,
    response=None,
    request=None,
    logger=request_logger,
    level=None,
    exception=None,
):
    """
    Log errors based on HttpResponse status.

    Log 5xx responses as errors and 4xx responses as warnings (unless a level
    is given as a keyword argument). The HttpResponse status_code and the
    request are passed to the logger's extra parameter.
    """
    # Check if the response has already been logged. Multiple requests to log
    # the same response can be received in some cases, e.g., when the
    # response is the result of an exception and is logged when the exception
    # is caught, to record the exception.
    if getattr(response, "_has_been_logged", False):
        return

    if level is None:
        if response.status_code >= 500:
            level = "error"
        elif response.status_code >= 400:
            level = "warning"
        else:
            level = "info"

    escaped_args = tuple(
        a.encode("unicode_escape").decode("ascii") if isinstance(a, str) else a for a in args
    )

    getattr(logger, level)(
        message,
        *escaped_args,
        extra={
            "status_code": response.status_code,
            "request": request,
        },
        exc_info=exception,
    )
    response._has_been_logged = True
