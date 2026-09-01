SUPPORTED_LANGUAGE_HEADER = {
    "name": "Accept-Language",
    "in": "header",
    "required": False,
    "description": (
        "Language used for translatable response and validation messages. "
        "Defaults to English."
    ),
    "schema": {
        "type": "string",
        "enum": ["en", "fa"],
        "default": "en",
    },
}

CSRF_TOKEN_HEADER = {
    "name": "X-CSRFToken",
    "in": "header",
    "required": True,
    "description": (
        "CSRF token returned by GET /api/v1/accounts/csrf/. "
        "Required for state-changing requests when cookie authentication is used."
    ),
    "schema": {
        "type": "string",
    },
}


def add_accept_language_header(result, generator, request, public):
    """Expose language and CSRF headers on API operations in OpenAPI."""
    for path_item in result.get("paths", {}).values():
        for method, operation in path_item.items():
            method_name = method.lower()
            if method_name not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
            }:
                continue

            parameters = operation.setdefault("parameters", [])
            has_language_header = any(
                parameter.get("name") == "Accept-Language"
                and parameter.get("in") == "header"
                for parameter in parameters
            )
            if not has_language_header:
                parameters.append(SUPPORTED_LANGUAGE_HEADER.copy())

            if method_name in {"post", "put", "patch", "delete"} and not any(
                parameter.get("name") == "X-CSRFToken"
                and parameter.get("in") == "header"
                for parameter in parameters
            ):
                parameters.append(CSRF_TOKEN_HEADER.copy())

    return result
