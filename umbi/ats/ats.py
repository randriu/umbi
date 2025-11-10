import time
from dataclasses import dataclass, field, fields
from typing import Optional, Literal

import umbi.io
import umbi.io.index as index
import umbi.version
import umbi.datatypes
from umbi.datatypes import CommonType, Numeric, Interval

@dataclass
class ExplicitAts:
    """Explicit container for an annotated transition system (ATS)."""

    #TODO use local ModelData class?
    model_data: index.ModelData | None = None

    time: Literal["discrete", "stochastic", "urgent-stochastic"] = "discrete" #TODO enum
    num_states: int = 0

    num_players: int = 0
    state_to_player: list[int] | None = None

    num_initial_states: int = 0
    initial_states: list[int] = field(default_factory=list)

    num_observations: int | None = None
    #TODO other POMDP stuff

    num_choices: int = 0
    state_to_choice: list[int] | None = None

    markovian_states: list[int] | None = None
    exit_rate_type: CommonType | None = None
    state_exit_rate: list[Numeric | Interval] | None = None

    num_actions: int = 1
    choice_to_action: list[int] | None = None
    action_strings: list[str] | None = None

    num_branches: int = 0
    choice_to_branch: list[int] | None = None
    branch_to_target: list[int] | None = None
    branch_probability_type: CommonType | None = None
    branch_probabilities: list[Numeric | Interval] | None = None

    #TODO consolidate each into one structure
    rewards: dict[str, index.Annotation] | None = None
    rewards_values: dict[str, dict[str, list]] | None = None

    aps: dict[str, index.Annotation] | None = None
    aps_values: dict[str, dict[str, list]] | None = None

    state_valuations: umbi.datatypes.StructType | None = None
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

    def validate(self):
        # TODO implement

        NUMERIC_DATATYPES = [
            CommonType.DOUBLE, CommonType.RATIONAL,
            CommonType.DOUBLE_INTERVAL, CommonType.RATIONAL_INTERVAL
        ]

        if self.time not in ["discrete", "stochastic", "urgent-stochastic"]:
            raise ValueError(f"invalid time type {self.time}")

        if not self.num_states > 0:
            raise ValueError("expected num_states > 0")

        if self.num_players > 1:
            if self.state_to_player is None:
                raise ValueError("num_players > 1 but state_to_player is None")
            if len(self.state_to_player) != self.num_states:
                raise ValueError("expected len(state_to_player) == num_states")

        if self.num_initial_states != sum(self.initial_states):
            raise ValueError("expected num_initial_states == sum(initial_states)")

        if self.exit_rate_type is not None:
            if self.exit_rate_type not in NUMERIC_DATATYPES:
                raise ValueError(f"invalid exit rate type {self.exit_rate_type}")
        if self.branch_probability_type is not None:
            if self.branch_probability_type not in NUMERIC_DATATYPES:
                raise ValueError(f"invalid branch probability type {self.branch_probability_type}")
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


class ExplicitAtsConverter:
    """Converter between ExplicitAts and ExplicitUmb."""

    @staticmethod
    def from_explicit_umb(umb: umbi.io.ExplicitUmb) -> ExplicitAts:
        umb.validate()
        ats = ExplicitAts()

        ## index
        # skip format_version
        # skip format_revision
        ats.model_data = umb.index.model_data
        # skip file_data
        # load index.transition_system fields into ats
        for f in fields(index.TransitionSystem):
            setattr(ats, f.name, getattr(umb.index.transition_system, f.name))

        # load annotations
        if umb.index.annotations is not None:
            ats.rewards = umb.index.annotations.rewards
            ats.aps = umb.index.annotations.aps
            ats.state_valuations = umb.index.state_valuations

        ## values 
        ats.initial_states = umb.initial_states
        ats.state_to_choice = umb.state_to_choice
        ats.state_to_player = umb.state_to_player

        ats.markovian_states = umb.markovian_states
        ats.state_exit_rate = umb.state_exit_rate

        ats.choice_to_branch = umb.choice_to_branch
        ats.choice_to_action = umb.choice_to_action
        ats.action_strings = umb.action_strings

        ats.branch_to_target = umb.branch_to_target
        ats.branch_probabilities = umb.branch_probabilities

        ats.rewards_values = umb.rewards
        ats.aps_values = umb.aps
        ats.state_valuations_values = umb.state_valuations

        ats.validate()
        return ats

    @staticmethod
    def to_explicit_umb(ats: ExplicitAts) -> umbi.io.ExplicitUmb:
        ats.validate()
        umb = umbi.io.ExplicitUmb()

        ## index
        # insert our format_version, format_revision
        umb.index = umbi.io.index.UmbIndex(
            format_version=umbi.version.__format_version__,
            format_revision=umbi.version.__format_revision__,
            # create transition_system from matching fields
            transition_system=index.TransitionSystem(
                **{f.name: getattr(ats, f.name) for f in fields(index.TransitionSystem)}
            ),
            model_data=ats.model_data,
            # insert our file_data
            file_data=index.FileData(
                tool=umbi.version.__toolname__,
                tool_version=umbi.version.__version__,
                creation_date=int(time.time()),
                # parameters=parameters,
            ),
            # create annotations
            annotations=index.Annotations(
                rewards=ats.rewards,
                aps=ats.aps,
            ),
            state_valuations=ats.state_valuations,
        )
        ## values
        umb.initial_states = ats.initial_states
        umb.state_to_choice = ats.state_to_choice
        umb.state_to_player = ats.state_to_player

        umb.markovian_states = ats.markovian_states
        umb.state_exit_rate = ats.state_exit_rate

        umb.choice_to_branch = ats.choice_to_branch
        umb.choice_to_action = ats.choice_to_action
        umb.action_strings = ats.action_strings

        umb.branch_to_target = ats.branch_to_target
        umb.branch_probabilities = ats.branch_probabilities

        umb.rewards = ats.rewards_values
        umb.aps = ats.aps_values
        umb.state_valuations = ats.state_valuations_values

        umb.validate()
        return umb


def read_ats(umbpath: str) -> ExplicitAts:
    """Read ATS from a umbfile."""
    umb = umbi.io.read_umb(umbpath)
    ats = ExplicitAtsConverter.from_explicit_umb(umb)
    return ats


def write_ats(ats: ExplicitAts, umbpath: str):
    """Write ATS to a umbfile."""
    umb = ExplicitAtsConverter.to_explicit_umb(ats)
    umbi.io.write_umb(umb, umbpath)
