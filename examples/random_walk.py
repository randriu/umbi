#!/usr/bin/env python3
"""
umbi demo: A random walk ATS.
"""

from fractions import Fraction

import umbi
import umbi.ats


def random_walk_ats(num_states: int) -> umbi.ats.ExplicitAts:
    # create ATS
    ats = umbi.ats.ExplicitAts()

    # basic parameters
    ats.time = umbi.ats.TimeType.DISCRETE
    ats.num_players = 0
    ats.num_states = num_states
    ats.num_initial_states = 1
    ats.set_initial_states([num_states // 2])  # start in the middle state

    # two actions: left (0) and right (1), each with 0.9 success prob
    ats.num_actions = 2
    ats.action_strings = ["left", "right"]
    ats.num_choices = 2 * ats.num_states  # each state has 2 choices (left and right)
    ats.num_branches = 2 * ats.num_choices  # each choice has 2 branches (succeed or fail)

    # build structure
    ats.state_to_choice = []
    ats.choice_to_action = []
    ats.choice_to_branch = []
    ats.branch_to_target = []
    ats.branch_probabilities = []

    for state in range(ats.num_states):
        ats.state_to_choice.append(len(ats.choice_to_action))

        # left action
        ats.choice_to_action.append(0)
        ats.choice_to_branch.append(len(ats.branch_to_target))
        left = max(0, state - 1)
        ats.branch_to_target.extend([left, state])
        ats.branch_probabilities.extend([Fraction(9, 10), Fraction(1, 10)])

        # right action
        ats.choice_to_action.append(1)
        ats.choice_to_branch.append(len(ats.branch_to_target))
        right = min(ats.num_states - 1, state + 1)
        ats.branch_to_target.extend([right, state])
        ats.branch_probabilities.extend([0.9, 0.1])

    ats.state_to_choice.append(len(ats.choice_to_action))
    ats.choice_to_branch.append(len(ats.branch_to_target))

    print(f"branch_probability_type = {ats.branch_probability_type}")

    # example: APs
    ats.add_ap_annotation(
        umbi.ats.AtomicPropositionAnnotation(
            name="is_terminal",
            alias="Terminal State",
            description="Indicates whether the state is terminal.",
            state_to_value=[s == 0 or s == ats.num_states - 1 for s in range(ats.num_states)],
        )
    )
    ats.add_ap_annotation(
        umbi.ats.AtomicPropositionAnnotation(
            name="is_odd",
            alias="Odd State",
            description="Indicates whether the state is an odd-numbered state.",
            state_to_value=[s % 2 == 1 for s in range(ats.num_states)],
        )
    )

    # example: rewards
    ats.add_reward_annotation(
        umbi.ats.RewardAnnotation(
            name="steps",
            alias="step cost",
            description="Cost incurred at each step.",
            choice_to_value=[1 for c in range(ats.num_choices)],
        )
    )

    # wall hit penalty
    choice_penalty = [0] * ats.num_choices
    for choice in ats.state_choice_range(0):
        action = ats.choice_to_action[choice]
        if ats.action_strings[action] == "left":  # left action in first state
            choice_penalty[choice] = -10
    for choice in ats.state_choice_range(ats.num_states - 1):
        action = ats.choice_to_action[choice]
        if ats.action_strings[action] == "right":  # right action in last state
            choice_penalty[choice] = -10
    ats.add_reward_annotation(
        umbi.ats.RewardAnnotation(
            name="wall_hit_penalty",
            alias="wall hit penalty",
            description="Penalty incurred when hitting a wall.",
            choice_to_value=choice_penalty,
        )
    )

    # arbitrary mixed rewards
    ats.add_reward_annotation(
        umbi.ats.RewardAnnotation(
            name="combined_reward",
            state_to_value=[Fraction((s * 3 + 1), (s + 2)) for s in range(ats.num_states)],
            choice_to_value=[Fraction((c * 5 + 2), (c + 4)) for c in range(ats.num_choices)],
            branch_to_value=[Fraction((b * 2 + 1), (b + 3)) for b in range(ats.num_branches)],
        )
    )

    # observations: 3 observations, based on state mod 3
    ats.observation_annotation = umbi.ats.ObservationAnnotation(
        num_observations=3, state_to_value=[s % 3 for s in range(ats.num_states)]
    )

    return ats


def main():
    umbi.setup_logging()
    ats = random_walk_ats(num_states=10)
    filename = "random_walk.umb"

    # write to file
    umbi.io.write_ats(ats, filename)
    print(f"Wrote ATS to {filename}")

    # read back
    ats_loaded = umbi.io.read_ats(filename)
    print(f"Loaded ATS from {filename}: {ats_loaded.num_states} states, {ats_loaded.num_actions} actions")

    # simple equality check using __eq__
    assert ats == ats_loaded


if __name__ == "__main__":
    main()
