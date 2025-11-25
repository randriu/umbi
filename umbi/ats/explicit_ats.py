from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from umbi.datatypes import (
    CommonType,
    Interval,
    Numeric,
    StructType,
    vector_common_numeric_type,
)

from .annotation import *
from .model_info import ModelInfo


class TimeType(str, Enum):
    """Time types for transition systems."""

    DISCRETE = "discrete"
    STOCHASTIC = "stochastic"
    URGENT_STOCHASTIC = "urgent-stochastic"


@dataclass
class ExplicitAts:
    """Explicit container for an annotated transition system (ATS)."""

    # TODO annotate fields, describe optionality and defaults

    model_info: ModelInfo | None = None
    time: TimeType = TimeType.DISCRETE
    num_states: int = 0

    num_players: int = 0
    state_to_player: list[int] | None = None

    num_initial_states: int = 0
    state_is_initial: list[bool] = field(default_factory=list)

    num_choices: int = 0
    # CSR list of length num_states + 1
    state_to_choice: list[int] | None = None

    num_branches: int = 0
    choice_to_branch: list[int] | None = None
    branch_to_target: list[int] | None = None
    branch_probabilities: list[Numeric] | None = None

    state_is_markovian: list[bool] | None = None
    state_exit_rate: list[Numeric] | None = None

    # actions associated with choices
    num_actions: int = 0
    choice_to_action: list[int] | None = None
    action_strings: list[str] | None = None

    # actions associated with branches
    num_branch_actions: int = 0
    branch_to_branch_action: list[int] | None = None
    branch_action_strings: list[str] | None = None

    reward_annotations: dict[str, RewardAnnotation] = field(default_factory=dict)
    ap_annotations: dict[str, AtomicPropositionAnnotation] = field(default_factory=dict)
    observation_annotation: ObservationAnnotation | None = None

    # TODO consolidate into one structure
    state_valuations: StructType | None = None
    state_valuations_values: list[dict] | None = None

    def __eq__(self, other):
        # TODO implement
        if not isinstance(other, ExplicitAts):
            return False
        if self.time != other.time:
            return False
        if self.num_players != other.num_players:
            return False
        if self.state_to_player != other.state_to_player:
            return False
        if self.num_states != other.num_states:
            return False
        if self.num_actions != other.num_actions:
            return False
        return True

    @property
    def initial_states(self) -> list[int]:
        """Get the list of the initial states."""
        return [i for i, is_initial in enumerate(self.state_is_initial) if is_initial]

    def set_initial_states(self, initial_states: list[int]):
        """Set the initial states."""
        self.state_is_initial = [False] * self.num_states
        for s in initial_states:
            if s >= self.num_states:
                raise ValueError(f"Invalid initial state {s}, must be < {self.num_states}.")
            self.state_is_initial[s] = True
        self.num_initial_states = len(initial_states)

    @property
    def markovian_states(self) -> list[int]:
        """Get the list of the markovian states."""
        if self.state_is_markovian is None:
            raise ValueError("state_is_markovian is not set")
        return [i for i, is_markovian in enumerate(self.state_is_markovian) if is_markovian]

    def get_branch_probability(self, branch_id: int) -> Numeric:
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
        # TODO what is the default here?

    def get_action_name(self, action_id: int) -> str:
        """Get the name of an action identifier"""
        if self.action_strings is not None:
            return self.action_strings[action_id]
        raise ValueError("action strings are not set")

    def state_choice_range(self, state: int) -> Iterable[int]:
        """Return the choice range of the given state."""
        if self.state_to_choice is not None:
            assert state <= self.num_states
            return range(self.state_to_choice[state], self.state_to_choice[state + 1])
        else:
            return range(state, state + 1)

    def choice_branch_range(self, choice: int) -> Iterable[int]:
        """Return the branch range of the given choice."""
        if self.choice_to_branch is not None:
            assert choice <= self.num_choices
            return range(self.choice_to_branch[choice], self.choice_to_branch[choice + 1])
        else:
            return range(choice, choice + 1)

    @property
    def branch_probability_type(self) -> CommonType | None:
        if self.branch_probabilities is None:
            return None
        return vector_common_numeric_type(self.branch_probabilities)

    @property
    def exit_rate_type(self) -> CommonType | None:
        if self.state_exit_rate is None:
            return None
        return vector_common_numeric_type(self.state_exit_rate)

    @property
    def reward_annotation_names(self) -> list[str]:
        """Get the names of all reward annotations."""
        return list(self.reward_annotations.keys())

    def add_reward_annotation(self, annotation: RewardAnnotation):
        """Add a reward annotation."""
        if annotation.name in self.reward_annotations:
            raise ValueError(f"reward annotation with name {annotation.name} already exists")
        self.reward_annotations[annotation.name] = annotation

    def get_reward_annotation(self, name: str) -> RewardAnnotation:
        """Get the reward annotation with the given name."""
        if name not in self.reward_annotations:
            raise ValueError(f"reward annotation with name {name} does not exist")
        return self.reward_annotations[name]

    @property
    def atomic_proposition_names(self) -> list[str]:
        """Get the names of all atomic proposition annotations."""
        return list(self.ap_annotations.keys())

    def add_ap_annotation(self, annotation: AtomicPropositionAnnotation):
        """Add an atomic proposition annotation."""
        if annotation.name in self.ap_annotations:
            raise ValueError(f"AP annotation with name {annotation.name} already exists")
        self.ap_annotations[annotation.name] = annotation

    def get_ap_annotation(self, name: str) -> AtomicPropositionAnnotation:
        """Get the atomic proposition annotation with the given name."""
        if name not in self.ap_annotations:
            raise ValueError(f"AP annotation with name {name} does not exist")
        return self.ap_annotations[name]

    @property
    def has_observations(self) -> bool:
        return self.observation_annotation is not None

    @property
    def has_state_valuations(self) -> bool:
        return self.state_valuations is not None

    def validate(self):
        # TODO implement

        if not self.num_states > 0:
            raise ValueError("expected num_states > 0")

        if self.num_players > 1:
            if self.state_to_player is None:
                raise ValueError("num_players > 1 but state_to_player is None")
            if len(self.state_to_player) != self.num_states:
                raise ValueError("expected len(state_to_player) == num_states")

        if self.num_initial_states != len(self.initial_states):
            raise ValueError("expected num_initial_states == len(initial_states)")

        if self.state_to_choice is not None:
            if len(self.state_to_choice) != self.num_states + 1:
                raise ValueError("expected len(state_to_choice) == num_states+1")
        if self.choice_to_branch is not None:
            if len(self.choice_to_branch) != self.num_choices + 1:
                raise ValueError("expected len(choice_to_branch) == num_choices+1")
        if self.branch_to_target is not None:
            if len(self.branch_to_target) != self.num_branches:
                raise ValueError("expected len(branch_to_target) == num_branches")

        for reward_annotation in self.reward_annotations.values():
            reward_annotation.validate()
        for ap_annotation in self.ap_annotations.values():
            ap_annotation.validate()
        if self.observation_annotation is not None:
            self.observation_annotation.validate()
