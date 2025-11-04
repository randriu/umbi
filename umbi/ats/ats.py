"""
ATS (Abstract Transition System) implementation.

This module provides the ATS representation and I/O functions for reading/writing
ATS from/to UMB files.
"""

import time
from typing import Optional

import umbi
import umbi.io.index as index


class AtsIndex:
    """Index metadata for an ATS."""

    def __init__(self):
        self.transition_system: index.TransitionSystem
        self.model_data: Optional[index.ModelData] = None
        self.annotations: Optional[index.Annotations] = None
        self.state_valuations: Optional[index.StateValuations] = None

    @classmethod
    def from_umb_index(cls, umb_index: index.UmbIndex) -> "AtsIndex":
        ats_index = cls()
        ats_index.transition_system = umb_index.transition_system
        ats_index.model_data = umb_index.model_data
        ats_index.annotations = umb_index.annotations
        ats_index.state_valuations = umb_index.state_valuations
        return ats_index

    def to_umb_index(self) -> index.UmbIndex:
        return index.UmbIndex(
            format_version=umbi.__format_version__,
            format_revision=umbi.__format_revision__,
            transition_system=self.transition_system,
            model_data=self.model_data,
            file_data=index.FileData(
                tool=umbi.__toolname__,
                tool_version=umbi.__version__,
                creation_date=int(time.time()),
                # parameters=parameters,
            ),
            annotations=self.annotations,
            state_valuations=self.state_valuations,
        )


class Ats:
    """Abstract Transition System representation."""

    def __init__(self):
        self.index: Optional[AtsIndex] = None

        self.initial_states = None
        self.state_to_choice = None
        self.state_to_player = None

        self.markovian_states = None
        self.state_exit_rate = None

        self.choice_to_branch = None
        self.choice_to_action = None
        self.action_strings = None

        self.branch_to_target = None
        self.branch_probabilities = None

        self.rewards = None
        self.aps = None
        self.state_valuations = None
    
    @classmethod
    def from_explicit_umb(cls, umb: "ExplicitUmb") -> "Ats":
        from umbi.io.umb import ExplicitUmb
        
        ats = cls()
        ats.index = AtsIndex.from_umb_index(umb.index)

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

        ats.rewards = umb.rewards
        ats.aps = umb.aps
        ats.state_valuations = umb.state_valuations

        return ats

    @classmethod
    def to_explicit_umb(cls, ats: "Ats") -> "ExplicitUmb":
        from umbi.io.umb import ExplicitUmb
        
        umb = ExplicitUmb()
        umb.index = ats.index.to_umb_index()

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

        umb.rewards = ats.rewards
        umb.aps = ats.aps
        umb.state_valuations = ats.state_valuations

        return umb


def read_ats(umbpath: str) -> Ats:
    """Read ATS from a umbfile."""
    from umbi.io.umb import read_umb
    
    umb = read_umb(umbpath)
    ats = Ats.from_explicit_umb(umb)
    return ats


def write_ats(ats: Ats, umbpath: str):
    """Write ATS to a umbfile."""
    from umbi.io.umb import write_umb
    
    umb = Ats.to_explicit_umb(ats)
    write_umb(umb, umbpath)


__all__ = [
    "AtsIndex",
    "Ats",
    "read_ats",
    "write_ats",
]
