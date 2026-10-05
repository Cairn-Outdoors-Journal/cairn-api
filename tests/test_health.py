from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from cairn_api import __version__
from cairn_api.config import Settings, get_settings
from cairn_api.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(environment="test")
    with TestClient(app) as client:
        yield client


def test_healthz_reports_ok_and_version(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_readyz_without_database_is_ok(client: TestClient) -> None:
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "not_configured"}


def test_readyz_with_unreachable_database_is_503() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test", database_url="postgresql://nobody@127.0.0.1:1/none"
    )
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unreachable"}
