import logging
from http import HTTPStatus
from typing import Any, final

import pytest

from dmr import Controller
from dmr.exceptions import InternalServerError, NotAuthenticatedError
from dmr.plugins.pydantic import PydanticSerializer
from dmr.test import DMRAsyncRequestFactory, DMRRequestFactory


@final
class _SyncController(Controller[PydanticSerializer]):
    validate_responses = False

    def get(self) -> str:
        raise InternalServerError('sync')

    def post(self) -> Any:
        return object()

    def put(self) -> str:
        raise NotAuthenticatedError


@final
class _AsyncController(Controller[PydanticSerializer]):
    validate_responses = False

    async def get(self) -> str:
        raise InternalServerError('async')


@pytest.mark.parametrize('method', ['get', 'post'])
def test_sync_server_error_logged(
    dmr_rf: DMRRequestFactory,
    caplog: pytest.LogCaptureFixture,
    *,
    method: str,
) -> None:
    """Ensures that errors converted into ``5xx`` responses are logged."""
    request = getattr(dmr_rf, method)('/whatever/')

    response = _SyncController.as_view()(request)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == 'dmr.request'
    assert record.levelno == logging.ERROR
    assert record.getMessage() == 'Internal Server Error: /whatever/'
    assert record.exc_info
    assert record.__dict__['status_code'] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert record.__dict__['request'] is request


@pytest.mark.asyncio
async def test_async_server_error_logged(
    dmr_async_rf: DMRAsyncRequestFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ensures that async errors converted into ``5xx`` responses are logged."""
    request = dmr_async_rf.get('/whatever/')

    response = await dmr_async_rf.wrap(_AsyncController.as_view()(request))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == 'dmr.request'
    assert record.exc_info
    assert isinstance(record.exc_info[1], InternalServerError)


def test_client_error_not_logged(
    dmr_rf: DMRRequestFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ensures that errors converted into ``4xx`` responses are not logged."""
    caplog.set_level(logging.DEBUG, logger='dmr')

    response = _SyncController.as_view()(dmr_rf.put('/whatever/'))

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert not caplog.records
