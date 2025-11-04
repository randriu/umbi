import time
from dataclasses import dataclass, field, fields
from typing import Optional, Literal

import umbi.io
import umbi.io.index as index
import umbi.version

#TODO import Numeric from umbi.binary?

@dataclass
class ExplicitAts:
    """Explicit container for an annotated transition system (ATS)."""

    #TODO use local ModelData class?
    model_data: Optional[index.ModelData] = None

    time: Literal["discrete", "stochastic", "urgent-stochastic"] = "discrete"
    num_states: int = 0

    num_players: int = 0
    state_to_player: Optional[list[int]] = None

    num_initial_states: int = 0
    initial_states: list[int] = field(default_factory=list)

    num_observations: Optional[int] = None
    #TODO other POMDP stuff

    num_choices: int = 0
    state_to_choice: Optional[list[int]] = None

    markovian_states: Optional[list[int]] = None
    exit_rate_type: Optional[Literal["double", "rational", "double-interval", "rational-interval"]] = None
    state_exit_rate: Optional[list] = None #TODO use Numeric

    num_actions: int = 0
    choice_to_action: Optional[list[int]] = None
    action_strings: Optional[list[str]] = None

    num_branches: int = 0
    choice_to_branch: Optional[list[int]] = None
    branch_to_target: Optional[list[int]] = None
    branch_probability_type: Optional[Literal["double", "rational", "double-interval", "rational-interval"]] = None
    branch_probabilities: Optional[list] = None #TODO use Numeric

    #TODO consolidate each into one structure
    rewards: Optional[dict[str, index.Annotation]] = None
    rewards_values: Optional[dict[str, dict[str, list]]] = None

    aps: Optional[dict[str, index.Annotation]] = None
    aps_values: Optional[dict[str, dict[str, list]]] = None

    state_valuations: Optional[index.StateValuations] = None
    state_valuations_values: Optional[list[dict]] = None

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

    def validate(self):
        # TODO implement
        assert self.num_states > 0
        assert self.num_initial_states == sum(self.initial_states)
        assert self.state_to_choice is None or len(self.state_to_choice) == self.num_states+1
        assert self.choice_to_branch is None or len(self.choice_to_branch) == self.num_choices+1
        assert self.branch_to_target is None or len(self.branch_to_target) == self.num_branches
        if self.num_players > 0:
            assert self.state_to_player is not None and len(self.state_to_player) == self.num_states


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
