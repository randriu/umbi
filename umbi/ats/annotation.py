from enum import Enum

from umbi.datatypes import CommonType, Numeric


class Annotation:
    """General annotation."""

    # TODO add lower: float | None = None
    # TODO add upper: float | None = None

    def __init__(
        self,
        name: str,
        type: CommonType,
        alias: str | None = None,
        description: str | None = None,
        state_to_value: list[Numeric] | None = None,
        choice_to_value: list[Numeric] | None = None,
        branch_to_value: list[Numeric] | None = None,
    ):
        self._name = name
        if not type in [
            CommonType.BOOLEAN,
            CommonType.STRING,
            CommonType.DOUBLE,
            CommonType.RATIONAL,
            CommonType.DOUBLE_INTERVAL,
            CommonType.RATIONAL_INTERVAL,
        ]:
            raise ValueError(f"Invalid annotation type: {type}")
        self._type = type
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
        return self._type

    def validate(self) -> None:
        """Validate the annotation data."""
        # TODO check datatypes
        # TODO check lower
        # TODO check upper
        pass


class RewardAnnotation(Annotation):
    """Reward annotation data class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.type not in [
            CommonType.DOUBLE,
            CommonType.RATIONAL,
            CommonType.DOUBLE_INTERVAL,
            CommonType.RATIONAL_INTERVAL,
        ]:
            raise ValueError(f"Invalid reward annotation type: {self.type}")


class AtomicPropositionAnnotation(Annotation):
    """Atomic proposition annotation data class."""

    def __init__(
        self,
        name: str,
        alias: str | None = None,
        description: str | None = None,
        state_to_value: list[Numeric] | None = None,
        choice_to_value: list[Numeric] | None = None,
        branch_to_value: list[Numeric] | None = None,
    ):
        super().__init__(
            name=name,
            type=CommonType.BOOLEAN,
            alias=alias,
            description=description,
            state_to_value=state_to_value,
            choice_to_value=choice_to_value,
            branch_to_value=branch_to_value,
        )
        if self.type != CommonType.BOOLEAN:
            raise ValueError(f"Invalid atomic proposition annotation type: {self.type}")
