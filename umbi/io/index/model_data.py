"""
Model data schemas and classes.
"""

from dataclasses import dataclass

from marshmallow import fields

from .json_schema import (
    JsonSchema,
    JsonSchemaResult,
)


class ModelDataSchema(JsonSchema):
    name = fields.String(data_key="name", required=False)
    version = fields.String(data_key="version", required=False)
    authors = fields.List(fields.String(), data_key="authors", required=False)
    description = fields.String(data_key="description", required=False)
    comment = fields.String(data_key="comment", required=False)
    doi = fields.String(data_key="doi", required=False)
    url = fields.String(data_key="url", required=False)

    @classmethod
    def schema_class(cls) -> type:
        return ModelData


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
    def class_schema(cls) -> type:
        return ModelDataSchema
