import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from umbi.datatypes import (
    CommonType,
    Numeric,
    can_promote_vector_to,
)
from .annotations import (
    RewardAnnotation,
    AtomicPropositionAnnotation,
    ObservationAnnotation,
)
from .model_info import ModelInfo
from .variable_valuations import ItemValuations

logger = logging.getLogger(__name__)


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

    state_valuations: ItemValuations = field(default_factory=ItemValuations)

    def equal(self, other: object, debug=False) -> bool:
        if not isinstance(other, ExplicitAts):
            if debug:
                logger.debug("ExplicitAts.__eq__: other is not an ExplicitAts")
            return False
        equal = True
        for field_name in self.__dataclass_fields__:
            if getattr(self, field_name) != getattr(other, field_name):
                equal = False
                if not debug:
                    break
                logger.debug(f"ExplicitAts.__eq__: field {field_name} differs")
                logger.debug(f"  self: {getattr(self, field_name)}")
                logger.debug(f"  other: {getattr(other, field_name)}")
        return equal

    def __eq__(self, other):
        return self.equal(other)

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
        return can_promote_vector_to(self.branch_probabilities)

    @property
    def exit_rate_type(self) -> CommonType | None:
        if self.state_exit_rate is None:
            return None
        return can_promote_vector_to(self.state_exit_rate)

    @property
    def reward_annotation_names(self) -> list[str]:
        """Get the names of all reward annotations."""
        return list(self.reward_annotations.keys())

    def has_reward_annotation(self, name: str) -> bool:
        """Check if a reward annotation with the given name exists."""
        return name in self.reward_annotations

    def add_reward_annotation(self, annotation: RewardAnnotation):
        """Add a reward annotation."""
        if self.has_reward_annotation(annotation.name):
            raise ValueError(f"reward annotation with name {annotation.name} already exists")
        self.reward_annotations[annotation.name] = annotation

    def get_reward_annotation(self, name: str) -> RewardAnnotation:
        """Get the reward annotation with the given name."""
        if not self.has_reward_annotation(name):
            raise ValueError(f"reward annotation with name {name} does not exist")
        return self.reward_annotations[name]

    @property
    def atomic_proposition_names(self) -> list[str]:
        """Get the names of all atomic proposition annotations."""
        return list(self.ap_annotations.keys())

    def has_ap_annotation(self, name: str) -> bool:
        """Check if an atomic proposition annotation with the given name exists."""
        return name in self.ap_annotations

    def add_ap_annotation(self, annotation: AtomicPropositionAnnotation):
        """Add an atomic proposition annotation."""
        if self.has_ap_annotation(annotation.name):
            raise ValueError(f"AP annotation with name {annotation.name} already exists")
        self.ap_annotations[annotation.name] = annotation

    def get_ap_annotation(self, name: str) -> AtomicPropositionAnnotation:
        """Get the atomic proposition annotation with the given name."""
        if not self.has_ap_annotation(name):
            raise ValueError(f"AP annotation with name {name} does not exist")
        return self.ap_annotations[name]

    @property
    def has_observations(self) -> bool:
        return self.observation_annotation is not None

    @property
    def has_state_valuations(self) -> bool:
        return self.state_valuations.num_variables > 0

    def validate(self):
        # TODO implement

        if not self.num_states > 0:
            raise ValueError("expected num_states > 0")

        if self.num_players > 1:
            if self.state_to_player is None:
                raise ValueError("num_players > 1 but state_to_player is None")
            if len(self.state_to_player) != self.num_states:
                raise ValueError("expected len(state_to_player) == num_states")

        if len(self.state_is_initial) != self.num_states:
            raise ValueError("expected len(state_is_initial) == num_states")
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
        if self.has_state_valuations:
            if not self.state_valuations.num_items == self.num_states:
                raise ValueError(
                    f"state_valuations has {self.state_valuations.num_items} items, expected {self.num_states}"
                )
            self.state_valuations.validate()
