"""
File data schemas and classes.
"""

from dataclasses import dataclass
from typing import Optional, Type
from marshmallow import fields, post_load

from .json_schema import *
import umbi.binary


class FileDataSchema(JsonSchema):
    """File data schema."""

    tool = fields.String(data_key="tool", required=False)
    tool_version = fields.String(data_key="tool-version", required=False)
    creation_date = FieldUint(data_key="creation-date", required=False)
    parameters = fields.Raw(data_key="parameters", required=False)

    @post_load
    def make_object(self, data : dict, **kwargs) -> "FileData":
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
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    creation_date: Optional[int] = None
    parameters: Optional[umbi.binary.JsonLike] = None

    @classmethod
    def class_schema(cls) -> Type:
        return FileDataSchema
