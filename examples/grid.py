#!/usr/bin/env python3
"""
umbi demo: Create an ATS from a grid string.
"""

from fractions import Fraction

import umbi
import umbi.ats


def ats_from_grid_string(grid: str) -> umbi.ats.ExplicitAts:
    """
    Create a simple ATS from a rectangular grid string.

    :param grid: A rectangular grid string where:
        - 'i' represents the initial state
        - 'g' represents a goal state
        - 'x' represents an obstacle
        - any other character represents an empty cell
    :return: An ExplicitAts object.
    """
    # parse the grid into a 2D array
    parsed_grid = [list(row.strip()) for row in grid.strip().split("\n")]
    rows, cols = len(parsed_grid), len(parsed_grid[0])
    if any(len(row) != cols for row in parsed_grid):
        raise ValueError("The grid must be rectangular (all rows must have the same length).")

    # Create ATS
    ats = umbi.ats.ExplicitAts()
    ats.time = umbi.ats.TimeType.DISCRETE
    ats.num_players = 1

    cell_to_state = {}
    initial_states = set()
    goal_states = set()

    for y in range(rows):
        for x in range(cols):
            c = parsed_grid[y][x]
            if c == "x":
                continue
            state = len(cell_to_state)
            cell_to_state[(x, y)] = state
            if c == "i":
                initial_states.add(state)
            elif c == "g":
                goal_states.add(state)

    ats.num_states = len(cell_to_state)
    ats.set_initial_states(list(initial_states))

    directions = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    ats.state_to_choice = []
    ats.choice_to_branch = []
    ats.branch_to_target = []
    ats.branch_probabilities = []
    ats.choice_to_action = []
    ats.action_strings = list(directions.keys())
    ats.num_actions = len(ats.action_strings)

    for (x, y), state in cell_to_state.items():
        ats.state_to_choice.append(len(ats.choice_to_action))

        for action, (dx, dy) in directions.items():
            target = (x + dx, y + dy)
            ats.choice_to_action.append(ats.action_strings.index(action))
            ats.choice_to_branch.append(len(ats.branch_to_target))

            if target in cell_to_state:
                target_state = cell_to_state[target]
                ats.branch_to_target.extend([target_state, state])
                ats.branch_probabilities.extend([Fraction(9, 10), Fraction(1, 10)])
            else:
                ats.branch_to_target.append(state)
                ats.branch_probabilities.append(1)

    ats.state_to_choice.append(len(ats.choice_to_action))
    ats.choice_to_branch.append(len(ats.branch_to_target))
    ats.num_choices = len(ats.choice_to_action)
    ats.num_branches = len(ats.branch_to_target)

    ats.add_ap_annotation(
        umbi.ats.AtomicPropositionAnnotation(
            name="goal", state_to_value=[s in goal_states for s in range(ats.num_states)]
        )
    )

    ats.add_reward_annotation(
        umbi.ats.RewardAnnotation(name="step_cost", choice_to_value=[1 for _ in range(ats.num_choices)])
    )
    return ats


def main():
    umbi.setup_logging()

    grid = """
    ....x..g
    ...x....
    i.......
    ...x.x..
    ..xxxx..
    """
    ats = ats_from_grid_string(grid)
    print(f"Created ATS with {ats.num_states} states and {ats.num_choices} choices.")

    filename = "grid.umb"

    # write to file
    umbi.io.write_ats(ats, filename)

    # read back
    ats_loaded = umbi.io.read_ats(filename)
    print(f"Loaded ATS having {ats_loaded.num_states} states and {ats_loaded.num_choices} choices")

    # simple equality check using __eq__
    assert ats == ats_loaded


if __name__ == "__main__":
    main()
