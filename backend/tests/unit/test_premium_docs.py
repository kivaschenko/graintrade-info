from app.utils.openapi_filters import (
    filter_schema_for_premium as _filter_openapi_schema,
)


def test_filter_openapi_schema_only_allows_whitelist():
    schema = {
        "openapi": "3.1.0",
        "paths": {
            "/categories": {"post": {"operationId": "createCategory"}, "get": {}},
            "/create-batches-item": {"post": {"operationId": "createBatch"}},
            "/items": {"get": {"operationId": "listItems"}, "post": {}},
            "/items/{id}": {"get": {}},
        },
    }

    filtered = _filter_openapi_schema(schema)

    assert "/categories" in filtered["paths"]
    assert "post" in filtered["paths"]["/categories"]
    assert "get" not in filtered["paths"]["/categories"]

    assert "/create-batches-item" in filtered["paths"]
    assert "post" in filtered["paths"]["/create-batches-item"]

    assert "/items" in filtered["paths"]
    assert "get" in filtered["paths"]["/items"]
    assert "post" not in filtered["paths"]["/items"]

    # Non-whitelisted path should be removed entirely
    assert "/items/{id}" not in filtered["paths"]
