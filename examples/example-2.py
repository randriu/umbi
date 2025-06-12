import umbi

ats = umbi.Ats()
ats.time = "discrete"
ats.branch_values = "number"
ats.branch_value_type = "double"
ats.initial_states = [2]

ats.state_choices = [[0, 1], [2, 3], [4], [5], [6, 7], [8, 9]]
ats.choice_branches = [[0, 1], [2, 3, 4], [5], [6, 7], [8], [9], [10], [11, 12], [13], [14, 15]]

ats.branch_target = [0, 1, 1, 3, 4, 2, 2, 4, 2, 3, 5, 3, 4, 4, 2, 5]
ats.branch_value = [0.4, 0.6, 0.1, 0.8, 0.1, 1, 0.5, 0.5, 1, 1, 1, 0.6, 0.4, 1, 0.9, 0.1]

umbi.to_umb(ats, "simple.umb")

ats = umbi.from_umb("simple.umb")
print(ats.initial_states)
