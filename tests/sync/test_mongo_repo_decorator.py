import random

from bson import ObjectId

from tests.common import (
    SimpleDTO,
    DTOWithID,
    ComplicatedDTO,
    collection_for_complicated_dto,
    collection_for_dto_with_id,
    collection_for_simple_dto,
)

from mongorepo.decorators import mongo_repository_factory


def test_all_methods_with_decorator():
    cl = collection_for_simple_dto()

    @mongo_repository_factory
    class TestMongoRepository:
        class Meta:
            dto = SimpleDTO
            collection = cl

    num = random.randint(1, 123456)

    repo = TestMongoRepository()
    new_dto: SimpleDTO = repo.create(SimpleDTO(x='hey', y=num))
    assert new_dto.x == 'hey'

    updated_dto = repo.update(SimpleDTO(x='hey all!', y=13), y=num)
    assert updated_dto.x == 'hey all!'

    for dto in repo.get_all():
        assert isinstance(dto, SimpleDTO)

    dto = repo.get(y=13)
    assert dto is not None

    is_deleted = repo.delete(y=13)
    assert is_deleted is True

    dto = repo.get(y=13)
    assert dto is None

    cl.drop()


def test_can_get_dto_with_id():
    cl = collection_for_dto_with_id()

    @mongo_repository_factory
    class TestMongoRepository:
        class Meta:
            dto = DTOWithID
            collection = cl

    num = random.randint(1, 12346)

    repo = TestMongoRepository()
    new_dto: DTOWithID = repo.create(DTOWithID(x='dto with id', y=num))
    assert new_dto.x == 'dto with id'

    dto: DTOWithID = repo.get(y=num)
    assert dto._id is not None

    assert isinstance(dto._id, ObjectId)

    cl.drop()


def test_can_handle_complicated_dto():
    cl = collection_for_complicated_dto()

    @mongo_repository_factory
    class TestMongoRepository:
        class Meta:
            dto = ComplicatedDTO
            collection = cl

    repo = TestMongoRepository()
    repo.create(ComplicatedDTO(x='comp', y=True, name='You', skills=['h', 'e']))

    resolved_dto = repo.get(name='You')
    assert resolved_dto.skills == ['h', 'e'] and resolved_dto.x == 'comp'

    cl.drop()


def test_can_update_partially():
    cl = collection_for_complicated_dto()

    @mongo_repository_factory
    class TestMongoRepository:
        class Meta:
            dto = ComplicatedDTO
            collection = cl

    repo = TestMongoRepository()
    repo.create(ComplicatedDTO(x='Test', y=True, name='Me'))
    repo.update(name='Me', dto=ComplicatedDTO(x='Test', skills=['hello!'], name='Me'))

    updated_dto = repo.get(name='Me')
    assert updated_dto.skills == ['hello!']

    cl.drop()


def test_can_search_with_id():
    cl = collection_for_dto_with_id()

    @mongo_repository_factory
    class TestMongoRepository:
        class Meta:
            dto = DTOWithID
            collection = cl

    repo = TestMongoRepository()
    dto_id = repo.create(DTOWithID(x='ID', y=10))._id

    dto: DTOWithID = repo.get(_id=dto_id)
    assert dto.x == 'ID'

    assert isinstance(dto._id, ObjectId)

    cl.drop()