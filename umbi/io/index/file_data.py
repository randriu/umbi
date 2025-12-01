"""
File data schemas and classes.
"""

from dataclasses import dataclass

from marshmallow import fields

import umbi.datatypes

from .json_schema import (
    JsonSchema,
    JsonSchemaResult,
    FieldUint,
)


class FileDataSchema(JsonSchema):
    """File data schema."""

    tool = fields.String(data_key="tool", required=False)
    tool_version = fields.String(data_key="tool-version", required=False)
    creation_date = FieldUint(data_key="creation-date", required=False)
    parameters = fields.Raw(data_key="parameters", required=False)

    @classmethod
    def schema_class(cls) -> type:
        return FileData


@dataclass
class FileData(JsonSchemaResult):
    """File data class."""

    tool: str | None = None
    tool_version: str | None = None
    creation_date: int | None = None
    parameters: umbi.datatypes.JsonLike | None = None

    @classmethod
    def class_schema(cls) -> type:
        return FileDataSchema
