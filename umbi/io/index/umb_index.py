"""
Main UMB index class and schema.
"""

from dataclasses import dataclass, field
from typing import Type

from marshmallow import fields, post_load

import umbi.datatypes

from .annotations import Annotations, AnnotationsSchema
from .file_data import FileData, FileDataSchema
from .json_schema import *
from .model_data import ModelData, ModelDataSchema
from .transition_system import TransitionSystem, TransitionSystemSchema
from .variable_valuations import VariableValuationsSchema


class UmbIndexSchema(JsonSchema):
    """UMB index file schema."""

    format_version = FieldUint(data_key="format-version", required=True)
    format_revision = FieldUint(data_key="format-revision", required=True)
    model_data = fields.Nested(ModelDataSchema, data_key="model-data", required=False)
    file_data = fields.Nested(FileDataSchema, data_key="file-data", required=False)
    transition_system = fields.Nested(TransitionSystemSchema, data_key="transition-system", required=True)
    annotations = fields.Nested(AnnotationsSchema, data_key="annotations", required=False)
    state_valuations = fields.Nested(VariableValuationsSchema, data_key="state-valuations", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "UmbIndex":
        """Create an UmbIndex object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return UmbIndex(
            format_version=obj.format_version,
            format_revision=obj.format_revision,
            model_data=getattr(obj, "model_data", None),
            file_data=getattr(obj, "file_data", None),
            transition_system=obj.transition_system,
            annotations=getattr(obj, "annotations", None),
            state_valuations=getattr(obj, "state_valuations", None),
        )


@dataclass
class UmbIndex(JsonSchemaResult):

    format_version: int = 0
    format_revision: int = 0
    model_data: ModelData | None = None
    file_data: FileData | None = None
    transition_system: TransitionSystem = field(default_factory=TransitionSystem)
    annotations: Annotations | None = None
    state_valuations: umbi.datatypes.StructType | None = None

    @classmethod
    def class_schema(cls) -> Type:
        return UmbIndexSchema

    def __str__(self) -> str:
        """Convert to a string (json format)."""
        return umbi.datatypes.json_to_string(self.to_json())
