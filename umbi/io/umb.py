"""
Utilities for reading and writing umbfiles.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

from enum import Enum
from types import SimpleNamespace

import umbi
import umbi.binary

from .index import UmbIndex
from .tar import TarReader, TarWriter


class UmbFile(Enum):
    """A list of common files expected in a umbfile. Each entry is a tuple of (filename, filetype)."""

    INDEX_JSON = ("index.json", "json")

    INITIAL_STATES = ("initial-states.bin", "vector[bool]")
    STATE_TO_CHOICE = ("state-to-choice.bin", "csr")
    STATE_TO_PLAYER = ("state-to-player.bin", "vector[uint32]")

    MARKOVIAN_STATES = ("markovian-states.bin", "vector[bool]")
    STATE_TO_EXIT_RATE = ("state-to-exit-rate.bin", "csr")
    EXIT_RATES = ("exit-rates.bin", "bytes")

    CHOICE_TO_BRANCH = ("choice-to-branch.bin", "csr")
    CHOICE_TO_ACTION = ("choice-to-action.bin", "vector[uint32]")
    ACTION_TO_ACTION_STRING = ("action-to-action-string.bin", "csr")
    ACTION_STRINGS = ("action-strings.bin", "bytes")

    BRANCH_TO_TARGET = ("branch-to-target.bin", "vector[uint64]")
    BRANCH_TO_PROBABILITY = ("branch-to-probability.bin", "csr")
    BRANCH_PROBABILITIES = ("branch-probabilities.bin", "bytes")

    STATE_TO_VALUATION = ("state-to-valuation.bin", "csr")
    STATE_VALUATIONS = ("state-valuations.bin", "bytes")


class ExplicitUmb:
    """Class for an explicit representation of a umbfile. The goal of this class is to have all the data is stored in numpy arrays and lists."""

    def __init__(self):
        self.index: UmbIndex = UmbIndex()

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

    def validate(self):
        # TODO implement
        # logger.debug("UMB validation requested but is not implemented yet")
        return



class UmbReader(TarReader):
    def __init__(self, tarpath: str):
        super().__init__(tarpath)
        # to keep track of which files were read
        self.filename_read = {filename: False for filename in self.filenames}

    def warn_about_unread_files(self):
        """Print warning about unread files from the tarfile, if such exist."""
        unread_files = [f for f, read in self.filename_read.items() if not read]
        for f in unread_files:
            logger.warning(f"umbfile contains unrecognized file: {f}")

    def read_file(self, filename: str, required: bool = False) -> bytes | None:
        """Read raw bytes from a specific file in the tarball. Mark the file as read."""
        logger.debug(f"attempting to read {filename} ...")
        if filename in self.filenames:
            self.filename_read[filename] = True
        return super().read_file(filename, required)

    def read_common(self, file: UmbFile, required: bool = False):
        filename, filetype = file.value
        return self.read_filetype(filename, filetype, required)

    def read_common_csr(self, file: UmbFile, value_type: str, required: bool, file_csr: UmbFile, required_csr: bool = False):
        filename, _ = file.value
        filename_csr, _ = file_csr.value
        return self.read_filetype_csr(filename, value_type, required, filename_csr, required_csr)

    # TODO make annotation into a dedicated class
    def read_annotation(self, label: str, annotation_dict: dict[str, SimpleNamespace] | None):
        """
        Read annotation files. The values from the files will be stored in the corresponding annotation object as a new dictionary mapping applies-to -> values
        :param label: annotation label, usually one of ["rewards","aps"]
        :param annotation_dict: a dictionary annotation name -> annotation
        """
        if annotation_dict is None:
            return
        for name, annotation in annotation_dict.items():
            annotation.values = dict[str, list]()
            for applies in annotation.applies_to:
                path = f"annotations/{label}/{name}/for-{applies}"
                vector = self.read_filetype_csr(
                    f"{path}/values.bin", annotation.type, required=True, filename_csr=f"{path}/to-value.bin"
                )
                assert vector is not None
                annotation.values[applies] = vector

    def read_state_valuations(self, state_valuations: SimpleNamespace | None, num_states: int):
        if state_valuations is None:
            return None
        ranges = self.read_common(UmbFile.STATE_TO_VALUATION, required=False)
        if ranges is None:
            ranges = [(s,s+1) for s in range(num_states)]
        assert isinstance(ranges, (list, type(tuple([int,int]))))
        a = state_valuations.alignment
        ranges = [(x*a,y*a) for (x,y) in ranges]
        valuations = self.read_common(UmbFile.STATE_VALUATIONS, required=True)
        assert isinstance(valuations, bytes)
        value_type = umbi.binary.CompositeType.from_namespace(state_valuations.variables)
        return umbi.binary.bytes_to_vector(valuations, value_type, ranges)

    def read_umb(self):  # type: ignore
        logger.info(f"loading umbfile from {self.tarpath} ...")
        umb = ExplicitUmb()

        json_obj = self.read_common(UmbFile.INDEX_JSON, required=True)
        umb.index = UmbIndex.from_json(json_obj)

        umb.initial_states = self.read_common(UmbFile.INITIAL_STATES, required=True)
        umb.state_to_choice = self.read_common(UmbFile.STATE_TO_CHOICE)
        umb.state_to_player = self.read_common(UmbFile.STATE_TO_PLAYER)

        umb.markovian_states = self.read_common(UmbFile.MARKOVIAN_STATES)
        if umb.index.transition_system.exit_rate_type is not None:
            umb.state_exit_rate = self.read_common_csr(
                UmbFile.EXIT_RATES, umb.index.transition_system.exit_rate_type, False, UmbFile.STATE_TO_EXIT_RATE, False
            )

        umb.choice_to_branch = self.read_common(UmbFile.CHOICE_TO_BRANCH)
        umb.choice_to_action = self.read_common(UmbFile.CHOICE_TO_ACTION)
        umb.action_strings = self.read_common_csr(UmbFile.ACTION_STRINGS, "string", False, UmbFile.ACTION_TO_ACTION_STRING, True)

        umb.branch_to_target = self.read_common(UmbFile.BRANCH_TO_TARGET)
        if umb.index.transition_system.branch_probability_type is not None:
            umb.branch_probabilities = self.read_common_csr(
                UmbFile.BRANCH_PROBABILITIES, umb.index.transition_system.branch_probability_type, False,
                UmbFile.BRANCH_TO_PROBABILITY, False
            )

        self.read_annotation("rewards", umb.index.annotations.rewards) # TODO store to umb.rewards
        self.read_annotation("aps", umb.index.annotations.aps) # TODO store to umb.aps
        umb.state_valuations = self.read_state_valuations(umb.index.annotations.state_valuations, umb.index.transition_system.num_states)

        self.warn_about_unread_files()
        umb.validate()
        logger.info(f"finished loading the umbfile")
        return umb


class UmbWriter(TarWriter):

    def add_common(self, file: UmbFile, data, required: bool = False):
        filename, filetype = file.value
        self.add_filetype(filename, filetype, data, required=required)

    def add_common_csr(self, file: UmbFile, data, value_type: str, file_csr: UmbFile, required: bool = False):
        filename, _ = file.value
        filename_csr, _ = file_csr.value
        self.add_filetype_csr(filename, value_type, data, required, filename_csr)

    def add_annotation(self, label: str, annotation_dict: dict[str, SimpleNamespace] | None):
        """
        Read annotation files.
        :param label: annotation label, usually one of ["rewards","aps"]
        :param annotation_dict: a dictionary annotation name -> annotation
        """
        if annotation_dict is None:
            return
        for name, annotation in annotation_dict.items():
            for applies, values in annotation.values.items():
                prefix = f"annotations/{label}/{name}/for-{applies}"
                self.add_filetype_csr(
                    f"{prefix}/values.bin", annotation.type, values, required=True, filename_csr=f"{prefix}/to-values.bin"
                )

    def add_state_valuations(self, state_valuations_index: SimpleNamespace | None, state_valuations: list[dict] | None):
        if state_valuations_index is None:
            return
        assert state_valuations is not None
        value_type = umbi.binary.CompositeType.from_namespace(state_valuations_index.variables)
        bytestring,ranges = umbi.binary.vector_to_bytes(state_valuations, value_type)
        self.add_common(UmbFile.STATE_VALUATIONS, bytestring)
        assert ranges is not None
        state_valuations_index.alignment = 1 # TODO compute nontrivial alignment
        self.add_common(UmbFile.STATE_TO_VALUATION, ranges)

    def write_umb(self, umb: ExplicitUmb, umbpath: str):
        umb.validate()
        logger.info(f"writing umbfile to {umbpath} ...")
        self.add_common(UmbFile.INDEX_JSON, umb.index.to_json(), required=True)
        self.add_common(UmbFile.INITIAL_STATES, umb.initial_states, required=True)
        self.add_common(UmbFile.STATE_TO_CHOICE, umb.state_to_choice)
        self.add_common(UmbFile.STATE_TO_PLAYER, umb.state_to_player)
        self.add_common(UmbFile.MARKOVIAN_STATES, umb.markovian_states)
        self.add_common_csr(
            UmbFile.EXIT_RATES,
            umb.state_exit_rate,
            umb.index.transition_system.exit_rate_type,
            UmbFile.STATE_TO_EXIT_RATE,
        )
        self.add_common(UmbFile.CHOICE_TO_BRANCH, umb.choice_to_branch)
        self.add_common(UmbFile.CHOICE_TO_ACTION, umb.choice_to_action)
        self.add_common_csr(UmbFile.ACTION_STRINGS, umb.action_strings, "string", UmbFile.ACTION_TO_ACTION_STRING)
        self.add_common(UmbFile.BRANCH_TO_TARGET, umb.branch_to_target)
        self.add_common_csr(
            UmbFile.BRANCH_PROBABILITIES,
            umb.branch_probabilities,
            umb.index.transition_system.branch_probability_type,
            UmbFile.BRANCH_TO_PROBABILITY,
        )
        self.add_annotation("rewards", umb.index.annotations.rewards)
        self.add_annotation("aps", umb.index.annotations.aps)
        self.add_state_valuations(umb.index.annotations.state_valuations, umb.state_valuations)
        self.write(umbpath)
        logger.info(f"finished writing the umbfile")


def read_umb(umbpath: str) -> ExplicitUmb:
    """Read UMB from a umbfile."""
    return UmbReader(umbpath).read_umb()


def write_umb(umb: ExplicitUmb, umbpath: str):
    """Write UMB to a umbfile."""
    UmbWriter().write_umb(umb, umbpath)
