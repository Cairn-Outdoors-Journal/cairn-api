from cairn_api.main import create_app


def test_openapi_documents_health_endpoints() -> None:
    spec = create_app().openapi()

    assert spec["info"]["title"] == "Cairn API"
    assert {"/healthz", "/readyz"} <= set(spec["paths"])
