import logging
from http import HTTPStatus
from typing import Final

from django.http import HttpRequest

request_logger: Final = logging.getLogger('dmr.request')


def log_server_error(
    request: HttpRequest,
    exc: Exception,
    status_code: HTTPStatus,
) -> None:
    """Log *exc* that was converted into a ``5xx`` response."""
    if status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
        return
    request_logger.error(
        '%s: %s',
        status_code.phrase,
        request.path,
        exc_info=exc,
        extra={'status_code': status_code, 'request': request},
    )
