"""
State valuation schemas and classes.
"""

from dataclasses import dataclass
from typing import Optional, Literal, Union, Type
from marshmallow import fields, post_load, validate
from marshmallow_oneofschema.one_of_schema import OneOfSchema

from .json_schema import *


class PaddingSchema(JsonSchema):
    """Schema for padding fields."""
    padding = FieldUint(data_key="padding", required=True)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "Padding":
        """Create a Padding object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return Padding(padding=obj.padding)


@dataclass
class Padding(JsonSchemaResult):
    """Padding data class."""
    padding: int

    @classmethod
    def class_schema(cls) -> Type:
        return PaddingSchema


class VariableSchema(JsonSchema):
    """Schema for variable fields."""
    name = fields.String(data_key="name", required=True)
    type = fields.String(
        data_key="type", required=True, validate=validate.OneOf(["bool", "int", "uint", "double", "rational", "string"])
    )
    size = FieldUint(data_key="size", required=False)
    lower = fields.Float(data_key="lower", required=False)
    upper = fields.Float(data_key="upper", required=False)
    offset = fields.Float(data_key="offset", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "Variable":
        """Validate and create a Variable object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        # Check for unsupported fields
        for field in ("lower", "upper", "offset"):
            if getattr(obj, field, None) is not None:
                raise NotImplementedError(
                    f"feature not implemented: '{field}' must be omitted, but got {getattr(obj, field)}."
                )
        
        return Variable(
            name=obj.name,
            type=obj.type,
            size=getattr(obj, "size", None),
            lower=getattr(obj, "lower", None),
            upper=getattr(obj, "upper", None),
            offset=getattr(obj, "offset", None),
        )


@dataclass
class Variable(JsonSchemaResult):
    """Variable data class."""
    name: str
    type: Literal["bool", "int", "uint", "double", "rational", "string"]
    size: Optional[int] = None
    lower: Optional[float] = None
    upper: Optional[float] = None
    offset: Optional[float] = None

    @classmethod
    def class_schema(cls) -> Type:
        return VariableSchema


class ValuationFieldSchema(OneOfSchema):
    """Schema for valuation fields (padding or variable)."""
    type_schemas = {
        "padding": PaddingSchema,
        "variable": VariableSchema,
    }

    # custom discriminator field since the default 'type' field is used in VariableSchema
    type_field = "_discriminator"

    def get_obj_type(self, obj):
        """Determine which schema to use based on the object's attributes."""
        if hasattr(obj, "padding"):
            return "padding"
        elif hasattr(obj, "name") and hasattr(obj, "type"):
            return "variable"
        else:
            raise ValueError("Object must be either a padding or variable namespace")

    def load(self, json_data, *args, **kwargs):
        """Add discriminator field before loading."""
        assert isinstance(json_data, dict)
        json_data = dict(json_data, _discriminator="padding" if "padding" in json_data else "variable")
        return super().load(json_data, *args, **kwargs)

    def dump(self, obj, *args, **kwargs):
        """Remove discriminator field after dumping."""
        result = super().dump(obj, *args, **kwargs)
        assert isinstance(result, dict)
        result.pop("_discriminator", None)
        return result


class StateValuationsSchema(JsonSchema):
    """Schema for state valuations."""
    alignment = FieldUint(data_key="alignment", required=True)
    variables = fields.List(fields.Nested(ValuationFieldSchema), data_key="variables", required=True)

    @post_load
    def make_object(self, data: dict, **kwargs) -> "StateValuations":
        """Create a StateValuations object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return StateValuations(
            alignment=obj.alignment,
            variables=obj.variables,
        )


@dataclass
class StateValuations(JsonSchemaResult):
    """State valuations data class."""
    alignment: int
    variables: list[Union[Padding, Variable]]

    @classmethod
    def class_schema(cls) -> Type:
        return StateValuationsSchema

    def __str__(self) -> str:
        lines = [f"state valuations (alignment={self.alignment}):"]
        for var in self.variables:
            lines.append(f"  {var}")
        return "\n".join(lines)
