import logging
from csv import reader

logger = logging.getLogger(__name__)

from enum import Enum
from types import SimpleNamespace

import umbi


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


class ExplicitUmb:
    """Class for an explicit representation of a umbfile. The goal of this class is to have all the data is stored in numpy arrays and lists."""

    def __init__(self):
        self.index: umbi.UmbIndex = umbi.UmbIndex()

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
        logger.debug("UMB validation requested but is not implemented yet")


class UmbReader(umbi.io.TarReader):
    def __init__(self, tarpath: str):
        super().__init__(tarpath)
        # to keep track of which files were read
        self.filename_read = {filename: False for filename in self.filenames}

    def read_file(self, filename: str, required: bool = False) -> bytes | None:
        """Read raw bytes from a specific file in the tarball. Mark the file as read."""
        if filename in self.filenames:
            self.filename_read[filename] = True
        return super().read_file(filename, required)

    def warn_about_unread_files(self):
        """Print warning about unread files from the tarfile, if such exist."""
        unread_files = [f for f, read in self.filename_read.items() if not read]
        if len(unread_files) > 0:
            for f in unread_files:
                logger.warning(f"umbfile contains unrecognized file: {f}")

    def read_common(self, file: UmbFile, required: bool = False):
        filename, file_type = file.value
        if file_type == "json":
            return self.read_json(filename, required=required)
        elif file_type == "csr":
            return self.read_csr(filename, required=required)
        elif file_type == "bytes":
            return self.read_file(filename, required=required)
        elif file_type.startswith("vector[") and file_type.endswith("]"):
            value_type = file_type[len("vector[") : -1]
            return self.read_vector(filename, value_type, required=required)
        else:
            raise ValueError(f"unrecognized file type {file_type} for file {filename}")

    def read_common_csr(self, file: UmbFile, value_type: str, file_csr: UmbFile, required: bool = False):
        csr_required = False
        if value_type == "string":
            csr_required = True
        bytes = self.read_common(file, required=required)
        chunk_ranges = self.read_common(file_csr, required=csr_required)
        return umbi.io.bytes_to_vector(bytes, value_type, chunk_ranges=chunk_ranges)

    # TODO make annotation a dedicated class
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
                values = self.read_file(f"annotations/{label}/{name}/for-{applies}/values.bin", required=True)
                to_value = self.read_csr(f"annotations/{label}/{name}/for-{applies}/to-value.bin", required=False)
                annotation.values[applies] = umbi.io.bytes_to_vector(values, annotation.type, chunk_ranges=to_value)

    def read_state_valuations(self, state_valuations: dict[str, object] | None):
        # TODO implement
        if state_valuations is None:
            return
        logger.warning("state valuations import is not implemented yet")
        return

    def read_umb(self):
        logger.info(f"loading umbfile from ${self.tarpath} ...")
        umb = ExplicitUmb()

        json_obj = self.read_common(UmbFile.INDEX_JSON, required=True)
        umb.index = umbi.UmbIndex.from_json(json_obj)

        umb.initial_states = self.read_common(UmbFile.INITIAL_STATES, required=True)
        umb.state_to_choice = self.read_common(UmbFile.STATE_TO_CHOICE)
        umb.state_to_player = self.read_common(UmbFile.STATE_TO_PLAYER)

        umb.markovian_states = self.read_common(UmbFile.MARKOVIAN_STATES)
        if umb.index.transition_system.exit_rate_type is not None:
            umb.state_exit_rate = self.read_common_csr(
                UmbFile.EXIT_RATES, umb.index.transition_system.exit_rate_type, UmbFile.STATE_TO_EXIT_RATE
            )

        umb.choice_to_branch = self.read_common(UmbFile.CHOICE_TO_BRANCH)
        umb.choice_to_action = self.read_common(UmbFile.CHOICE_TO_ACTION)
        umb.action_strings = self.read_common_csr(UmbFile.ACTION_STRINGS, "string", UmbFile.ACTION_TO_ACTION_STRING)

        umb.branch_to_target = self.read_common(UmbFile.BRANCH_TO_TARGET)
        if umb.index.transition_system.branch_probability_type is not None:
            umb.branch_probabilities = self.read_common_csr(
                UmbFile.BRANCH_PROBABILITIES,
                umb.index.transition_system.branch_probability_type,
                UmbFile.BRANCH_TO_PROBABILITY,
            )

        self.read_annotation("rewards", umb.index.annotations.rewards)
        self.read_annotation("aps", umb.index.annotations.aps)
        self.read_state_valuations(umb.index.annotations.state_valuations)

        self.warn_about_unread_files()
        umb.validate()
        logger.info(f"finished loading the umbfile")
        return umb


class UmbWriter(umbi.io.TarWriter):

    def add_common(self, file: UmbFile, data, required: bool = False):
        if data is None:
            if required:
                raise ValueError(f"missing required data for {file}")
            return
        filename, file_type = file.value
        if file_type == "json":
            self.add_json(filename, data)
        elif file_type == "csr":
            self.add_csr(filename, data)
        elif file_type == "bytes":
            self.add_file(filename, data)
        elif file_type.startswith("vector[") and file_type.endswith("]"):
            value_type = file_type[len("vector[") : -1]
            self.add_vector(filename, data, value_type)
        else:
            raise ValueError(f"unrecognized file type {file_type} for file {filename}")

    def add_common_csr(self, file: UmbFile, data, value_type: str, file_csr: UmbFile, required: bool = False):
        if data is None:
            if required:
                raise ValueError(f"missing required data for {file}")
            return
        filename, _ = file.value
        filename_csr, _ = file_csr.value
        self.add_vector(filename, data, value_type, filename_csr=filename_csr)

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
                self.add_vector(f"{prefix}/values.bin", values, annotation.type, filename_csr=f"{prefix}/to-values.bin")

    def add_state_valuations(self, state_valuations: dict[str, list[float]] | None):
        if state_valuations is None:
            return
        logger.warning("state valuations export is not implemented yet")
        return

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
        self.add_state_valuations(umb.index.annotations.state_valuations)
        self.write(umbpath)
        logger.info(f"finished writing the umbfile")


def read_umb(umbpath: str) -> ExplicitUmb:
    """Read UMB from a umbfile."""
    return UmbReader(umbpath).read_umb()


def write_umb(umb: ExplicitUmb, umbpath: str):
    """Write UMB to a umbfile."""
    UmbWriter().write_umb(umb, umbpath)
