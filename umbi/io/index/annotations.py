"""
Annotation schemas and classes.
"""

from dataclasses import dataclass
from typing import Literal, Type

from marshmallow import fields, post_load, validate

from .json_schema import *


class AnnotationSchema(JsonSchema):
    """Schema for one annotation."""

    alias = fields.String(data_key="alias", required=False)
    description = fields.String(data_key="description", required=False)
    applies_to = fields.List(
        fields.String(validate=validate.OneOf(["states", "choices", "branches"])),
        data_key="applies-to",
        required=False,
        validate=validate.Length(min=1),
    )
    type = fields.String(
        data_key="type",
        required=False,
        validate=validate.OneOf(["bool", "double", "rational", "double-interval", "rational-interval", "string"]),
    )
    lower = fields.Float(data_key="lower", required=False)
    upper = fields.Float(data_key="upper", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "Annotation":
        """Create an Annotation object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return Annotation(
            alias=obj.alias,
            description=obj.description,
            applies_to=obj.applies_to,
            type=obj.type,
            lower=obj.lower,
            upper=obj.upper,
        )


@dataclass
class Annotation(JsonSchemaResult):
    """Annotation data class."""

    alias: str | None = None
    description: str | None = None
    applies_to: list[Literal["states", "choices", "branches"]] | None = None
    type: Literal["bool", "double", "rational", "double-interval", "rational-interval", "string"] | None = None
    lower: float | None = None
    upper: float | None = None

    @classmethod
    def class_schema(cls) -> Type:
        return AnnotationSchema


class AnnotationsSchema(JsonSchema):
    """Schema for all annotations."""

    rewards = fields.Dict(
        keys=fields.String(), values=fields.Nested(AnnotationSchema), data_key="rewards", required=False
    )
    aps = fields.Dict(keys=fields.String(), values=fields.Nested(AnnotationSchema), data_key="aps", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "Annotations":
        """Create an Annotations object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return Annotations(
            rewards=obj.rewards,
            aps=obj.aps,
        )


@dataclass
class Annotations(JsonSchemaResult):
    """Annotations data class."""

    rewards: dict[str, Annotation] | None = None
    aps: dict[str, Annotation] | None = None

    @classmethod
    def class_schema(cls) -> Type:
        return AnnotationsSchema
