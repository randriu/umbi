"""
Variable valuation schemas and classes.
"""

from marshmallow import fields, post_load, validate
from marshmallow_oneofschema.one_of_schema import OneOfSchema

import umbi.datatypes

from .json_schema import (
    JsonSchema,
    FieldUint,
)


class ValuationPaddingSchema(JsonSchema):
    """Schema for padding fields."""

    padding = FieldUint(data_key="padding", required=True)

    def make_object(self, data: dict, **kwargs) -> umbi.datatypes.StructPadding:
        """Create a Padding object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return umbi.datatypes.StructPadding(padding=obj.padding)

    def dump(self, obj, *args, **kwargs):
        assert isinstance(obj, umbi.datatypes.StructPadding)
        obj_dict = {
            "padding": obj.padding,
        }
        return obj_dict


class ValuationAttributeSchema(JsonSchema):
    """Schema for variable fields."""

    name = fields.String(data_key="name", required=True)
    type = fields.String(
        data_key="type",
        required=True,
        validate=validate.OneOf(["bool", "int", "uint", "double", "rational", "string"]),
    )
    size = FieldUint(data_key="size", required=False)
    lower = fields.Float(data_key="lower", required=False)
    upper = fields.Float(data_key="upper", required=False)
    offset = fields.Float(data_key="offset", required=False)

    @post_load
    def make_object(self, data: dict, **kwargs) -> umbi.datatypes.StructAttribute:
        """Validate and create a Variable object from the deserialized data."""
        obj = super().make_object(data, **kwargs)

        return umbi.datatypes.StructAttribute(
            name=obj.name,
            type=umbi.datatypes.CommonType(obj.type),
            size=getattr(obj, "size", None),
            lower=getattr(obj, "lower", None),
            upper=getattr(obj, "upper", None),
            offset=getattr(obj, "offset", None),
        )

    def dump(self, obj, *args, **kwargs):
        assert isinstance(obj, umbi.datatypes.StructAttribute)
        obj_dict = {
            "name": obj.name,
            "type": obj.type.value,
            "size": obj.size,
            "lower": obj.lower,
            "upper": obj.upper,
            "offset": obj.offset,
        }
        return obj_dict


class ValuationFieldSchema(OneOfSchema):
    """Schema for valuation fields (padding or variable)."""

    type_schemas = {
        "padding": ValuationPaddingSchema,
        "attribute": ValuationAttributeSchema,
    }

    # custom discriminator field since the default 'type' field is used in ValuationAttributeSchema
    type_field = "_discriminator"

    def get_obj_type(self, obj):
        """Determine which schema to use based on the object's attributes."""
        if hasattr(obj, "padding"):
            return "padding"
        elif hasattr(obj, "name") and hasattr(obj, "type"):
            return "attribute"
        else:
            raise ValueError("Object must be either a padding or attribute namespace")

    def load(self, json_data, *args, **kwargs):
        """Add discriminator field before loading."""
        assert isinstance(json_data, dict)
        json_data = dict(
            json_data,
            _discriminator="padding" if "padding" in json_data else "attribute",
        )
        return super().load(json_data, *args, **kwargs)

    def dump(self, obj, *args, **kwargs):
        """Remove discriminator field after dumping."""
        result = super().dump(obj, *args, **kwargs)
        assert isinstance(result, dict)
        result.pop("_discriminator", None)
        return result


class VariableValuationsSchema(JsonSchema):
    """Schema for variable valuations."""

    alignment = FieldUint(data_key="alignment", required=True)
    variables = fields.List(fields.Nested(ValuationFieldSchema), data_key="variables", required=True)

    @post_load
    def make_object(self, data: dict, **kwargs) -> umbi.datatypes.StructType:
        obj = super().make_object(data, **kwargs)
        return umbi.datatypes.StructType(
            alignment=obj.alignment,
            fields=obj.variables,
        )

    def dump(self, obj, *args, **kwargs):
        assert isinstance(obj, umbi.datatypes.StructType)
        variables = []
        for field in obj.fields:
            if isinstance(field, umbi.datatypes.StructPadding):
                variables.append(ValuationPaddingSchema().dump(field))
            else:
                assert isinstance(field, umbi.datatypes.StructAttribute)
                variables.append(ValuationAttributeSchema().dump(field))
        obj_dict = {
            "alignment": obj.alignment,
            "variables": variables,
        }
        return obj_dict
