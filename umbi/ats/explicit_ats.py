from umbi.datatypes import CommonType, StructType, Numeric, Interval

from dataclasses import dataclass, field
from .model_info import ModelInfo

from typing import Iterable
from enum import Enum

class TimeType(str, Enum):
    """Time types for transition systems."""
    DISCRETE = "discrete"
    STOCHASTIC = "stochastic"
    URGENT_STOCHASTIC = "urgent-stochastic"


@dataclass
class ExplicitAts:
    """Explicit container for an annotated transition system (ATS)."""

    #TODO annotate fields, describe optionality and defaults

    model_info: ModelInfo | None = None
    time: TimeType = TimeType.DISCRETE
    num_states: int = 0

    num_players: int = 0
    state_to_player: list[int] | None = None

    num_initial_states: int = 0
    initial_states: list[int] = field(default_factory=list)

    num_observations: int | None = None

    num_choices: int = 0
    state_to_choice: list[int] | None = None

    markovian_states: list[int] | None = None
    exit_rate_type: CommonType | None = None
    state_exit_rate: list[Numeric | Interval] | None = None # will become obsolete

    num_actions: int = 1
    choice_to_action: list[int] | None = None
    action_strings: list[str] | None = None

    num_branches: int = 0
    choice_to_branch: list[int] | None = None
    branch_to_target: list[int] | None = None
    branch_probability_type: CommonType | None = None # will become obsolete
    branch_probabilities: list[Numeric | Interval] | None = None

    #TODO consolidate each into one structure
    from ..io.index import Annotation
    rewards: dict[str, Annotation] | None = None
    rewards_values: dict[str, dict[str, list]] | None = None

    aps: dict[str, Annotation] | None = None
    aps_values: dict[str, dict[str, list]] | None = None

    state_valuations: StructType | None = None
    state_valuations_values: list[dict] | None = None

    def __eq__(self, other):
        #TODO implement
        if not isinstance(other, ExplicitAts):
            return False
        if self.num_states != other.num_states:
            return False
        if self.num_players != other.num_players:
            return False
        if self.num_actions != other.num_actions:
            return False
        return True

    @property
    def has_state_valuations(self) -> bool:
        return self.state_valuations is not None

    def get_branch_probability(self, branch_id: int) -> Numeric | Interval:
        if self.branch_probabilities is not None:
            return self.branch_probabilities[branch_id]
        return 1.0

    def get_branch_target(self, branch_id: int) -> int:
        if self.branch_to_target is not None:
            return self.branch_to_target[branch_id]
        raise RuntimeError("Branches must have targets in UMBI.")

    def get_choice_action(self, choice_id: int) -> int:
        """Get the action identifier for a choice"""
        if self.choice_to_action is not None:
            return self.choice_to_action[choice_id]
        raise NotImplementedError("Getting actions when not set are not implemented.")
        #TODO what is the default here?

    def get_action_name(self, action_id: int) -> str:
        """Get the name of an action identifier"""
        if self.action_strings is not None:
            return self.action_strings[action_id]
        raise NotImplementedError("Getting action names when not set are not implemented.")
        #TODO what is the default here?

    def choice_range(self, state: int) -> Iterable[int]:
        """Return the choice range of the given state."""
        if self.state_to_choice is not None:
            assert state <= self.num_states
            return range(self.state_to_choice[state], self.state_to_choice[state + 1])
        else:
            return range(state, state+1)

    def branch_range(self, choice: int) -> Iterable[int]:
        """Return the branch range of the given choice."""
        if self.choice_to_branch is not None:
            assert choice <= self.num_choices
            return range(self.choice_to_branch[choice], self.choice_to_branch[choice + 1])
        else:
            return range(choice, choice+1)

    def validate(self):
        # TODO implement

        # will become obsolete when we implement automatic detection of types
        NUMERIC_AND_INTERVAL_DATATYPES = [
            CommonType.DOUBLE, CommonType.RATIONAL,
            CommonType.DOUBLE_INTERVAL, CommonType.RATIONAL_INTERVAL,
        ]
        if self.exit_rate_type is not None:
            if self.exit_rate_type not in NUMERIC_AND_INTERVAL_DATATYPES:
                raise ValueError(f"invalid exit rate type {self.exit_rate_type}")
        if self.branch_probability_type is not None:
            if self.branch_probability_type not in NUMERIC_AND_INTERVAL_DATATYPES:
                raise ValueError(f"invalid branch probability type {self.branch_probability_type}")

        if not self.num_states > 0:
            raise ValueError("expected num_states > 0")

        if self.num_players > 1:
            if self.state_to_player is None:
                raise ValueError("num_players > 1 but state_to_player is None")
            if len(self.state_to_player) != self.num_states:
                raise ValueError("expected len(state_to_player) == num_states")

        if self.num_initial_states != sum(self.initial_states):
            raise ValueError("expected num_initial_states == sum(initial_states)")

        if self.state_to_choice is not None:
            if len(self.state_to_choice) != self.num_states+1:
                raise ValueError("expected len(state_to_choice) == num_states+1")
        if self.choice_to_branch is not None:
            if len(self.choice_to_branch) != self.num_choices+1:
                raise ValueError("expected len(choice_to_branch) == num_choices+1")
        if self.branch_to_target is not None:
            if len(self.branch_to_target) != self.num_branches:
                raise ValueError("expected len(branch_to_target) == num_branches")
        if self.has_state_valuations:
            if self.state_valuations_values is None:
                raise ValueError("state_valuations is set but state_valuations_values is None")
            if len(self.state_valuations_values) != self.num_states:
                raise ValueError("expected len(state_valuations_values) == num_states")

