"""
Variable valuation schemas and classes.
"""

from dataclasses import dataclass
from marshmallow import fields, post_load, validate
from marshmallow_oneofschema.one_of_schema import OneOfSchema

from .json_schema import *

import umbi.datatypes

class ValuationPaddingSchema(JsonSchema):
    """Schema for padding fields."""
    padding = FieldUint(data_key="padding", required=True)

    @post_load
    def make_object(self, data: dict, **kwargs) -> umbi.datatypes.StructPadding:
        """Create a Padding object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return umbi.datatypes.StructPadding(padding=obj.padding)


class ValuationAttributeSchema(JsonSchema):
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
    def make_object(self, data: dict, **kwargs) -> umbi.datatypes.StructAttribute:
        """Validate and create a Variable object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        # Check for unsupported fields
        for field in ("lower", "upper", "offset"):
            if getattr(obj, field, None) is not None:
                raise NotImplementedError(
                    f"feature not implemented: '{field}' must be omitted, but got {getattr(obj, field)}."
                )

        return umbi.datatypes.StructAttribute(
            name=obj.name,
            type=obj.type,
            size=getattr(obj, "size", None),
            lower=getattr(obj, "lower", None),
            upper=getattr(obj, "upper", None),
            offset=getattr(obj, "offset", None),
        )



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
        json_data = dict(json_data, _discriminator="padding" if "padding" in json_data else "attribute")
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
        obj_dict = {
            "alignment": obj.alignment,
            "variables": self.fields["variables"].serialize("variables", {"variables": obj.fields}),
        }
        return obj_dict

