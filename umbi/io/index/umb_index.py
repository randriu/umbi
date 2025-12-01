"""
Main UMB index class and schema.
"""

from dataclasses import dataclass, field

from marshmallow import fields

from .annotations import Annotations, AnnotationsSchema
from .file_data import FileData, FileDataSchema
from .json_schema import (
    JsonSchema,
    JsonSchemaResult,
    FieldUint,
)
from .model_data import ModelData, ModelDataSchema
from .transition_system import TransitionSystem, TransitionSystemSchema
from .variable_valuations import VariableValuationsSchema
import umbi.datatypes


class UmbIndexSchema(JsonSchema):
    """UMB index file schema."""

    format_version = FieldUint(data_key="format-version", required=True)
    format_revision = FieldUint(data_key="format-revision", required=True)
    model_data = fields.Nested(ModelDataSchema, data_key="model-data", required=False)
    file_data = fields.Nested(FileDataSchema, data_key="file-data", required=False)
    transition_system = fields.Nested(TransitionSystemSchema, data_key="transition-system", required=True)
    annotations = fields.Nested(AnnotationsSchema, data_key="annotations", required=False)
    state_valuations = fields.Nested(VariableValuationsSchema, data_key="state-valuations", required=False)

    @classmethod
    def schema_class(cls) -> type:
        return UmbIndex


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
    def class_schema(cls) -> type:
        return UmbIndexSchema
