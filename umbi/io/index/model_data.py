"""
Model data schemas and classes.
"""

from dataclasses import dataclass
from typing import Type

from marshmallow import fields, post_load

from .json_schema import *


class ModelDataSchema(JsonSchema):
    name = fields.String(data_key="name", required=False)
    version = fields.String(data_key="version", required=False)
    authors = fields.List(fields.String(), data_key="authors", required=False)
    description = fields.String(data_key="description", required=False)
    comment = fields.String(data_key="comment", required=False)
    doi = fields.String(data_key="doi", required=False)
    url = fields.String(data_key="url", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "ModelData":
        obj = super().make_object(data, **kwargs)
        return ModelData(
            name=obj.name,
            version=obj.version,
            authors=obj.authors,
            description=obj.description,
            comment=obj.comment,
            doi=obj.doi,
            url=obj.url,
        )


@dataclass
class ModelData(JsonSchemaResult):
    name: str | None = None
    version: str | None = None
    authors: list[str] | None = None
    description: str | None = None
    comment: str | None = None
    doi: str | None = None
    url: str | None = None

    @classmethod
    def class_schema(cls) -> Type:
        return ModelDataSchema
