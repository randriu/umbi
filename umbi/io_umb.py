import logging
import time
from types import SimpleNamespace

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates_schema,
)

import umbi


class FieldUint(fields.Int):
    """Custom marshmallow field for unsigned integers."""

    def _deserialize(self, value, attr, data, **kwargs):
        result = super()._deserialize(value, attr, data, **kwargs)
        if result < 0:
            raise ValidationError(f"value {value} must be an unsigned integer")
        return result


class JsonSchema(Schema):
    """An abstract class to represent specific schemas that will follow."""

    @post_load
    def make_object(self, data, **kwargs):
        """Create an object with attributes matching the json fields."""
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
        :returns None if any exception occurs"""
        try:
            return cls().load(json_obj)
        except ValidationError as err:
            logging.error(f"{cls} validation error:")
            logging.error(umbi.json_to_string(err.messages))
            raise err


class ModelDataSchema(JsonSchema):
    """Model data schema."""

    name = fields.String(data_key="name")
    version = fields.String(data_key="version")
    authors = fields.List(fields.String(), data_key="authors")
    description = fields.String(data_key="description")
    comment = fields.String(data_key="comment")
    doi = fields.String(data_key="doi")
    url = fields.String(data_key="url")


class FileDataSchema(JsonSchema):
    """File data schema."""

    tool = fields.String(data_key="tool")
    tool_version = fields.String(data_key="tool-version")
    creation_date = FieldUint(data_key="creation-date")
    parameters = fields.Raw(data_key="parameters")

    @classmethod
    def this_tool_object(cls):
        """Create an object with attributes set according to this tool."""
        obj = SimpleNamespace(**{field: None for field in cls().fields})
        obj.tool = umbi.__toolname__
        obj.tool_version = umbi.__version__
        obj.creation_date = int(time.time())
        return obj


class TransitionSystemSchema(JsonSchema):
    """ATS index file schema."""

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
        required=True,
        validate=validate.OneOf(["none", "double", "rational", "double-interval", "rational-interval"]),
    )


class AtomicPropositionSchema(JsonSchema):
    """Atomic proposition schema."""

    alias = fields.String(data_key="alias", required=False)
    description = fields.String(data_key="description", required=False)
    applies_to = fields.List(
        fields.String(validate=validate.OneOf(["states", "choices", "branches"])), data_key="applies-to", required=True
    )
    type = fields.String(
        data_key="type", required=False, validate=validate.OneOf(["bool"]), load_default="bool"
    )  # TODO discuss


class RewardSchema(JsonSchema):
    """Reward model schema."""

    alias = fields.String(data_key="alias")
    description = fields.String(data_key="description")
    applies_to = fields.List(
        fields.String(validate=validate.OneOf(["states", "choices", "branches"])),
        data_key="applies-to",
        required=True,
    )
    type = fields.String(
        data_key="type",
        required=True,
        validate=validate.OneOf(["double", "rational", "double-interval", "rational-interval"]),
    )
    lower = fields.Float(data_key="lower", required=False)
    upper = fields.Float(data_key="upper", required=False)


class VariableValuationSchema(JsonSchema):
    """Variable valuation schema."""

    alias = fields.String(data_key="alias", required=False)
    description = fields.String(data_key="description", required=False)
    applies_to = fields.List(
        fields.String(validate=validate.OneOf(["states", "choices", "branches"])), data_key="applies-to", required=True
    )
    type = fields.String(
        data_key="type", required=True, validate=validate.OneOf(["bool", "int", "int32", "uint32", "int64", "uint64"])
    )

    @post_load
    def make_object(self, data, **kwargs):
        obj = super().make_object(data, **kwargs)
        if obj.type == "int":  # TODO discuss
            logging.warning("variable annotation type is int, interpreting as int32")
            obj.type = "int32"
        return obj


class AnnotationSchema(JsonSchema):
    """Single annotation schema."""

    aps = fields.Dict(
        keys=fields.String(), values=fields.Nested(AtomicPropositionSchema), data_key="aps", required=False
    )
    rewards = fields.Dict(keys=fields.String(), values=fields.Nested(RewardSchema), data_key="rewards", required=False)
    variables = fields.Dict(
        keys=fields.String(), values=fields.Nested(VariableValuationSchema), data_key="variables", required=False
    )


class AtsInfoSchema(JsonSchema):
    """ATS index file schema."""

    format_version = FieldUint(data_key="format-version", required=True)
    format_revision = FieldUint(data_key="format-revision", required=True)
    model_data = fields.Nested(ModelDataSchema, data_key="model-data", required=False)
    file_data = fields.Nested(FileDataSchema, data_key="file-data", required=False)
    transition_system = fields.Nested(TransitionSystemSchema, data_key="transition-system", required=True)
    annotations = fields.Nested(AnnotationSchema, data_key="annotations", required=False)

    @classmethod
    def empty_object(cls):
        """Create an empty object with attributes (set to None) corresponding to the fields of schema."""
        obj = SimpleNamespace(**{field: None for field in cls().fields})
        obj.format_version = umbi.__format_version__
        obj.format_revision = umbi.__format_revision__
        obj.model_data = ModelDataSchema.empty_object()
        obj.file_data = FileDataSchema.empty_object()
        obj.transition_system = TransitionSystemSchema.empty_object()
        obj.annotations = AnnotationSchema.empty_object()
        return obj


def read_index_file(reader: umbi.TarReader, ats: umbi.ExplicitAts):
    json_obj = reader.read("index.json", "json")
    umbi.json_show(json_obj)
    ats.info = AtsInfoSchema.from_json(json_obj)


def write_index_file(writer: umbi.TarWriter, ats: umbi.ExplicitAts):
    info = AtsInfoSchema().empty_object()
    info.model_data = ats.info.model_data
    info.file_data = FileDataSchema.this_tool_object()
    info.transition_system = ats.info.transition_system
    info.annotations = ats.info.annotations
    # FIXME variable type int32->int
    if info.annotations.variables is not None:
        for key, annotation in info.annotations.variables.items():
            if annotation.type == "int32":
                logging.warning("variable annotation type is int32, storing as int in the index file")
                annotation.type = "int"
    json_obj = AtsInfoSchema().dump(info)
    json_obj = umbi.json_remove_none(json_obj)
    umbi.json_show(json_obj)
    writer.add(json_obj, "index.json", "json")


def read_state_files(reader: umbi.TarReader, ats: umbi.ExplicitAts):
    ts = ats.info.transition_system
    ats.initial_states = reader.read("initial-states.bin", "bool")
    if ts.num_players > 0:
        ats.state_choices = reader.read("state-to-choice.bin", "uint64", csr=True)
    if ts.num_players > 1:
        ats.state_to_player = reader.read("state-to-player.bin", "uint64")
    if ts.time in ["stochastic", "urgent-stochastic"]:
        ats.exit_rates = reader.read("exit-rates.bin", "double")  # TODO discuss


def write_state_files(writer: umbi.TarWriter, ats: umbi.ExplicitAts):
    ts = ats.info.transition_system
    writer.add(umbi.indices_to_bitvector(ats.initial_states, ts.num_states), "initial-states.bin", "bool")
    if ts.num_players > 0:
        writer.add(umbi.ranges_to_row_start(ats.state_choices), "state-to-choice.bin", "uint64")
    if ts.num_players > 1:
        writer.add(ats.state_to_player, "state-to-player.bin", "uint64")
    if ts.time in ["stochastic", "urgent-stochastic"]:
        writer.add(ats.exit_rates, "exit-rates.bin", "double")  # TODO discuss


def read_branch_files(reader: umbi.TarReader, ats: umbi.ExplicitAts):
    ts = ats.info.transition_system
    if ts.num_branches > ts.num_choices:
        ats.choice_branches = reader.read("choice-to-branch.bin", "uint64", csr=True)
    ats.branch_target = reader.read("branch-to-target.bin", "uint64")
    assert ts.branch_probability_type == "double", "not implemented yet"
    ats.branch_probabilities = reader.read("branch-probabilities.bin", "double")


def write_branch_files(writer: umbi.TarWriter, ats: umbi.ExplicitAts):
    ts = ats.info.transition_system
    if ts.num_branches > ts.num_choices:
        writer.add(ats.choice_branches, "choice-to-branch.bin", "uint64", csr=True)
    writer.add(ats.branch_target, "branch-to-target.bin", "uint64")
    assert ts.branch_probability_type == "double", "not implemented yet"
    writer.add(ats.branch_probabilities, "branch-probabilities.bin", "double")


def read_action_files(reader: umbi.TarReader, ats: umbi.ExplicitAts):
    ts = ats.info.transition_system
    if ts.time == "discrete":
        if ts.num_players > 0:
            ats.choice_to_action = reader.read("choice-to-action.bin", "uint32")
    else:
        ats.branch_to_action = reader.read("branch-to-action.bin", "uint32")
    if "action-to-action-strings.bin" in reader.filenames and "action-strings.bin" in reader.filenames:
        action_string_offset = reader.read("action-to-action-strings.bin", "uint32")
        action_string_chars = reader.read("action-strings.bin", "char")
        ats.action_to_string = []
        for action in range(ts.num_actions):
            action_string = action_string_chars[action_string_offset[action] : action_string_offset[action + 1]]
            ats.action_to_string.append(action_string)


def write_action_files(writer: umbi.TarWriter, ats: umbi.ExplicitAts):
    ts = ats.info.transition_system
    if ts.time == "discrete":
        if ts.num_players > 0:
            writer.add(ats.choice_to_action, "choice-to-action.bin", "uint32")
    else:
        writer.add(ats.branch_to_action, "branch-to-action.bin", "uint32")
    if ats.action_to_string is not None:
        action_string_offset = [0]
        action_string_chars = ""
        for action, string in enumerate(ats.action_to_string):
            action_string_chars += string
            action_string_offset.append(len(action_string_chars))
        writer.add(action_string_offset, "action-to-action-strings.bin", "uint32")
        writer.add(action_string_chars, "action-strings.bin", "char")


def read_annotation(reader: umbi.TarReader, annotation_label: str, annotation_dict: dict[str, object]):
    if annotation_dict is None:
        return
    path = f"annotations/{annotation_label}"
    for key, annotation in annotation_dict.items():
        annotation.data = dict()
        for applies in annotation.applies_to:
            filename = f"{path}/{key}/for-{applies}/values.bin"
            # logging.debug(annotation.type)
            annotation.data[applies] = reader.read(filename, annotation.type)


def write_annotation(writer: umbi.TarWriter, annotation_label: str, annotation_dict: dict[str, object]):
    if annotation_dict is None:
        return
    path = f"annotations/{annotation_label}"
    for key, annotation in annotation_dict.items():
        for applies in annotation.applies_to:
            assert applies in annotation.data
            filename = f"{path}/{key}/for-{applies}/values.bin"
            if annotation.type == "int":
                logging.warning("variable annotation type is int, interpreting as int32")
                annotation.type = "int32"
            writer.add(annotation.data[applies], filename, annotation.type)


def read_annotation_files(reader: umbi.TarReader, ats: umbi.ExplicitAts):
    read_annotation(reader, "aps", ats.info.annotations.aps)
    read_annotation(reader, "rewards", ats.info.annotations.rewards)
    read_annotation(reader, "variables", ats.info.annotations.variables)


def write_annotation_files(writer: umbi.TarWriter, ats: umbi.ExplicitAts):
    write_annotation(writer, "aps", ats.info.annotations.aps)
    write_annotation(writer, "rewards", ats.info.annotations.rewards)
    write_annotation(writer, "variables", ats.info.annotations.variables)


def read_umb(tarpath: str) -> umbi.ExplicitAts:
    """Read ATS from a .umb file."""
    reader = umbi.TarReader(tarpath)
    ats = umbi.ExplicitAts()
    read_index_file(reader, ats)
    read_state_files(reader, ats)
    read_branch_files(reader, ats)
    read_action_files(reader, ats)
    read_annotation_files(reader, ats)
    reader.warn_unread_files()
    # ats.validate()
    return ats


def write_umb(ats: umbi.ExplicitAts, tarpath: str):
    """Store ATS to a .umb file."""
    # ats.validate()
    writer = umbi.TarWriter()
    write_index_file(writer, ats)
    write_state_files(writer, ats)
    write_branch_files(writer, ats)
    write_action_files(writer, ats)
    write_annotation_files(writer, ats)
    writer.write(tarpath)

    # sanity check: try to read the resulting file
    try:
        read_umb(tarpath)
    except Exception as e:
        logging.warning(f"failed to read the resulted file {tarpath}, printing the error message below:")
        logging.warning(e)
