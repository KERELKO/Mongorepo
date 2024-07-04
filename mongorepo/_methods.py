from dataclasses import asdict
import inspect
from typing import Any, Callable, Iterable, Type

from bson import ObjectId
from pymongo.collection import Collection

from mongorepo.utils import (
    replace_typevars,
    _validate_method_annotations,
    _get_converter,
)
from mongorepo import DTO, exceptions


def _add_method(
    dto_type: Type[DTO],
    collection: Collection,
    id_field: str | None = None,
) -> Callable:

    def add(self, dto: DTO) -> DTO:
        collection.insert_one(asdict(dto))
        return dto

    def add_return_with_id(self, dto: DTO) -> DTO:
        object_id = ObjectId()
        dto.__dict__[id_field] = str(object_id)  # type: ignore
        collection.insert_one({**asdict(dto), '_id': object_id})
        return dto

    if not id_field:
        return add
    return add_return_with_id


def _get_list_method(
    dto_type: Type[DTO],
    collection: Collection,
    id_field: str | None = None,
):
    to_dto = _get_converter(id_field=id_field)

    def get_list(self, offset: int = 0, limit: int = 20) -> list[DTO]:
        cursor = collection.find().skip(offset).limit(limit)
        return [to_dto(dto_type, doc) for doc in cursor]
    return get_list


def _get_all_method(
    dto_type: Type[DTO],
    collection: Collection,
    id_field: str | None = None
) -> Callable:
    to_dto = _get_converter(id_field=id_field)

    def get_all(self, **filters: Any) -> Iterable[DTO]:
        cursor = collection.find(filters)
        for dct in cursor:
            yield to_dto(dto_type, dct)
    return get_all


def _update_method(
    dto_type: Type[DTO],
    collection: Collection,
    id_field: str | None = None,
) -> Callable:
    to_dto = _get_converter(id_field=id_field)

    def update(self, dto: DTO, **filters: Any) -> DTO | None:
        data: dict[str, dict[str, Any]] = {'$set': {}}
        for field, value in asdict(dto).items():
            if isinstance(value, (int, bool, float)):
                data['$set'][field] = value
            elif not value:
                continue
            else:
                data['$set'][field] = value
        updated_document: dict[str, Any] | None = collection.find_one_and_update(
            filter=filters, update=data, return_document=True,
        )
        return to_dto(dto_type, updated_document) if updated_document else None
    return update


def _delete_method(dto_type: Type[DTO], collection: Collection) -> Callable:
    def delete(self, **filters: Any) -> bool:
        deleted = collection.find_one_and_delete(filters)
        return True if deleted else False
    return delete


def _get_method(
    dto_type: Type[DTO],
    collection: Collection,
    id_field: str | None = None,
) -> Callable:
    to_dto = _get_converter(id_field=id_field)

    def get(self, **filters: Any) -> DTO | None:
        result = collection.find_one(filters)
        return to_dto(dto_type, result) if result else None
    return get


def _update_field_method(
    dto_type: Type[DTO],
    collection: Collection,
    id_field: str | None = None,
) -> Callable:
    to_dto = _get_converter(id_field=id_field)

    def update_field(self, field_name: str, value: Any, **filters) -> DTO | None:
        if field_name not in dto_type.__dict__['__annotations__']:
            raise exceptions.MongoRepoException(
                message=f'{dto_type} does not have field "{field_name}"'
            )
        result = collection.find_one_and_update(
            filter=filters, update={'$set': {field_name: value}}, return_document=True,
        )
        return to_dto(dto_type, result) if result else None
    return update_field


def _update_integer_field_method(
    dto_type: Type[DTO], collection: Collection, field_name: str, _weight: int = 1,
) -> Callable:
    def update_interger_field(self, weight: int | None = None, **filters) -> None:
        w = weight if weight is not None else _weight
        collection.update_one(
            filter=filters, update={'$inc': {field_name: w}}
        )
    return update_interger_field


def _update_list_field_method(
    dto_type: Type[DTO], collection: Collection, field_name: str, command: str = '$push',
) -> Callable:
    def update_list(self, value: Any, **filters) -> None:
        collection.update_one(
            filter=filters, update={command: {field_name: value}}
        )
    return update_list


def _pop_list_method(dto_type: Type[DTO], collection: Collection, field_name: str) -> Callable:
    def pop_list(self, **filters) -> Any | None:
        document = collection.find_one_and_update(
            filter=filters, update={'$pop': {field_name: 1}},
        )
        return document[field_name][-1] if document else None
    return pop_list


def _is_read_method(method: Callable) -> bool:
    if method.__name__ in ['get', 'get_list', 'get_all']:
        return True
    return False


def _substitute_method(
    mongorepo_method: Callable,
    generic_method: Callable,
    dto: Type[DTO],
    collection: Collection,
    id_field: str | None = None,
) -> Callable:
    if id_field in mongorepo_method.__annotations__:
        mongorepo_method = mongorepo_method(dto_type=dto, collection=collection, id_field=id_field)
    else:
        mongorepo_method = mongorepo_method(dto_type=dto, collection=collection)

    is_async = inspect.isawaitable(generic_method)

    def func(self, *args, **kwargs) -> Any:
        required_params = __manage_params(
            mongorepo_method, generic_method, *args, **kwargs,
        )
        return mongorepo_method(self, **required_params)

    async def async_func(self, *args, **kwargs) -> Any:
        required_params = __manage_params(
            mongorepo_method, generic_method, *args, **kwargs,
        )
        return await mongorepo_method(self, **required_params)

    new_method = async_func if is_async else func

    new_method.__annotations__ = generic_method.__annotations__
    new_method.__name__ = generic_method.__name__
    new_method.__annotations__['return'] = dto | None

    replace_typevars(new_method, dto)

    return new_method


def __manage_params(
    mongorepo_method: Callable,
    generic_method: Callable,
    *args,
    **kwargs,
) -> dict[str, Any]:
    _validate_method_annotations(generic_method)
    result: dict[str, Any] = {}
    # generic_method_hm = _get_params_posititions(generic_method, exclude_first=True)
    # mongorepo_method_hm = _get_params_posititions(mongorepo_method, exclude_first=True)
    return result


def _get_params_posititions(
    func: Callable,
    exclude_first: bool = False,
) -> dict[int, str]:
    params = dict(inspect.signature(func).parameters)
    result: dict[int, str] = {}
    if exclude_first:
        first = list(params)[0]
        del params[first]
    i = 1
    for name in params.keys():
        result[i] = name
    return result


METHOD_NAME__CALLABLE: dict[str, Callable] = {
    'get': _get_method,
    'add': _add_method,
    'update': _update_method,
    'delete': _delete_method,
    'get_list': _get_list_method,
    'get_all': _get_all_method,
    'pop': _pop_list_method,
    'update_field': _update_field_method,
    'update_list': _update_list_field_method,
    'update_integer': _update_integer_field_method,
}
