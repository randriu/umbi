"""
File data schemas and classes.
"""

from dataclasses import dataclass
from typing import Type

from marshmallow import fields, post_load

import umbi.datatypes

from .json_schema import *


class FileDataSchema(JsonSchema):
    """File data schema."""

    tool = fields.String(data_key="tool", required=False)
    tool_version = fields.String(data_key="tool-version", required=False)
    creation_date = FieldUint(data_key="creation-date", required=False)
    parameters = fields.Raw(data_key="parameters", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "FileData":
        """Create a FileData object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return FileData(
            tool=obj.tool,
            tool_version=obj.tool_version,
            creation_date=obj.creation_date,
            parameters=obj.parameters,
        )


@dataclass
class FileData(JsonSchemaResult):
    """File data class."""

    tool: str | None = None
    tool_version: str | None = None
    creation_date: int | None = None
    parameters: umbi.datatypes.JsonLike | None = None

    @classmethod
    def class_schema(cls) -> Type:
        return FileDataSchema
