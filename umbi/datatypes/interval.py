"""
Interval datatype.
"""

from .common_type import Numeric


class Interval:
    """Represents a numeric interval where left <= right."""
    
    def __init__(self, left: Numeric, right: Numeric) -> None:
        self.left = left
        self.right = right
        self.validate()
    
    def validate(self) -> None:
        assert isinstance(self.left, Numeric), f"expected numeric left bound, got: {self.left}"
        assert isinstance(self.right, Numeric), f"expected numeric right bound, got: {self.right}"
        if not self.left <= self.right:
            raise ValueError(f"expected {self.left} <=  {self.right}")

    def __str__(self) -> str:
        return f"interval[{self.left},{self.right}]"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            raise ValueError("can only compare Interval with another Interval")
        return self.left == other.left and self.right == other.right
    
    def __contains__(self, value: Numeric) -> bool:
        """Check if a numeric value is within the interval."""
        return self.left <= value <= self.right

