import argparse
from pathlib import Path

import stormpy

import umbi


def existing_prism_file(path):
    """Check if the file exists and has a .prism extension."""
    p = Path(path)
    if not p.is_file():
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist.")
    if p.suffix != ".prism":
        raise argparse.ArgumentTypeError(f"File '{path}' is not a .prism file.")
    return p


def from_stormpy(model, model_name: str) -> umbi.Ats:
    ats = umbi.Ats()

    ats.info.model_data.name = model_name
    num_branches = 0
    assert model.model_type in [
        stormpy.ModelType.DTMC,
        stormpy.ModelType.CTMC,
        stormpy.ModelType.MDP,
        stormpy.ModelType.POMDP,
    ]
    ats.time = "stochastic" if model.model_type == stormpy.ModelType.CTMC else "discrete"
    if model.model_type in [stormpy.ModelType.DTMC, stormpy.ModelType.CTMC]:
        ats.num_players = 0
    if model.model_type in [stormpy.ModelType.MDP, stormpy.ModelType.MDP]:
        ats.num_players = 1

    ats.branch_values = "number"
    ats.branch_value_type = "double" if not model.is_exact else "rational"

    ats.initial_states = list(model.initial_states)

    ats.state_choices = [None] * model.nr_states
    ats.choice_branches = [None] * model.nr_choices
    ats.branch_target = []
    ats.branch_value = []

    tm = model.transition_matrix
    for state in range(ats.num_states):
        ats.state_choices[state] = list(range(tm.get_row_group_start(state), tm.get_row_group_end(state)))
        for choice in ats.state_choices[state]:
            branch_start = num_branches
            for entry in tm.get_row(choice):
                ats.branch_target.append(entry.column)
                ats.branch_value.append(entry.value())
                num_branches += 1
            branch_end = ats.num_branches
            assert branch_start < branch_end
            ats.choice_branches[choice] = list(range(branch_start, branch_end))

    # print(dir(model))
    for label in model.labeling.get_labels():
        if label == "init":
            continue
        print(f"adding state labeling {label}...")
        annotation = ats.add_annotation(label)
        annotation.name = label
        annotation.applies_to = "states"
        annotation.type = "bool"
        annotation.values = [False] * ats.num_states
        for state in model.labeling.get_states(label):
            annotation.values[state] = True

    if model.has_choice_labeling():
        for label in model.choice_labeling.get_labels():
            print(f"adding choice labeling {label}...")
            annotation = ats.add_annotation(label)
            annotation.name = label
            annotation.applies_to = "choices"
            annotation.type = "bool"
            annotation.values = [False] * ats.num_choices
            for choice in model.labeling.get_states(label):
                annotation.values[choice] = True

    for name, rm in model.reward_models.items():
        if rm.has_state_rewards:
            print(f"adding reward model {name} (states)...")
            annotation = ats.add_annotation(f"{name} (states)")
            annotation.name = name
            annotation.applies_to = "states"
            annotation.type = "double"
            annotation.values = [0] * ats.num_states
            for state in range(ats.num_states):
                annotation.values[state] = rm.get_state_reward(state)
        if rm.has_state_action_rewards:
            print(f"adding reward model {name} (choices)...")
            annotation = ats.add_annotation(f"{name} (choices)")
            annotation.name = name
            annotation.applies_to = "choices"
            annotation.type = "double"
            annotation.values = [0] * ats.num_choices
            for choice in range(ats.num_choices):
                annotation.values[choice] = rm.get_state_action_reward(choice)
    return ats


parser = argparse.ArgumentParser()
parser.add_argument("input_path", type=existing_prism_file, help="path to a PRISM model")
args = parser.parse_args()
input_path = args.input_path

model_name = input_path.stem
print(model_name)
prism_path = str(input_path)
drn_path = str(input_path.with_suffix(".drn"))
umb_path = str(input_path.with_suffix(".umb"))

print(f"loading {prism_path}...")
prism = stormpy.parse_prism_program(prism_path)
model = stormpy.build_model(prism)
stormpy.export_to_drn(model, drn_path)

print(f"creating {umb_path}...")
ats = from_stormpy(model, model_name)
print(ats.initial_states)
umbi.to_umb(ats, umb_path)

print(f"loading {umb_path}...")
ats = umbi.from_umb(umb_path)
print(ats.initial_states)
print(ats.num_players)
