"""
Base JSON schema classes and utilities.
"""

import logging
from dataclasses import dataclass
from types import SimpleNamespace

from marshmallow import (
    INCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    validates_schema,
)

import umbi.datatypes

logger = logging.getLogger(__name__)


class FieldUint(fields.Int):
    """Custom marshmallow field for unsigned integers."""

    def _deserialize(self, value, attr, data, **kwargs):
        result = super()._deserialize(value, attr, data, **kwargs)
        if result is None:
            raise ValidationError("value is required")
        if result < 0:
            raise ValidationError(f"value {value} must be an unsigned integer")
        return result


class JsonSchema(Schema):
    """An abstract class to represent specific schemas that will follow."""

    # to allow unknown fields in the input data
    class Meta:
        unknown = INCLUDE

    @classmethod
    def schema_class(cls) -> type:
        """The class used as a representation of this schema result."""
        return JsonSchemaResult

    @post_load
    def make_object(self, data, **kwargs):
        """Create an object with attributes matching all the json fields. Notify about unrecognized fields."""
        extra_fields = set(data.keys()) - set(self.fields.keys())
        for f in extra_fields:
            logger.warning(f"JSON contains unrecognized field: {f}")

        obj = self.schema_class()()
        for field in self.fields:
            value = data.get(field, None)
            setattr(obj, field, value)
        return obj

    @classmethod
    def parse(cls, json_data, *args, **kwargs):
        """Parse from a json object.
        :raises: ValidationError if the json object does not conform to the schema
        """
        try:
            return cls().load(json_data, *args, **kwargs)
        except ValidationError as e:
            logger.error(f"{cls} validation error:")
            # messages is actually a json object, so we can pretty print it
            logger.error(umbi.datatypes.json_to_string(e.messages))  # type: ignore
            raise e


@dataclass
class JsonSchemaResult(SimpleNamespace):

    @classmethod
    def class_schema(cls) -> type:
        """The schema responsible for serialization of this class."""
        return JsonSchema

    @classmethod
    def from_json(cls, json_obj):
        return cls.class_schema()().parse(json_obj)

    def to_json(self):
        """Convert the current object to json and strip null values."""
        json_obj = self.class_schema()().dump(self)
        json_obj = umbi.datatypes.json_remove_none_dict_values(json_obj)
        return json_obj

    def __str__(self) -> str:
        """Convert to a string (json format)."""
        return umbi.datatypes.json_to_string(self.to_json())

    def validate(self):
        """Validate the current object syntactically."""
        self.from_json(self.to_json())
