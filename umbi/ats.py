import collections
import random

import umbi


class SimpleAts:
    """Annotated transition system."""

    def __init__(self):
        self.info = umbi.AtsInfoSchema.empty_object()

        self.time = None
        self.branch_probability_type = None

        self.num_players = 1
        self.num_actions = 1

        self.initial_states = None
        self.state_choices = []
        self.choice_branches = []
        self.branch_target = []
        self.branch_value = []
        self.annotations = {}

    def validate_field_set(self, field: str):
        field_value = getattr(self, field)
        if field_value is None:
            raise ValueError(f"SimpleAts: field '{field}' is not set")

    def validate_field_in(self, field: str, domain: list):
        """Validate that the field has the value within the given domain."""
        self.validate_field_set(field)
        field_value = getattr(self, field)
        if field_value not in domain:
            raise ValueError(f"SimpleAts: field '{field}' must be in {domain}")

    @staticmethod
    def validate_is_list(l, name, length=None):
        if not isinstance(l, list):
            raise ValueError(f"SimpleAts: '{name}' must be a list")
        if length is not None and not len(l) == length:
            raise ValueError(f"SimpleAts: '{name}' must be of length {length}")

    @property
    def num_states(self):
        return len(self.state_choices)

    @property
    def num_initial_states(self):
        return len(self.initial_states)

    @property
    def num_choices(self):
        return len(self.choice_branches)

    @property
    def num_branches(self):
        return len(self.branch_target)

    def validate(self):
        self.validate_field_in("time", ["discrete", "stochastic", "urgent-stochastic"])
        self.validate_field_in("branch_values", ["none", "number", "interval"])
        if self.branch_values != "none":
            self.validate_field_in("branch_value_type", ["double", "rational"])

        self.validate_field_set("num_states")
        self.validate_field_set("num_initial_states")
        self.validate_field_set("num_choices")
        self.validate_field_set("num_branches")
        self.validate_field_set("num_players")
        self.validate_field_set("num_actions")

        SimpleAts.validate_is_list(self.initial_states, "initial_states")
        if not all([state < self.num_states for state in self.initial_states]):
            raise ValueError(f"SimpleAts: invalid initial states")

        SimpleAts.validate_is_list(self.choice_branches, "choice_branches", self.num_choices)
        for choice, branches in enumerate(self.choice_branches):
            SimpleAts.validate_is_list(branches, f"choice_branches[{choice}]")
            if not len(branches) > 0:
                raise ValueError(f"SimpleAts: 'choice_branches[{choice}]' must be a non-empty list")

        SimpleAts.validate_is_list(self.branch_target, "branch_target")
        SimpleAts.validate_is_list(self.branch_value, "branch_target")

    # def add_state(self):
    #     self.state_choices.append([])

    # def add_states(self, num_new_states : int):
    #     for _ in range(num_new_states):
    #         self.add_state()

    def add_annotation(self, key: str):
        if key in self.annotations:
            print(f"warning: redefining annotation {key}")
        annotation = umbi.AnnotationSchema.empty_object()
        self.annotations[key] = annotation
        return annotation

    def choice_successors(self, choice: int) -> set:
        successors = set()
        for branch in self.choice_branches[choice]:
            successors.add(self.branch_target[branch])
        return successors

    def state_successors(self, state: int) -> set:
        successors = set()
        for choice in self.state_choices[state]:
            successors.update(self.choice_successors(choice))
        return successors

    def choice_distribution(self, choice: int) -> dict:
        distr = collections.defaultdict(int)
        for branch in self.choice_branches[choice]:
            target, value = self.branches[branch]
            distr[target] += value
        return dict(distr)

    def sample_choice(self, state: int) -> int:
        return random.choice(self.state_choices[state])

    def sample_choice_target(self, choice: int) -> int:
        distr = self.choice_distribution(choice)
        target = random.choices(population=list(distr.keys()), weights=list(distr.values()), k=1)[0]
        return target

    def sample_path(self, state=None, length=0):
        if state is None:
            state = random.choice(self.initial_states)
        path = [state]
        for _ in range(length):
            choice = self.sample_choice(state)
            state = self.sample_choice_target(choice)
            path.append(state)
        return path
