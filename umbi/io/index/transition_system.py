"""
Transition system schemas and classes.
"""

from dataclasses import dataclass
from typing import Optional, Type
from marshmallow import fields, validate, post_load

from .json_schema import *


class TransitionSystemSchema(JsonSchema):
    """Transition system schema."""

    time = fields.String(
        data_key="time", required=True, validate=validate.OneOf(["discrete", "stochastic", "urgent-stochastic"])
    )
    num_players = fields.Int(data_key="#players", required=True, validate=validate.Range(min=0))
    num_states = fields.Int(data_key="#states", required=True, validate=validate.Range(min=0))
    num_initial_states = fields.Int(data_key="#initial-states", required=True, validate=validate.Range(min=0))
    num_choices = fields.Int(data_key="#choices", required=True, validate=validate.Range(min=0))
    num_actions = fields.Int(data_key="#actions", required=True, validate=validate.Range(min=0))
    num_branches = fields.Int(data_key="#branches", required=True, validate=validate.Range(min=0))
    num_observations = fields.Int(data_key="#observations", required=False, validate=validate.Range(min=0))

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

    @post_load
    def make_object(self, data: dict, **kwargs) -> "TransitionSystem":
        """Create a TransitionSystem object from the deserialized data."""
        obj = super().make_object(data, **kwargs)
        return TransitionSystem(
            time=obj.time,
            num_players=obj.num_players,
            num_states=obj.num_states,
            num_initial_states=obj.num_initial_states,
            num_choices=obj.num_choices,
            num_actions=obj.num_actions,
            num_branches=obj.num_branches,
            num_observations=obj.num_observations,
            branch_probability_type=obj.branch_probability_type,
            exit_rate_type=obj.exit_rate_type,
        )


@dataclass
class TransitionSystem(JsonSchemaResult):
    """Transition system data class."""
    time: str
    num_players: int
    num_states: int
    num_initial_states: int
    num_choices: int
    num_actions: int
    num_branches: int
    num_observations: Optional[int] = None
    branch_probability_type: Optional[str] = None
    exit_rate_type: Optional[str] = None

    @classmethod
    def class_schema(cls) -> Type:
        return TransitionSystemSchema
