"""
Parsing the .umb index file.
"""

import logging

logger = logging.getLogger(__name__)
import time
from types import SimpleNamespace

from marshmallow import (
    INCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates,
    validates_schema,
)

import umbi
import umbi.io


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

    """ To allow unknown fields in the input data. """

    class Meta:
        unknown = INCLUDE

    @post_load
    def make_object(self, data, **kwargs) -> SimpleNamespace:
        """Create an object with attributes matching all the json fields. Notify about unrecognized fields."""
        extra_fields = set(data.keys()) - set(self.fields.keys())
        for f in extra_fields:
            logger.warning(f"JSON contains unrecognized field: {f}")

        for field in self.fields:
            if field not in data:
                data[field] = None
        return SimpleNamespace(**data)

    @classmethod
    def empty_object(cls):
        """Create an empty object with attributes (set to None) corresponding to the fields of schema."""
        return SimpleNamespace(**{field: None for field in cls().fields})

    @validates_schema
    def validate_fields(self, data, **kwargs):
        """A method that is called upon the creation of the object to validate the fields."""
        pass

    @classmethod
    def from_json(cls, json_obj) -> SimpleNamespace:
        """Parse from a json object.
        :raises: ValidationError if the json object does not conform to the schema
        """
        try:
            return cls().load(json_obj)  # type: ignore[return-value] since post_load will return SimpleNamespace
        except ValidationError as err:
            logger.error(f"{cls} validation error:")
            logger.error(umbi.io.json_to_string(err.messages))
            raise err


class ModelDataSchema(JsonSchema):
    """Model data schema."""

    name = fields.String(data_key="name", required=False)
    version = fields.String(data_key="version", required=False)
    authors = fields.List(fields.String(), data_key="authors", required=False)
    description = fields.String(data_key="description", required=False)
    comment = fields.String(data_key="comment", required=False)
    doi = fields.String(data_key="doi", required=False)
    url = fields.String(data_key="url", required=False)


class FileDataSchema(JsonSchema):
    """File data schema."""

    tool = fields.String(data_key="tool", required=False)
    tool_version = fields.String(data_key="tool-version", required=False)
    creation_date = FieldUint(data_key="creation-date", required=False)
    parameters = fields.Raw(data_key="parameters", required=False)

    @classmethod
    def this_tool_object(cls, parameters: umbi.io.JsonLike | None = None):
        """
        Create a file-data object that reflects that umbi was used to create this index file.
        :param parameters: (optional) umbi parameters
        """
        obj = cls.empty_object()
        obj.tool = umbi.__toolname__
        obj.tool_version = umbi.__version__
        obj.creation_date = int(time.time())
        obj.parameters = parameters
        return obj


class TransitionSystemSchema(JsonSchema):
    """Transition system schema."""

    time = fields.String(
        data_key="time", required=True, validate=validate.OneOf(["discrete", "stochastic", "urgent-stochastic"])
    )
    num_players = FieldUint(data_key="#players", required=True)
    num_states = FieldUint(data_key="#states", required=True)
    num_initial_states = FieldUint(data_key="#initial-states", required=True)
    num_choices = FieldUint(data_key="#choices", required=True)
    num_actions = FieldUint(data_key="#actions", required=True)
    num_branches = FieldUint(data_key="#branches", required=True)

    branch_probability_type = fields.String(
        data_key="branch-probability-type",
        required=False,
        validate=validate.OneOf(["double", "rational", "double-interval", "rational-interval"]),
    )
    exit_rate_type = fields.String(
        data_key="exit-rate-type",
        required=False,
        validate=validate.OneOf(["double", "rational", "double-interval", "rational-interval"]),
    )


class AnnotationSchema(JsonSchema):
    """An annotation schema."""

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


class PaddingSchema(JsonSchema):
    padding = FieldUint(data_key="padding", required=True)

    @validates("padding")
    def validate_padding(self, value):
        if value <= 0:
            raise ValidationError("padding must be a positive integer")


class VariableSchema(JsonSchema):
    name = fields.String(data_key="name", required=True)
    type = fields.String(
        data_key="type", required=True, validate=validate.OneOf(["bool", "int", "uint", "double", "rational", "string"])
    )
    size = FieldUint(data_key="size", required=False)
    lower = fields.Float(data_key="lower", required=False)
    upper = fields.Float(data_key="upper", required=False)
    offset = fields.Float(data_key="offset", required=False)


class StateValuationsSchema(JsonSchema):
    alignment = FieldUint(required=True)
    variables = fields.List(fields.Raw(), required=True)

    @validates("variables")
    def validate_variables(self, value):
        if not isinstance(value, list):  # is this necessary?
            raise ValidationError("variables must be a list")
        for v in value:
            if not isinstance(v, dict):
                raise ValidationError("each variable must be a dict")
            if "padding" in v:
                try:
                    PaddingSchema().load(v)
                except ValidationError as err:
                    raise ValidationError(f"invalid padding variable: {err.messages}")
            elif "name" in v and "type" in v:
                try:
                    VariableSchema().load(v)
                except ValidationError as err:
                    raise ValidationError(f"invalid variable: {err.messages}")
            else:
                raise ValidationError("variable must be either a padding or variable dict")


class AnnotationsSchema(JsonSchema):
    """A schema annotations."""

    rewards = fields.Dict(
        keys=fields.String(), values=fields.Nested(AnnotationSchema), data_key="rewards", required=False
    )
    aps = fields.Dict(keys=fields.String(), values=fields.Nested(AnnotationSchema), data_key="aps", required=False)
    state_valuations = fields.Nested(StateValuationsSchema, data_key="state-valuations", required=False)

    @classmethod
    def empty_object(cls):
        """Create an empty object with attributes (set to None) corresponding to the fields of schema."""
        obj = super().empty_object()
        obj.rewards = dict[str, SimpleNamespace]()
        obj.aps = dict[str, SimpleNamespace]()
        obj.state_valuations = dict[str, SimpleNamespace]()
        return obj


class UmbIndexSchema(JsonSchema):
    """UMB index file schema."""

    format_version = FieldUint(data_key="format-version", required=True)
    format_revision = FieldUint(data_key="format-revision", required=True)
    model_data = fields.Nested(ModelDataSchema, data_key="model-data", required=False)
    file_data = fields.Nested(FileDataSchema, data_key="file-data", required=False)
    transition_system = fields.Nested(TransitionSystemSchema, data_key="transition-system", required=True)
    annotations = fields.Nested(AnnotationsSchema, data_key="annotations", required=False)

    @classmethod
    def empty_object(cls):
        """Create an empty object with attributes (set to None) corresponding to the fields of schema."""
        obj = super().empty_object()
        obj.format_version = umbi.__format_version__
        obj.format_revision = umbi.__format_revision__
        obj.model_data = ModelDataSchema.empty_object()
        obj.file_data = FileDataSchema.empty_object()
        obj.transition_system = TransitionSystemSchema.empty_object()
        obj.annotations = AnnotationsSchema.empty_object()
        return obj


class UmbIndex:
    """A high-level representation of the .umb index file. This is basically UmbIndexSchema, but with a more convenient interface."""

    def __init__(self):
        self.format_version = umbi.__format_version__
        self.format_revision = umbi.__format_revision__
        self.model_data = ModelDataSchema.empty_object()
        self.file_data = FileDataSchema.empty_object()
        self.transition_system = TransitionSystemSchema.empty_object()
        self.annotations = AnnotationsSchema.empty_object()

    @classmethod
    def from_json(cls, json_obj: umbi.io.JsonLike) -> "UmbIndex":
        """Parse from a json object."""
        info = UmbIndexSchema.from_json(json_obj)
        obj = cls()
        for field in [
            "format_version",
            "format_revision",
            "model_data",
            "file_data",
            "transition_system",
            "annotations",
        ]:
            setattr(obj, field, getattr(info, field))
        return obj

    def copy(self) -> "UmbIndex":
        """Create a shallow copy."""
        other = UmbIndex()
        for field in [
            "format_version",
            "format_revision",
            "model_data",
            "file_data",
            "transition_system",
            "annotations",
        ]:
            setattr(other, field, getattr(self, field))
        return other

    def to_json(self, use_this_tool_file_data: bool = False) -> umbi.io.JsonLike:
        """
        Convert to a json object.
        :param use_this_tool_file_data: if True, the file-data field will be set to the values corresponding to this tool
        """
        info = UmbIndexSchema().empty_object()
        for field in [
            "format_version",
            "format_revision",
            "model_data",
            "file_data",
            "transition_system",
            "annotations",
        ]:
            setattr(info, field, getattr(self, field))
        if use_this_tool_file_data:
            info.file_data = FileDataSchema.this_tool_object()
        json_obj = UmbIndexSchema().dump(info)
        assert isinstance(json_obj, umbi.io.JsonLike)
        json_obj = umbi.io.json_remove_none_dict_values(json_obj)
        return json_obj

    def __str__(self) -> str:
        """Convert to a string (json format)."""
        return umbi.io.json_to_string(self.to_json())
