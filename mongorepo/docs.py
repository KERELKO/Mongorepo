def get_available_meta_attributes(only_names: bool = False) -> dict[str, str] | tuple[str, ...]:
    attrs = {
        'index': 'creates index for a collection',
        'method_access': (
            'added methods will be private, '
            'protected or public, use mongorepo.Access'
        ),
        'dto': 'sets default dto for repository, repository saves data in the format of the dto',
        'collection': 'sets default collection for repository',
        'substitute': (
            '#Not implemented! Substitutes methods of mongorepo decorator or'
            'class with provided or inherited class'
        ),
    }
    if only_names:
        return tuple(attrs.keys())
    return attrs


def get_available_repository_methods(only_names: bool = False) -> dict[str, str] | tuple[str, ...]:
    methods = {
        'add': 'add document to a collection, collection stores it in dto format, params: dto: DTO',
        'delete': 'delete document from a collection, params: **filters: Any',
        'update': (
            'update document in a collection takes dto as parameter, '
            'if no value in dto(except: float, int, bool) skips it'
        ),
        'get': 'retrieve a document from a collection, params: **filters: Any',
        'get_all': 'retrive all documents of the same type(dto type), params: **filters: Any',
        '{field}__append': (
            'Only for decorator with "array_fields" append item to a document'
        ),
        '{field}__remove': (
            'Only for decorator with "array_fields" remove item from a document'
        ),
        '{field}__pop': (
            'Only for decorator with "array_fields" pop last item from a document'
        ),
        'increment_{field}': (
            'Only for decorator with "integer_fields" increment integer field by 1 in a document'
            ),
        'decrement_{field}': (
            'Only for decorator with "integer_fields" decrement integer fied by 1 in a document'
        ),
    }
    if only_names:
        return tuple(methods.keys())
    return methods