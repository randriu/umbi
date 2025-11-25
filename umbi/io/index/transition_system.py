"""
Transition system schemas and classes.
"""

from dataclasses import dataclass
from typing import Literal, Type

from marshmallow import fields, post_load, validate

from .json_schema import *


class TransitionSystemSchema(JsonSchema):
    """Transition system schema."""

    time = fields.String(
        data_key="time", required=True, validate=validate.OneOf(["discrete", "stochastic", "urgent-stochastic"])
    )
    num_players = fields.Int(data_key="#players", required=True, validate=validate.Range(min=0))
    num_states = fields.Int(data_key="#states", required=True, validate=validate.Range(min=1))
    num_initial_states = fields.Int(data_key="#initial-states", required=True, validate=validate.Range(min=0))
    num_choices = fields.Int(data_key="#choices", required=True, validate=validate.Range(min=1))
    num_actions = fields.Int(data_key="#choice-actions", required=True, validate=validate.Range(min=0))
    num_branches = fields.Int(data_key="#branches", required=True, validate=validate.Range(min=0))
    num_branch_actions = fields.Int(data_key="#branch-actions", required=True, validate=validate.Range(min=0))
    num_observations = fields.Int(data_key="#observations", required=True, validate=validate.Range(min=0))
    observations_apply_to = fields.String(
        data_key="observations-apply-to", required=False, validate=validate.OneOf(["states", "choices", "branches"])
    )

    # coordination WIP marker

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

    @classmethod
    def schema_class(cls) -> type:
        return TransitionSystem


@dataclass
class TransitionSystem(JsonSchemaResult):
    """Transition system data class."""

    time: Literal["discrete", "stochastic", "urgent-stochastic"] = "discrete"
    num_players: int = 0
    num_states: int = 0
    num_initial_states: int = 0
    num_choices: int = 0
    num_actions: int = 0
    num_branches: int = 0
    num_branch_actions: int = 0
    num_observations: int = 0
    observations_apply_to: Literal["states", "choices", "branches"] | None = None
    branch_probability_type: Literal["double", "rational", "double-interval", "rational-interval"] | None = None
    exit_rate_type: Literal["double", "rational", "double-interval", "rational-interval"] | None = None

    @classmethod
    def class_schema(cls) -> Type:
        return TransitionSystemSchema
