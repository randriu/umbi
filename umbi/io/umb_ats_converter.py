import time

import umbi
import umbi.ats
from umbi.datatypes import (
    CommonType,
    promote_to_vector_of_numeric,
    vector_promotion_type,
)

from .index import (
    Annotation,
    Annotations,
    FileData,
    ModelData,
    TransitionSystem,
    UmbIndex,
)
from .umb import ExplicitUmb, read_umb, write_umb


def umbi_file_data() -> FileData:
    return FileData(
        tool=umbi.version.__toolname__,
        tool_version=umbi.version.__version__,
        creation_date=int(time.time()),
        # parameters=parameters,
    )


def umb_annotation_to_ats_annotation(
    umb_annotation: Annotation, applies_to_values: dict[str, list], ats_annotation: umbi.ats.Annotation
):
    for applies_to in umb_annotation.applies_to or []:
        if applies_to == "states":
            ats_annotation.state_to_value = applies_to_values["states"]
        elif applies_to == "choices":
            ats_annotation.choice_to_value = applies_to_values["choices"]
        elif applies_to == "branches":
            ats_annotation.branch_to_value = applies_to_values["branches"]


def ats_annotation_to_umb_annotation(annotation: umbi.ats.Annotation) -> tuple[Annotation, dict[str, list]]:
    applies_to = []
    applies_to_values = {}
    target_type = annotation.type
    for key, values in [
        ("states", annotation.state_to_value),
        ("choices", annotation.choice_to_value),
        ("branches", annotation.branch_to_value),
    ]:
        if values is not None:
            applies_to.append(key)
            if target_type not in [CommonType.STRING, CommonType.BOOLEAN]:
                # implicit promotion
                values = promote_to_vector_of_numeric(values, target_type)
            applies_to_values[key] = values
    umb_annotation = Annotation(
        alias=annotation.alias,
        description=annotation.description,
        applies_to=applies_to,
        type=annotation.type.value,
        lower=None,
        upper=None,
    )
    return umb_annotation, applies_to_values


def explicit_umb_to_explicit_ats(umb: ExplicitUmb) -> umbi.ats.ExplicitAts:
    umb.validate()
    ats = umbi.ats.ExplicitAts()

    ## index
    # skip format_version
    # skip format_revision
    md = umb.index.model_data
    if md is not None:
        ats.model_info = umbi.ats.ModelInfo(
            name=md.name,
            version=md.version,
            authors=md.authors,
            description=md.description,
            comment=md.comment,
            doi=md.doi,
            url=md.url,
        )
    # skip file_data
    # load index.transition_system fields into ats
    ts = umb.index.transition_system
    ats.time = umbi.ats.TimeType(ts.time)
    ats.num_players = ts.num_players
    ats.num_states = ts.num_states
    ats.num_initial_states = ts.num_initial_states
    ats.num_choices = ts.num_choices
    ats.num_actions = ts.num_actions
    ats.num_branches = ts.num_branches
    ats.num_observations = ts.num_observations

    # load annotations
    if umb.index.annotations is not None:
        if umb.index.annotations.rewards is not None:
            assert umb.rewards is not None
            for name, umb_annotation in umb.index.annotations.rewards.items():
                assert name in umb.rewards
                applies_to_values = umb.rewards[name]
                ats_annotation = umbi.ats.RewardAnnotation(
                    name=name,
                    type=CommonType(umb_annotation.type) if umb_annotation.type is not None else CommonType.BOOLEAN,
                    alias=umb_annotation.alias,
                    description=umb_annotation.description,
                )
                umb_annotation_to_ats_annotation(umb_annotation, applies_to_values, ats_annotation)
                ats.add_reward_annotation(ats_annotation)
        if umb.index.annotations.aps is not None:
            assert umb.aps is not None
            for name, umb_annotation in umb.index.annotations.aps.items():
                assert name in umb.aps
                applies_to_values = umb.aps[name]
                ats_annotation = umbi.ats.AtomicPropositionAnnotation(
                    name=name,
                    alias=umb_annotation.alias,
                    description=umb_annotation.description,
                )
                umb_annotation_to_ats_annotation(umb_annotation, applies_to_values, ats_annotation)
                ats.add_ap_annotation(ats_annotation)

    ## values
    ats.state_is_initial = umb.state_is_initial
    ats.state_to_choice = umb.state_to_choice
    ats.state_to_player = umb.state_to_player

    ats.state_is_markovian = umb.state_is_markovian
    ats.state_exit_rate = umb.state_exit_rate

    ats.choice_to_branch = umb.choice_to_branch
    ats.choice_to_action = umb.choice_to_action
    ats.action_strings = umb.action_strings

    ats.branch_to_target = umb.branch_to_target
    ats.branch_probabilities = umb.branch_probabilities

    # TODO consolidate into one structure
    ats.state_valuations = umb.index.state_valuations
    ats.state_valuations_values = umb.state_valuations

    ats.validate()
    return ats


def explicit_ats_to_explicit_umb(ats: umbi.ats.ExplicitAts) -> ExplicitUmb:
    ats.validate()
    umb = ExplicitUmb()

    ## index
    # insert our format_version, format_revision

    reward_annotations = {}
    reward_values = {}
    for name, ats_annotation in ats.reward_annotations.items():
        umb_annotation, applies_to_values = ats_annotation_to_umb_annotation(ats_annotation)
        reward_values[name] = applies_to_values
        reward_annotations[name] = umb_annotation
    ap_annotations = {}
    ap_values = {}
    for name, ats_annotation in ats.ap_annotations.items():
        umb_annotation, applies_to_values = ats_annotation_to_umb_annotation(ats_annotation)
        ap_values[name] = applies_to_values
        ap_annotations[name] = umb_annotation

    umb.index = UmbIndex(
        format_version=umbi.version.__format_version__,
        format_revision=umbi.version.__format_revision__,
        # create transition_system from matching fields
        transition_system=TransitionSystem(
            time=ats.time.value,
            num_players=ats.num_players,
            num_states=ats.num_states,
            num_initial_states=ats.num_initial_states,
            num_choices=ats.num_choices,
            num_actions=ats.num_actions,
            num_branches=ats.num_branches,
            num_observations=ats.num_observations,
            branch_probability_type=None,  # for now
            exit_rate_type=None,  # for now
        ),
        model_data=(
            ModelData(
                name=ats.model_info.name,
                version=ats.model_info.version,
                authors=ats.model_info.authors,
                description=ats.model_info.description,
                comment=ats.model_info.comment,
                doi=ats.model_info.doi,
                url=ats.model_info.url,
            )
            if ats.model_info is not None
            else None
        ),
        # insert our file_data
        file_data=umbi_file_data(),
        # create annotations
        annotations=Annotations(
            rewards=reward_annotations,
            aps=ap_annotations,
        ),
        state_valuations=ats.state_valuations,
    )
    ## values
    umb.state_is_initial = ats.state_is_initial
    umb.state_to_choice = ats.state_to_choice
    umb.state_to_player = ats.state_to_player

    umb.state_is_markovian = ats.state_is_markovian
    if ats.state_exit_rate is not None:
        # derive promotion type and promote
        target_type = ats.exit_rate_type
        assert target_type is not None
        umb.index.exit_rate_type = target_type.value
        umb.state_exit_rate = promote_to_vector_of_numeric(ats.state_exit_rate, target_type)

    umb.choice_to_branch = ats.choice_to_branch
    umb.choice_to_action = ats.choice_to_action
    umb.action_strings = ats.action_strings

    umb.branch_to_target = ats.branch_to_target
    if ats.branch_probabilities is not None:
        # derive promotion type and promote
        target_type = ats.branch_probability_type
        assert target_type is not None
        umb.index.branch_probability_type = target_type.value
        umb.branch_probabilities = promote_to_vector_of_numeric(ats.branch_probabilities, target_type)

    umb.rewards = reward_values
    umb.aps = ap_values
    umb.state_valuations = ats.state_valuations_values

    umb.validate()
    return umb


def read_ats(umbpath: str) -> umbi.ats.ExplicitAts:
    """Read ATS from a umbfile."""
    umb = read_umb(umbpath)
    ats = explicit_umb_to_explicit_ats(umb)
    return ats


def write_ats(ats: umbi.ats.ExplicitAts, umbpath: str):
    """Write ATS to a umbfile."""
    umb = explicit_ats_to_explicit_umb(ats)
    write_umb(umb, umbpath)
