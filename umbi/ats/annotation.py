from enum import Enum

from umbi.datatypes import (
    CommonType,
    Numeric,
    common_numeric_type,
    is_numeric_type,
    vector_element_types,
)


class AnnotationAppliesTo(str, Enum):
    """Applies-to types for annotations."""

    STATES = "states"
    CHOICES = "choices"
    BRANCHES = "branches"


class Annotation:
    """General annotation."""

    # TODO add lower: float | None = None
    # TODO add upper: float | None = None

    def __init__(
        self,
        name: str,
        alias: str | None = None,
        description: str | None = None,
        state_to_value: list | None = None,
        choice_to_value: list | None = None,
        branch_to_value: list | None = None,
    ):
        self._name = name
        self.alias = alias
        self.description = description
        self.state_to_value = state_to_value
        self.choice_to_value = choice_to_value
        self.branch_to_value = branch_to_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> CommonType:
        types: set[CommonType] = set()
        for v in [self.state_to_value, self.choice_to_value, self.branch_to_value]:
            if v is not None:
                types.update(vector_element_types(v))
        if len(types) == 0:
            raise ValueError("Annotation has no values to determine type from")
        if len(types) == 1:
            return types.pop()
        return common_numeric_type(types)

    @property
    def mappings(self) -> dict[AnnotationAppliesTo, list]:
        """Get all non-None mappings as a dictionary."""
        return {
            k: v
            for k, v in [
                (AnnotationAppliesTo.STATES, self.state_to_value),
                (AnnotationAppliesTo.CHOICES, self.choice_to_value),
                (AnnotationAppliesTo.BRANCHES, self.branch_to_value),
            ]
            if v is not None
        }

    def validate(self) -> None:
        """Validate the annotation data."""
        if not isinstance(self.name, str):
            raise ValueError("name must be a string")
        if not isinstance(self.alias, (str, type(None))):
            raise ValueError("alias must be a string or None")
        if not isinstance(self.description, (str, type(None))):
            raise ValueError("description must be a string or None")
        if len(self.mappings) == 0:
            raise ValueError("At least one of *_to_value must be set")
        # TODO check datatypes
        # TODO check lower
        # TODO check upper
        pass


class RewardAnnotation(Annotation):
    """Reward annotation data class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self):
        super().validate()
        # Additional validation for reward annotations can be added here
        if not is_numeric_type(self.type):
            raise ValueError(f"Reward annotation type must be numeric ({self.type})")


class AtomicPropositionAnnotation(Annotation):
    """Atomic proposition annotation data class."""

    def __init__(
        self,
        name: str,
        alias: str | None = None,
        description: str | None = None,
        state_to_value: list[bool] | None = None,
        choice_to_value: list[bool] | None = None,
        branch_to_value: list[bool] | None = None,
    ):
        super().__init__(
            name=name,
            alias=alias,
            description=description,
            state_to_value=state_to_value,
            choice_to_value=choice_to_value,
            branch_to_value=branch_to_value,
        )

    def validate(self):
        super().validate()
        # Additional validation for AP annotations can be added here
        if self.type != CommonType.BOOLEAN:
            raise ValueError(f"Atomic proposition annotation type must be boolean ({self.type})")


class ObservationAnnotation(Annotation):
    """Observation annotation data class."""

    def __init__(
        self,
        num_observations: int,
        state_to_value: list[int] | None = None,
        choice_to_value: list[int] | None = None,
        branch_to_value: list[int] | None = None,
    ):
        super().__init__(
            name="observation",
            alias=None,
            description=None,
            state_to_value=state_to_value,
            choice_to_value=choice_to_value,
            branch_to_value=branch_to_value,
        )
        self.num_observations = num_observations

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.num_observations == other.num_observations

    @property
    def applies_to_mapping(self) -> tuple[AnnotationAppliesTo, list[int]]:
        """Get the applies-to type and mapping (only one of the three mappings will be set)."""
        mappings = self.mappings
        if len(mappings) != 1:
            raise ValueError("Observation annotation must have exactly one mapping set")
        return next(iter(mappings.items()))

    @property
    def applies_to(self) -> AnnotationAppliesTo:
        """Get the applies-to type."""
        return self.applies_to_mapping[0]

    @property
    def mapping(self) -> list[int]:
        """Get the observation mapping."""
        return self.applies_to_mapping[1]

    def validate(self) -> None:
        super().validate()
        if not (isinstance(self.num_observations, int) and 0 < self.num_observations):
            raise ValueError(f"num_observations must be a positive integer, got {self.num_observations}")
        for item, obs in enumerate(self.mapping):
            if not 0 <= obs < self.num_observations:
                raise ValueError(f"observation mapping[{item}] = {obs} is out of range [0, {self.num_observations})")
