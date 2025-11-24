"""
Utilities for reading and writing umbfiles.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

from enum import Enum

import umbi.binary
import umbi.datatypes
from umbi.datatypes import CSR_TYPE, CommonType, Numeric, StructType, VectorType

from .index import Annotation, UmbIndex
from .tar import TarReader, TarWriter


class UmbFile(Enum):
    """A list of common files expected in a umbfile. Each entry is a tuple of (filename, filetype)."""

    INDEX_JSON = ("index.json", CommonType.JSON)

    INITIAL_STATES = ("initial-states.bin", VectorType(CommonType.BOOLEAN))
    STATE_TO_CHOICE = ("state-to-choice.bin", CSR_TYPE)
    STATE_TO_PLAYER = ("state-to-player.bin", VectorType(CommonType.UINT32))

    MARKOVIAN_STATES = ("markovian-states.bin", VectorType(CommonType.BOOLEAN))
    STATE_TO_EXIT_RATE = ("state-to-exit-rate.bin", CSR_TYPE)
    EXIT_RATES = ("exit-rates.bin", CommonType.BYTES)

    CHOICE_TO_BRANCH = ("choice-to-branch.bin", CSR_TYPE)
    CHOICE_TO_ACTION = ("choice-to-action.bin", VectorType(CommonType.UINT32))
    ACTION_TO_ACTION_STRING = ("action-to-action-string.bin", CSR_TYPE)
    ACTION_STRINGS = ("action-strings.bin", CommonType.BYTES)

    BRANCH_TO_TARGET = ("branch-to-target.bin", VectorType(CommonType.UINT64))
    BRANCH_TO_PROBABILITY = ("branch-to-probability.bin", CSR_TYPE)
    BRANCH_PROBABILITIES = ("branch-probabilities.bin", CommonType.BYTES)

    STATE_TO_VALUATION = ("state-to-valuation.bin", CSR_TYPE)
    STATE_VALUATIONS = ("state-valuations.bin", CommonType.BYTES)


@dataclass
class ExplicitUmb:
    """Class for an explicit representation of a umbfile. The goal of this class is to have all the data is stored in numpy arrays and lists."""

    index: UmbIndex = field(default_factory=UmbIndex)

    state_is_initial: list[bool] = field(default_factory=list)
    state_to_choice: list[int] | None = None
    state_to_player: list[int] | None = None

    state_is_markovian: list[bool] | None = None
    state_exit_rate: list[Numeric] | None = None

    choice_to_branch: list[int] | None = None
    choice_to_action: list[int] | None = None
    action_strings: list[str] | None = None

    branch_to_target: list[int] | None = None
    branch_probabilities: list[Numeric] | None = None

    rewards: dict[str, dict[str, list]] | None = None
    aps: dict[str, dict[str, list]] | None = None
    state_valuations: list[dict] | None = None

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

    def read_common_csr(
        self, file: UmbFile, value_type: CommonType, required: bool, file_csr: UmbFile, required_csr: bool = False
    ):
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

    def read_annotation(self, label: str, name: str, annotation: Annotation) -> dict[str, list]:
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
            assert vector is not None
            applies_values[applies] = vector
        return applies_values

    def read_annotations(
        self, label: str, annotation_info: dict[str, Annotation] | None
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
            name_applies_values[name] = self.read_annotation(label, name, annotation)
        return name_applies_values

    def read_variable_valuations(self, state_valuations: StructType | None, num_states: int) -> list[dict] | None:
        if state_valuations is None:
            return None
        chunks_csr = self.read_common(UmbFile.STATE_TO_VALUATION, required=False)
        if chunks_csr is None:
            chunks_csr = [s for s in range(num_states + 1)]
        chunks_csr = [x * state_valuations.alignment for x in chunks_csr]
        valuations = self.read_common(UmbFile.STATE_VALUATIONS, required=True)
        assert isinstance(valuations, bytes)
        # assert len(valuations) == (chunks_csr[-1]), "state valuations data length does not match expected size"
        ranges = umbi.datatypes.csr_to_ranges(chunks_csr)
        return umbi.binary.bytes_to_vector(valuations, state_valuations, ranges)

    # @no_type_check
    def read_umb(self):  # type: ignore
        logger.info(f"loading umbfile from {self.tarpath} ...")
        umb = ExplicitUmb()

        umb.index = self.read_json(UmbFile.INDEX_JSON)

        umb.state_is_initial = self.read_common(UmbFile.INITIAL_STATES, required=True)
        umb.state_to_choice = self.read_common(UmbFile.STATE_TO_CHOICE)
        umb.state_to_player = self.read_common(UmbFile.STATE_TO_PLAYER)

        umb.state_is_markovian = self.read_common(UmbFile.MARKOVIAN_STATES)
        if umb.index.transition_system.exit_rate_type is not None:
            umb.state_exit_rate = self.read_common_csr(
                UmbFile.EXIT_RATES,
                CommonType(umb.index.transition_system.exit_rate_type),
                False,
                UmbFile.STATE_TO_EXIT_RATE,
                False,
            )

        umb.choice_to_branch = self.read_common(UmbFile.CHOICE_TO_BRANCH)
        umb.choice_to_action = self.read_common(UmbFile.CHOICE_TO_ACTION)
        umb.action_strings = self.read_common_csr(
            UmbFile.ACTION_STRINGS, CommonType.STRING, False, UmbFile.ACTION_TO_ACTION_STRING, True
        )

        umb.branch_to_target = self.read_common(UmbFile.BRANCH_TO_TARGET)
        if umb.index.transition_system.branch_probability_type is not None:
            umb.branch_probabilities = self.read_common_csr(
                UmbFile.BRANCH_PROBABILITIES,
                CommonType(umb.index.transition_system.branch_probability_type),
                False,
                UmbFile.BRANCH_TO_PROBABILITY,
                False,
            )

        if umb.index.annotations is not None:
            umb.rewards = self.read_annotations("rewards", umb.index.annotations.rewards)
            umb.aps = self.read_annotations("aps", umb.index.annotations.aps)
        umb.state_valuations = self.read_variable_valuations(
            umb.index.state_valuations, umb.index.transition_system.num_states
        )

        self.list_unread_files()
        logger.info(f"finished loading the umbfile")
        return umb


class UmbWriter(TarWriter):

    def add_common(self, file: UmbFile, data, required: bool = False):
        filename, filetype = file.value
        self.add_filetype(filename, filetype, data, required=required)

    def add_common_csr(self, file: UmbFile, data, value_type: CommonType, file_csr: UmbFile, required: bool = False):
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

    def add_variable_valuations(self, valuation_type: StructType | None, state_valuations: list[dict] | None):
        if valuation_type is None:
            return
        assert state_valuations is not None
        bytestring, ranges = umbi.binary.vector_to_bytes(state_valuations, valuation_type)
        assert ranges is not None
        self.add_common(UmbFile.STATE_VALUATIONS, bytestring)
        ranges = [x // valuation_type.alignment for x in ranges]
        self.add_common(UmbFile.STATE_TO_VALUATION, ranges)

    def write_umb(self, umb: ExplicitUmb, umbpath: str):
        logger.info(f"writing umbfile to {umbpath} ...")
        self.add_index(UmbFile.INDEX_JSON, umb.index)

        self.add_common(UmbFile.INITIAL_STATES, umb.state_is_initial, required=True)
        self.add_common(UmbFile.STATE_TO_CHOICE, umb.state_to_choice)
        self.add_common(UmbFile.STATE_TO_PLAYER, umb.state_to_player)
        self.add_common(UmbFile.MARKOVIAN_STATES, umb.state_is_markovian)
        if umb.index.transition_system.exit_rate_type is not None:
            self.add_common_csr(
                UmbFile.EXIT_RATES,
                umb.state_exit_rate,
                CommonType(umb.index.transition_system.exit_rate_type),
                UmbFile.STATE_TO_EXIT_RATE,
            )
        self.add_common(UmbFile.CHOICE_TO_BRANCH, umb.choice_to_branch)
        self.add_common(UmbFile.CHOICE_TO_ACTION, umb.choice_to_action)
        self.add_common_csr(
            UmbFile.ACTION_STRINGS, umb.action_strings, CommonType.STRING, UmbFile.ACTION_TO_ACTION_STRING
        )
        self.add_common(UmbFile.BRANCH_TO_TARGET, umb.branch_to_target)
        if umb.index.transition_system.branch_probability_type is not None:
            self.add_common_csr(
                UmbFile.BRANCH_PROBABILITIES,
                umb.branch_probabilities,
                CommonType(umb.index.transition_system.branch_probability_type),
                UmbFile.BRANCH_TO_PROBABILITY,
            )
        if umb.index.annotations is not None:
            self.add_annotations("rewards", umb.index.annotations.rewards, umb.rewards)
            self.add_annotations("aps", umb.index.annotations.aps, umb.aps)
        self.add_variable_valuations(umb.index.state_valuations, umb.state_valuations)
        self.write(umbpath)
        logger.info(f"finished writing the umbfile")


def read_umb(umbpath: str) -> ExplicitUmb:
    """Read UMB from a umbfile."""
    return UmbReader(umbpath).read_umb()


def write_umb(umb: ExplicitUmb, umbpath: str):
    """Write UMB to a umbfile."""
    UmbWriter().write_umb(umb, umbpath)
