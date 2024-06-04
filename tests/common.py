from dataclasses import dataclass, field

from bson import ObjectId

from conf import mongo_client


@dataclass
class SimpleDTO:
    x: str
    y: int


@dataclass
class DTOWithID:
    x: str
    y: int
    _id: ObjectId = field(default_factory=ObjectId, kw_only=True)


@dataclass
class ComplicatedDTO:
    x: str
    y: bool = False
    name: str = 'Hello World!'
    skills: list[str] = field(default_factory=list)


@dataclass
class NestedDTO:
    title: str = 'Nested DTO'
    _id: ObjectId = field(default_factory=ObjectId, kw_only=True)
    dtos: list[SimpleDTO] = field(default_factory=list)


def collection_for_complicated_dto():
    return mongo_client()['dto_complicated_db']['dto']


def collection_for_simple_dto():
    return mongo_client()['dto_simple_db']['dto']


def collection_for_dto_with_id():
    return mongo_client()['dto_with_id_db']['dto']