from copy import deepcopy
from typing import Dict, Tuple


ALLOWED_PREMIUM_ENDPOINTS: set[Tuple[str, str]] = {
    ("/categories", "post"),
    ("/create-batches-item", "post"),
    ("/items", "get"),
}


def filter_schema_for_premium(schema: Dict) -> Dict:
    """Return a copy of schema with only whitelisted endpoints visible in docs."""
    filtered = deepcopy(schema)
    paths = filtered.get("paths", {})
    new_paths = {}
    for path, methods in paths.items():
        keep_methods = {}
        for method, op in methods.items():
            if (path, method.lower()) in ALLOWED_PREMIUM_ENDPOINTS:
                keep_methods[method] = op
        if keep_methods:
            new_paths[path] = keep_methods
    filtered["paths"] = new_paths
    return filtered
