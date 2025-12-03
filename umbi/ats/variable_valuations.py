from dataclasses import dataclass, field

from umbi.datatypes import (
    CommonType,
    can_promote_numeric_to,
    vector_element_types,
    Numeric,
)

from collections.abc import Iterable


class Variable:
    """Variable data class."""

    # the name of the variable
    _name: str
    # sorted list of possible values
    _domain: list[object] | None = None
    # the type of variable values
    _type: CommonType | None = None

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def domain(self) -> list[object] | None:
        return self._domain

    @property
    def has_domain(self) -> bool:
        return self._domain is not None

    @property
    def lower(self) -> object | None:
        return self._domain[0] if self._domain else None

    @property
    def upper(self) -> object | None:
        return self._domain[-1] if self._domain else None

    @property
    def type(self) -> CommonType | None:
        return self._type

    def __str__(self) -> str:
        if not self.has_domain:
            return f"Variable(name={self.name}, type=?, domain=?)"
        if self.type == CommonType.INT and len(self.domain) == (self.upper - self.lower + 1):  # type: ignore
            domain_str = f"[{self.lower}..{self.upper}]"
        else:
            domain_str = str(self.domain)
        return f"Variable(name={self.name}, type={self.type}, domain={domain_str})"

    def __repr__(self) -> str:
        return self.__str__()

    def validate(self) -> None:
        if not isinstance(self.name, str):
            raise ValueError("Variable name must be a string")
        if not self.has_domain:
            return
        assert isinstance(self._type, CommonType), "Variable type must be a CommonType"
        if self.type not in [
            CommonType.BOOLEAN,
            CommonType.INT,
            CommonType.DOUBLE,
            CommonType.RATIONAL,
            CommonType.STRING,
        ]:
            raise ValueError(f"Unsupported variable type: {self.type}")

    def sync_domain(self, values: Iterable[bool | Numeric | str]) -> None:
        """Sets the variable type and domain from an iterable of values."""
        if not isinstance(values, Iterable) or not values:
            raise TypeError("values must be a non-empty iterable")
        self._domain = sorted(set(values))
        types = vector_element_types(list(values))  # TODO implement as collection_element_types
        if len(types) == 1:
            self._type = types.pop()
        else:
            # mixed types, try to deduce
            self._type = can_promote_numeric_to(types)


class VariableValuations:
    """Mapping from items to variable valuations."""

    # the variable
    _variable: Variable
    # for each item (state, action, etc.), the valuation of the variable (mutable)
    _values: list

    def __init__(self, variable: Variable):
        self._variable = variable
        self._values = []

    @property
    def variable(self) -> Variable:
        return self._variable

    @property
    def values(self) -> list:
        return self._values

    @property
    def num_items(self) -> int:
        return len(self._values)

    def __str__(self) -> str:
        return f"VariableValuations(variable={self.variable}, values={self.values})"

    def __repr__(self) -> str:
        return self.__str__()

    def ensure_capacity(self, num_items: int) -> None:
        """Ensures that the valuations list has at least num_items entries."""
        while len(self._values) < num_items:
            self._values.append(None)

    def get_item_value(self, item: int) -> object:
        """Gets the valuation for a given item index."""
        if item < 0 or item >= self.num_items:
            raise IndexError(f"item index {item} out of range [0, {self.num_items})")
        return self._values[item]

    def set_item_value(self, item: int, value: object) -> None:
        """Sets the valuation for a given item index. Increases capacity if needed."""
        self.ensure_capacity(item + 1)
        self._values[item] = value

    def sync_domain(self) -> None:
        """Sets the variable domain from the valuations."""
        self._variable.sync_domain(self._values)
        assert self._variable.type is not None

    def validate(self) -> None:
        self.sync_domain()
        self._variable.validate()


@dataclass
class ItemValuations:
    """Maintains a collection of VariableValuations."""

    # number of items (states, actions, etc.) to be associated with variable valuations
    _num_items: int = 0
    # for each variable name, the corresponding Variable
    _variable_name_to_variable: dict[str, Variable] = field(default_factory=dict)
    # for each variable, the corresponding VariableValuations
    _variable_to_valuations: dict[Variable, VariableValuations] = field(default_factory=dict)

    @property
    def variables(self) -> list[Variable]:
        """Returns a list of all variables defined."""
        return list(self._variable_to_valuations.keys())

    def __str__(self) -> str:
        lines = [f"ItemValuations(num_items={self.num_items}):"]
        for variable in self.variables:
            variable_valuation = self.get_variable_valuations(variable)
            lines.append(f"  {variable_valuation}")
        return "\n".join(lines)

    @property
    def num_variables(self) -> int:
        """Returns the number of variables defined."""
        return len(self.variables)

    @property
    def num_items(self) -> int:
        return self._num_items

    def has_variable(self, variable_name: str) -> bool:
        """Checks if a VariableValuation exists for the given variable name."""
        return variable_name in self._variable_name_to_variable

    def add_variable(self, variable_name: str) -> Variable:
        """Adds a new VariableValuation for a given variable."""
        if self.has_variable(variable_name):
            raise ValueError(f"Variable '{variable_name}' already exists.")
        variable = Variable(name=variable_name)
        self._variable_name_to_variable[variable_name] = variable
        self._variable_to_valuations[variable] = VariableValuations(variable)
        return variable

    def get_variable(self, variable_name: str) -> Variable:
        """Retrieves the Variable for a given variable name."""
        if not self.has_variable(variable_name):
            raise KeyError(f"Variable '{variable_name}' not found.")
        return self._variable_name_to_variable[variable_name]

    def get_or_add_variable(self, variable_name: str) -> Variable:
        """Retrieves the Variable for a given variable name, adding it if it does not exist."""
        if not self.has_variable(variable_name):
            return self.add_variable(variable_name)
        return self.get_variable(variable_name)

    def remove_variable(self, variable: Variable) -> None:
        """Removes the VariableValuations for a given variable."""
        if not self.has_variable(variable.name):
            raise KeyError(f"Variable '{variable.name}' not found.")
        variable = self._variable_name_to_variable[variable.name]
        del self._variable_name_to_variable[variable.name]
        del self._variable_to_valuations[variable]

    def get_variable_valuations(self, variable: Variable) -> VariableValuations:
        """Retrieves the VariableValuations for a given variable."""
        if not self.has_variable(variable.name):
            raise KeyError(f"Variable '{variable.name}' not found.")
        variable = self._variable_name_to_variable[variable.name]
        return self._variable_to_valuations[variable]

    def ensure_capacity(self, num_items: int) -> None:
        """Ensures that all VariableValuations have at least num_items entries."""
        for variable_valuation in self._variable_to_valuations.values():
            variable_valuation.ensure_capacity(num_items)
        if self._num_items < num_items:
            self._num_items = num_items

    def get_item_valuation(self, item: int) -> dict[Variable, object]:
        """Gets the variable valuations for a given item index."""
        if item < 0 or item >= self.num_items:
            raise IndexError(f"item {item} out of range [0, {self.num_items})")
        return {
            variable: variable_valuation.get_item_value(item)
            for variable, variable_valuation in self._variable_to_valuations.items()
        }

    def set_item_valuation(self, item: int, valuations: dict[Variable, object]) -> None:
        """Adds a new item with the given variable valuations."""
        self.ensure_capacity(item + 1)
        for variable, value in valuations.items():
            variable_valuation = self.get_variable_valuations(variable)
            variable_valuation.set_item_value(item, value)

    def remove_item(self, item: int) -> None:
        """Removes the valuations for a given item index."""
        raise NotImplementedError

    def sync_domains(self) -> None:
        """Synchronizes the domains of all variables based on their valuations."""
        for variable_valuation in self._variable_to_valuations.values():
            variable_valuation.sync_domain()

    def validate(self) -> None:
        self.sync_domains()
        for v in self._variable_to_valuations.keys():
            assert v.type is not None, f"Variable '{v.name}' has no type after syncing domains"
        for v in self.variables:
            assert v.type is not None, f"Variable '{v.name}' has no type after syncing domains"
        assert all(v.type is not None for v in self.variables)
        for variable_valuation in self._variable_to_valuations.values():
            if not variable_valuation.num_items == self.num_items:
                raise ValueError(
                    f"Variable '{variable_valuation.variable.name}' has {variable_valuation.num_items} "
                    f"items, expected {self.num_items}"
                )
            variable_valuation.validate()

    def __eq__(self, other) -> bool:
        if not isinstance(other, ItemValuations):
            return False
        if self.num_items != other.num_items:
            return False
        # TODO more thorough comparison
        return True
