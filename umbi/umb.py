import logging
logger = logging.getLogger(__name__)

import umbi
from enum import Enum
from types import SimpleNamespace

class UmbFile(Enum):
    """ A list of common files in a .umb file. Each entry is a tuple of (filename, filetype, required)."""
    INDEX_JSON = ("index.json", "json", True)

    INITIAL_STATES = ("initial-states.bin", "vector[bool]", True)
    STATE_TO_CHOICE = ("state-to-choice.bin", "csr", False)
    STATE_TO_PLAYER = ("state-to-player.bin", "vector[uint32]", False)

    MARKOVIAN_STATES = ("markovian-states.bin", "vector[bool]", False)
    STATE_TO_EXIT_RATE = ("state-to-exit-rate.bin", "csr", False)
    EXIT_RATES = ("exit-rates.bin", "bytes", False)

    CHOICE_TO_BRANCH = ("choice-to-branch.bin", "csr", False)
    CHOICE_TO_ACTION = ("choice-to-action.bin", "vector[uint32]", False)
    ACTION_TO_ACTION_STRING = ("action-to-action-string.bin", "csr", False)
    ACTION_STRINGS = ("action-strings.bin", "bytes", False)

    BRANCH_TO_TARGET = ("branch-to-target.bin", "vector[uint64]", False)
    BRANCH_TO_PROBABILITY = ("branch-to-probability.bin", "csr", False)
    BRANCH_PROBABILITIES = ("branch-probabilities.bin", "bytes", False)


class UmbReader(umbi.io.TarReader):
    def __init__(self, tarpath: str):
        super().__init__(tarpath)
        # to keep track of which files were read
        self.filename_read = {filename: False for filename in self.filenames}
    
    def read_file(self, filename: str, required : bool = True) -> bytes | None:
        """Read raw bytes from a specific file in the tarball. Marks the file as read."""
        if filename in self.filenames:
            self.filename_read[filename] = True
        return super().read_file(filename,required)
    
    def warn_unread_files(self):
        """Print warning about unread files from the tarfile, if such exist."""
        unread_files = [f for f, read in self.filename_read.items() if not read]
        if len(unread_files) > 0:
            unread_files_str = "\n".join(unread_files)
            logger.warning(
                f'the following files from "{self.tarpath}" were not used during parsing:\n{unread_files_str}'
            )
        
    def read_common(self, file: UmbFile):
        filename, file_type, required = file.value
        if file_type == "json":
            return self.read_json(filename,required)
        elif file_type == "bytes":
            return self.read_file(filename,required)
        elif file_type.startswith("vector[") and file_type.endswith("]"):
            value_type = file_type[len("vector[") : -1]
            return self.read_vector(filename, value_type, required=required)
        elif file_type == "csr":
            return self.read_csr(filename, required=required)
        elif file_type == "bitvector":
            return self.read_bitvector_indices(filename, required=required)
        else:
            raise ValueError(f"unrecognized file type {file_type} for file {filename}")
    
    def read_annotation(self, annotation_label: str, annotation_dict: dict[str,SimpleNamespace] | None):
        if annotation_dict is None:
            return None
        path = f"annotations/{annotation_label}"
        for key, annotation in annotation_dict.items():
            annotation.data = dict()
            for applies in annotation.applies_to:
                annotation.data[applies] = self.read_csr(f"{path}/{key}/for-{applies}/to-value.bin", required=False)
                annotation.data[applies] = self.read_file(f"{path}/{key}/for-{applies}/values.bin", required=False)

    def read_state_valuations(self, state_valuations: dict[str, object]):
        # TODO implement
        return None

class ExplicitUmb:
    """Class for an explicit representation of a .umb file."""

    def __init__(self):
        self.index : umbi.UmbIndex = umbi.UmbIndex()

        self.initial_states = None
        self.state_to_choice = None
        self.state_to_player = None

        self.markovian_states = None
        self.state_to_exit_rate = None
        self.exit_rates = None

        self.choice_to_branch = None
        self.choice_to_action = None
        self.action_to_action_string = None
        self.action_strings = None

        self.branch_to_target = None
        self.branch_to_probability = None
        self.branch_probabilities = None

        self.rewards = None
        self.aps = None
        self.state_valuations = None


    def load(self, tarpath : str):
        logger.info(f"loading from ${tarpath}")
        reader = UmbReader(tarpath)

        json_obj = reader.read_common(UmbFile.INDEX_JSON)
        self.index = umbi.UmbIndex.from_json(json_obj)

        self.initial_states = reader.read_common(UmbFile.INITIAL_STATES)
        self.state_to_choice = reader.read_common(UmbFile.STATE_TO_CHOICE)
        self.state_to_player = reader.read_common(UmbFile.STATE_TO_PLAYER)

        self.markovian_states = reader.read_common(UmbFile.MARKOVIAN_STATES)
        self.state_to_exit_rate = reader.read_common(UmbFile.STATE_TO_EXIT_RATE)
        self.exit_rates = reader.read_common(UmbFile.EXIT_RATES)

        self.choice_to_branch = reader.read_common(UmbFile.CHOICE_TO_BRANCH)
        self.choice_to_action = reader.read_common(UmbFile.CHOICE_TO_ACTION)
        self.action_to_action_string = reader.read_common(UmbFile.ACTION_TO_ACTION_STRING)
        self.action_strings = reader.read_common(UmbFile.ACTION_STRINGS)

        self.branch_to_target = reader.read_common(UmbFile.BRANCH_TO_TARGET)
        self.branch_to_probability = reader.read_common(UmbFile.BRANCH_TO_PROBABILITY)
        self.branch_probabilities = reader.read_common(UmbFile.BRANCH_PROBABILITIES)

        self.rewards = reader.read_annotation("rewards", self.index.annotations.rewards)
        self.aps = reader.read_annotation("aps", self.index.annotations.aps)
        self.state_valuations = reader.read_state_valuations(self.index.annotations.state_valuations)

        reader.warn_unread_files()
        logger.info(f"loaded input .umb file")

    def validate(self):
        #TODO implement
        logger.debug("validating the .umb file ...")
        logger.debug("validation complete")
        exit()


def read_umb(tarpath: str) -> ExplicitUmb:
    """Read ATS from a .umb file."""
    umb = ExplicitUmb()
    umb.load(tarpath)
    umb.validate()
    return ats

