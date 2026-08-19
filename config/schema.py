SUPPORTED_LANGUAGE_HEADER = {
    'name': 'Accept-Language',
    'in': 'header',
    'required': False,
    'description': (
        'Language used for translatable response and validation messages. '
        'Defaults to English.'
    ),
    'schema': {
        'type': 'string',
        'enum': ['en', 'fa'],
        'default': 'en',
    },
}


def add_accept_language_header(result, generator, request, public):
    """Expose language negotiation on every API operation in OpenAPI."""
    for path_item in result.get('paths', {}).values():
        for method, operation in path_item.items():
            if method.lower() not in {
                'get',
                'post',
                'put',
                'patch',
                'delete',
                'options',
                'head',
            }:
                continue

            parameters = operation.setdefault('parameters', [])
            if any(
                parameter.get('name') == 'Accept-Language'
                and parameter.get('in') == 'header'
                for parameter in parameters
            ):
                continue
            parameters.append(SUPPORTED_LANGUAGE_HEADER.copy())

    return result
