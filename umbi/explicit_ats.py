# import umbi


class ExplicitAts:
    """Annotated transition system in an explicit format matching the .umb file format."""

    def __init__(self):
        self.info = None

        self.initial_states = None
        self.state_choices = None
        self.state_to_player = None
        self.exit_rates = None

        self.choice_branches = None
        self.branch_target = None
        self.branch_probabilities = None

        self.choice_to_action = None
        self.branch_to_action = None
        self.action_to_string = None

        self.annotations = {}
