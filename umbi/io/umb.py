"""
Utilities for reading and writing umbfiles.
"""

import logging
from dataclasses import dataclass, field
from typing import no_type_check

logger = logging.getLogger(__name__)

from enum import Enum

import umbi.binary
import umbi.datatypes
from umbi.datatypes import (
    VECTOR_TYPE_BITVECTOR,
    VECTOR_TYPE_CSR,
    CommonType,
    Numeric,
    StructType,
    VectorType,
)

from .index import Annotation, UmbIndex
from .tar import TarReader, TarWriter


class UmbFile(Enum):
    """A list of common files expected in a umbfile. Each entry is a tuple of (filename, filetype)."""

    INDEX_JSON = ("index.json", CommonType.JSON)

    STATE_IS_INITIAL = ("initial-states.bin", VECTOR_TYPE_BITVECTOR)
    STATE_TO_CHOICE = ("state-to-choice.bin", VECTOR_TYPE_CSR)
    STATE_TO_PLAYER = ("state-to-player.bin", VectorType(CommonType.UINT32))

    STATE_IS_MARKOVIAN = ("markovian-states.bin", VECTOR_TYPE_BITVECTOR)
    STATE_TO_EXIT_RATE = ("exit-rates.bin", CommonType.BYTES)
    STATE_TO_EXIT_RATE_CSR = ("state-to-exit-rate.bin", VECTOR_TYPE_CSR)

    CHOICE_TO_BRANCH = ("choice-to-branch.bin", VECTOR_TYPE_CSR)
    BRANCH_TO_TARGET = ("branch-to-target.bin", VectorType(CommonType.UINT64))
    BRANCH_TO_PROBABILITY = ("branch-probabilities.bin", CommonType.BYTES)
    BRANCH_TO_PROBABILITY_CSR = ("branch-to-probability.bin", VECTOR_TYPE_CSR)

    CHOICE_TO_ACTION = ("choice-to-choice-action.bin", VectorType(CommonType.UINT32))
    ACTION_TO_STRING = ("choice-action-strings.bin", VectorType(CommonType.STRING))
    ACTION_TO_STRING_CSR = ("choice-action-to-string.bin", VECTOR_TYPE_CSR)

    BRANCH_TO_BRANCH_ACTION = ("branch-to-branch-action.bin", VectorType(CommonType.UINT32))
    BRANCH_ACTION_TO_STRING = ("branch-action-strings.bin", VectorType(CommonType.STRING))
    BRANCH_ACTION_TO_STRING_CSR = ("branch-action-to-string.bin", VECTOR_TYPE_CSR)

    STATE_TO_VALUATION = ("state-valuations.bin", CommonType.BYTES)
    STATE_TO_VALUATION_CSR = ("state-to-valuation.bin", VECTOR_TYPE_CSR)

    # WIP
    STATE_TO_OBSERVATION = ("state-to-observation.bin", VectorType(CommonType.UINT64))
    CHOICE_TO_OBSERVATION = ("choice-to-observation.bin", VectorType(CommonType.UINT64))
    BRANCH_TO_OBSERVATION = ("branch-to-observation.bin", VectorType(CommonType.UINT64))


@dataclass
class ExplicitUmb:
    """Class for an explicit representation of a umbfile. The goal of this class is to have all the data is stored in python lists, rather than binary formats."""

    index: UmbIndex = field(default_factory=UmbIndex)

    state_is_initial: list[bool] = field(default_factory=list)
    state_to_choice: list[int] | None = None
    state_to_player: list[int] | None = None

    state_is_markovian: list[bool] | None = None
    state_to_exit_rate: list[Numeric] | None = None

    choice_to_branch: list[int] | None = None
    branch_to_target: list[int] | None = None
    branch_to_probability: list[Numeric] | None = None

    choice_to_action: list[int] | None = None
    action_to_string: list[str] | None = None

    branch_to_branch_action: list[int] | None = None
    branch_action_to_string: list[str] | None = None

    rewards: dict[str, dict[str, list]] | None = None
    aps: dict[str, dict[str, list]] | None = None
    item_to_observation: list[int] | None = None

    state_to_valuation: list[dict] | None = None

    def validate(self):
        self.index.validate()


class UmbReader(TarReader):
    def __init__(self, tarpath: str):
        super().__init__(tarpath)
        # to keep track of which files were read
        self.filename_read = {filename: False for filename in self.filenames}

    def list_unread_files(self):
        """Print warning about unread files from the tarfile, if such exist."""
        unread_files = [f for f, read in self.filename_read.items() if not read]
        for f in unread_files:
            logger.warning(f"umbfile contains unrecognized file: {f}")

    def read_file(self, filename: str, required: bool = False) -> bytes | None:
        """Read raw bytes from a specific file in the tarball. Mark the file as read."""
        if filename in self.filenames:
            self.filename_read[filename] = True
        return super().read_file(filename, required)

    def read_common(self, file: UmbFile, required: bool = False):
        filename, filetype = file.value
        return self.read_filetype(filename, filetype, required)

    def truncate_bitvector(self, vector: list[bool], num_entries: int) -> list[bool]:
        if not len(vector) >= num_entries:
            logger.error(f"bitvector length {len(vector)} is shorter than expected {num_entries}")
        return vector[:num_entries]

    def read_common_bitvector(self, file: UmbFile, num_entries: int, required: bool = False) -> list[bool] | None:
        vector = self.read_common(file, required)
        if vector is None:
            return None
        assert isinstance(vector, list)
        return self.truncate_bitvector(vector, num_entries)

    def read_common_csr(
        self,
        file: UmbFile,
        required: bool,
        file_csr: UmbFile,
        required_csr: bool = False,
        value_type: CommonType | None = None,
    ):
        if value_type is None:
            _, filetype = file.value
            assert isinstance(filetype, VectorType), "expected VectorType"
            value_type = filetype.base_type
        filename, _ = file.value
        filename_csr, _ = file_csr.value
        return self.read_filetype_with_csr(filename, value_type, required, filename_csr, required_csr)

    def read_json(self, file: UmbFile) -> UmbIndex:
        json_obj = self.read_common(file, required=True)
        pretty_str = umbi.datatypes.json_to_string(json_obj)
        logger.debug(f"loaded the following json:\n{pretty_str}")
        assert umbi.datatypes.is_json_instance(json_obj), "expected json object"
        idx = UmbIndex.from_json(json_obj)
        idx.validate()
        return idx

    def read_annotation(self, label: str, name: str, annotation: Annotation, index: UmbIndex) -> dict[str, list]:
        """
        Read annotation files for a single annotation.
        :param label: annotation label, usually one of ["rewards","aps"]
        :param name: annotation name
        :param annotation: annotation info (Annotation)
        :return: dict mapping applies_to -> values
        """
        applies_values = dict()
        applies_to = annotation.applies_to if annotation.applies_to is not None else ["states"]
        for applies in applies_to:
            path = f"annotations/{label}/{name}/for-{applies}"
            annotation_type = CommonType(annotation.type) if annotation.type is not None else CommonType.BOOLEAN
            vector = self.read_filetype_with_csr(
                f"{path}/values.bin", annotation_type, required=True, filename_csr=f"{path}/to-values.bin"
            )
            assert isinstance(vector, list)
            if annotation_type == CommonType.BOOLEAN:
                num_entries = {
                    "states": index.transition_system.num_states,
                    "choices": index.transition_system.num_choices,
                    "branches": index.transition_system.num_branches,
                }[applies]
                vector = self.truncate_bitvector(vector, num_entries=num_entries)
            applies_values[applies] = vector
        return applies_values

    def read_annotations(
        self, label: str, annotation_info: dict[str, Annotation] | None, index: UmbIndex
    ) -> dict[str, dict[str, list]] | None:
        """
        Read annotation files for all annotations in annotation_info.
        :param label: annotation label, usually one of ["rewards","aps"]
        :param annotation_info: a dictionary annotation name -> annotation
        :return: dict mapping annotation name -> applies_to -> values
        """
        if annotation_info is None:
            return None
        name_applies_values = dict()
        for name, annotation in annotation_info.items():
            name_applies_values[name] = self.read_annotation(label, name, annotation, index)
        return name_applies_values

    def read_observations(self, num_observations: int, observations_apply_to: str | None) -> list[int] | None:
        if num_observations == 0:
            return None
        if observations_apply_to is None:
            raise ValueError("observations_applies_to is required when #num_observations > 0")
        file = {
            "states": UmbFile.STATE_TO_OBSERVATION,
            "choices": UmbFile.CHOICE_TO_OBSERVATION,
            "branches": UmbFile.BRANCH_TO_OBSERVATION,
        }[observations_apply_to]
        return self.read_common(file, required=True)

    def read_variable_valuations(
        self, variable_valuations: StructType, num_entries: int, file: UmbFile, file_csr: UmbFile
    ) -> list[dict]:
        chunks_csr = self.read_common(file_csr, required=False)
        if chunks_csr is None:
            chunks_csr = list(range(num_entries + 1))
        chunks_csr = [x * variable_valuations.alignment for x in chunks_csr]
        valuations = self.read_common(file, required=True)
        assert isinstance(valuations, bytes)
        # assert len(valuations) == (chunks_csr[-1]), "state valuations data length does not match expected size"
        ranges = umbi.datatypes.csr_to_ranges(chunks_csr)
        return umbi.binary.bytes_to_vector(valuations, variable_valuations, ranges)

    @no_type_check
    def read_umb(self):  # type: ignore
        logger.info(f"loading umbfile from {self.tarpath} ...")
        umb = ExplicitUmb()

        umb.index = self.read_json(UmbFile.INDEX_JSON)
        ts = umb.index.transition_system

        umb.state_is_initial = self.read_common_bitvector(UmbFile.STATE_IS_INITIAL, ts.num_states, required=True)
        umb.state_to_choice = self.read_common(UmbFile.STATE_TO_CHOICE)
        umb.state_to_player = self.read_common(UmbFile.STATE_TO_PLAYER)

        umb.state_is_markovian = self.read_common_bitvector(UmbFile.STATE_IS_MARKOVIAN, ts.num_states, required=False)
        if umb.index.transition_system.exit_rate_type is not None:
            umb.state_to_exit_rate = self.read_common_csr(
                UmbFile.STATE_TO_EXIT_RATE,
                required=False,
                file_csr=UmbFile.STATE_TO_EXIT_RATE_CSR,
                required_csr=False,
                value_type=CommonType(umb.index.transition_system.exit_rate_type),
            )

        umb.choice_to_branch = self.read_common(UmbFile.CHOICE_TO_BRANCH)
        umb.branch_to_target = self.read_common(UmbFile.BRANCH_TO_TARGET)
        if umb.index.transition_system.branch_probability_type is not None:
            umb.branch_to_probability = self.read_common_csr(
                UmbFile.BRANCH_TO_PROBABILITY,
                required=False,
                file_csr=UmbFile.BRANCH_TO_PROBABILITY_CSR,
                required_csr=False,
                value_type=CommonType(umb.index.transition_system.branch_probability_type),
            )

        umb.choice_to_action = self.read_common(UmbFile.CHOICE_TO_ACTION)
        umb.action_to_string = self.read_common_csr(
            UmbFile.ACTION_TO_STRING,
            required=False,
            file_csr=UmbFile.ACTION_TO_STRING_CSR,
            required_csr=True,
        )

        umb.branch_to_branch_action = self.read_common(UmbFile.BRANCH_TO_BRANCH_ACTION)
        umb.branch_action_to_string = self.read_common_csr(
            UmbFile.BRANCH_ACTION_TO_STRING,
            required=False,
            file_csr=UmbFile.BRANCH_ACTION_TO_STRING_CSR,
            required_csr=True,
        )

        if umb.index.annotations is not None:
            umb.rewards = self.read_annotations("rewards", umb.index.annotations.rewards, umb.index)
            umb.aps = self.read_annotations("aps", umb.index.annotations.aps, umb.index)
        if umb.index.state_valuations is not None:
            umb.state_to_valuation = self.read_variable_valuations(
                umb.index.state_valuations,
                num_entries=umb.index.transition_system.num_states,
                file=UmbFile.STATE_TO_VALUATION,
                file_csr=UmbFile.STATE_TO_VALUATION_CSR,
            )
        umb.item_to_observation = self.read_observations(ts.num_observations, ts.observations_apply_to)

        self.list_unread_files()
        logger.info(f"finished loading the umbfile")
        return umb


class UmbWriter(TarWriter):

    def add_common(self, file: UmbFile, data, required: bool = False):
        filename, filetype = file.value
        self.add_filetype(filename, filetype, data, required=required)

    def add_common_csr(
        self, file: UmbFile, data, file_csr: UmbFile, required: bool = False, value_type: CommonType | None = None
    ):
        if value_type is None:
            _, filetype = file.value
            assert isinstance(filetype, VectorType), "expected VectorType"
            value_type = filetype.base_type
        filename, _ = file.value
        filename_csr, _ = file_csr.value
        self.add_filetype_with_csr(filename, value_type, data, required, filename_csr)

    def add_index(self, file: UmbFile, index: UmbIndex):
        index.validate()
        json_obj = index.to_json()
        self.add_common(file, json_obj, required=True)

    def add_annotation(self, label: str, name: str, annotation_info: Annotation, applies_values: dict[str, list]):
        """
        Add files for an annotation.
        :param label: annotation label, usually one of ["rewards","aps"]
        :param annotation_info: a dictionary annotation name -> annotation
        """
        for applies, values in applies_values.items():
            prefix = f"annotations/{label}/{name}/for-{applies}"
            annotation_type = (
                CommonType(annotation_info.type) if annotation_info.type is not None else CommonType.BOOLEAN
            )
            self.add_filetype_with_csr(
                f"{prefix}/values.bin",
                annotation_type,
                values,
                required=True,
                filename_csr=f"{prefix}/to-values.bin",
            )

    def add_annotations(
        self,
        label: str,
        annotation_info: dict[str, Annotation] | None,
        annotation_values: dict[str, dict[str, list]] | None = None,
    ):
        if annotation_info is None:
            return
        assert annotation_values is not None
        for name, annotation in annotation_info.items():
            assert name in annotation_values, f"missing values for annotation {name}"
            self.add_annotation(label, name, annotation, annotation_values[name])

    def add_observations(self, apply_to: str | None, item_to_observation: list[int] | None):
        if apply_to is None:
            return
        if item_to_observation is None:
            raise ValueError("item_to_observation is required when apply_to is specified")
        file = {
            "states": UmbFile.STATE_TO_OBSERVATION,
            "choices": UmbFile.CHOICE_TO_OBSERVATION,
            "branches": UmbFile.BRANCH_TO_OBSERVATION,
        }[apply_to]
        self.add_common(file, item_to_observation, required=True)

    def add_variable_valuations(
        self, valuation_type: StructType, variable_valuations: list[dict], file: UmbFile, file_csr: UmbFile
    ):
        bytestring, chunk_ranges = umbi.binary.vector_to_bytes(variable_valuations, valuation_type)
        assert chunk_ranges is not None
        self.add_common(file, bytestring)
        chunk_ranges = [x // valuation_type.alignment for x in chunk_ranges]
        self.add_common(file_csr, chunk_ranges)

    def write_umb(self, umb: ExplicitUmb, umbpath: str):
        logger.info(f"writing umbfile to {umbpath} ...")
        self.add_index(UmbFile.INDEX_JSON, umb.index)

        self.add_common(UmbFile.STATE_IS_INITIAL, umb.state_is_initial, required=True)
        self.add_common(UmbFile.STATE_TO_CHOICE, umb.state_to_choice)
        self.add_common(UmbFile.STATE_TO_PLAYER, umb.state_to_player)

        self.add_common(UmbFile.STATE_IS_MARKOVIAN, umb.state_is_markovian)
        if umb.index.transition_system.exit_rate_type is not None:
            self.add_common_csr(
                UmbFile.STATE_TO_EXIT_RATE,
                umb.state_to_exit_rate,
                file_csr=UmbFile.STATE_TO_EXIT_RATE_CSR,
                value_type=CommonType(umb.index.transition_system.exit_rate_type),
            )

        self.add_common(UmbFile.CHOICE_TO_BRANCH, umb.choice_to_branch)
        self.add_common(UmbFile.BRANCH_TO_TARGET, umb.branch_to_target)
        if umb.index.transition_system.branch_probability_type is not None:
            self.add_common_csr(
                UmbFile.BRANCH_TO_PROBABILITY,
                umb.branch_to_probability,
                file_csr=UmbFile.BRANCH_TO_PROBABILITY_CSR,
                value_type=CommonType(umb.index.transition_system.branch_probability_type),
            )

        self.add_common(UmbFile.CHOICE_TO_ACTION, umb.choice_to_action)
        self.add_common_csr(UmbFile.ACTION_TO_STRING, umb.action_to_string, UmbFile.ACTION_TO_STRING_CSR)
        self.add_common(UmbFile.BRANCH_TO_BRANCH_ACTION, umb.branch_to_branch_action)
        self.add_common_csr(
            UmbFile.BRANCH_ACTION_TO_STRING, umb.branch_action_to_string, UmbFile.BRANCH_ACTION_TO_STRING_CSR
        )

        if umb.index.annotations is not None:
            self.add_annotations("rewards", umb.index.annotations.rewards, umb.rewards)
            self.add_annotations("aps", umb.index.annotations.aps, umb.aps)
        if umb.index.state_valuations is not None:
            assert umb.state_to_valuation is not None
            self.add_variable_valuations(
                umb.index.state_valuations,
                umb.state_to_valuation,
                file=UmbFile.STATE_TO_VALUATION,
                file_csr=UmbFile.STATE_TO_VALUATION_CSR,
            )
        self.add_observations(umb.index.transition_system.observations_apply_to, umb.item_to_observation)
        self.write(umbpath)
        logger.info(f"finished writing the umbfile")


def read_umb(umbpath: str) -> ExplicitUmb:
    """Read UMB from a umbfile."""
    return UmbReader(umbpath).read_umb()


def write_umb(umb: ExplicitUmb, umbpath: str):
    """Write UMB to a umbfile."""
    UmbWriter().write_umb(umb, umbpath)
