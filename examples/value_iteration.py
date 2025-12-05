"""
umbi demo: Perform reachability via VI on a fitting UMBI model
"""

import argparse
import math
import pathlib

import umbi


def reachability_vi(
    model: umbi.ats.ExplicitAts,
    goal_states: set[int],
    maximizing_players: set[int],
    stopping_criterion=1e-6,
):
    if model.time != umbi.ats.TimeType.DISCRETE:
        raise NotImplementedError(
            "Reachability query only supported for discrete time models."
        )
    if any(p not in range(model.num_players) for p in maximizing_players):
        raise ValueError(
            f"Model only has {model.num_players} players, invalid maximizing players specified."
        )
    if any(s not in range(model.num_states) for s in goal_states):
        raise ValueError(
            f"Model only has {model.num_states} states, invalid goal states specified."
        )
    if not goal_states:
        return {s: 0.0 for s in model.initial_states}

    value_vector = [1.0 if s in goal_states else 0.0 for s in range(model.num_states)]
    active_states = set(range(model.num_states)) - goal_states
    if model.num_players <= 1:
        maximizing_states = active_states if 0 in maximizing_players else set()
    else:
        maximizing_states = set(
            s for s in active_states if model.state_to_player[s] in maximizing_players
        )

    while True:
        max_diff = 0.0
        solved_states = set()
        for s in active_states:
            values = (
                sum(
                    model.get_branch_probability(b)
                    * value_vector[model.get_branch_target(b)]
                    for b in model.choice_branch_range(c)
                )
                for c in model.state_choice_range(s)
            )
            new_value = max(values) if s in maximizing_states else min(values)
            assert new_value > value_vector[s] or math.isclose(
                new_value, value_vector[s]
            )
            max_diff = max(max_diff, value_vector[s] - new_value)
            value_vector[s] = new_value
            if new_value > 1.0 - 1e-14:
                solved_states.add(s)
        if max_diff < stopping_criterion:
            break
        active_states -= solved_states
        solved_states.clear()

    return {s: value_vector[s] for s in model.initial_states}


def main(args):
    ats = umbi.io.read_ats(args.filename.as_posix())
    values = reachability_vi(
        ats, set(args.goal_states), set(args.maximizing_players), args.precision
    )
    for s, v in values.items():
        if ats.has_state_valuations:
            print(
                f"({' '.join(f'{k}:{v}' for k, v in ats.state_valuations_values[s].items())}): {v}"
            )
        else:
            print(f"{s}: {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Perform reachability via (unsound) VI on a fitting UMBI model"
    )
    parser.add_argument(
        "filename", help="filename of the UMBI model to load", type=pathlib.Path
    )
    parser.add_argument(
        "--goal-states",
        help="comma-separated list of goal states",
        type=int,
        nargs="+",
        required=True,
    )
    parser.add_argument(
        "--maximizing-players",
        help="comma-separated list of maximizing players",
        type=int,
        nargs="+",
        default=[0],
    )
    parser.add_argument(
        "--precision", help="stopping criterion for VI", type=float, default=1e-6
    )
    main(parser.parse_args())
