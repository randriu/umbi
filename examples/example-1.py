import umbi

ats = umbi.from_umb("data/consensus-2-2.umb")
print(ats.num_states)
print(ats.initial_states)
print(ats.sample_path(state=52, length=10))

ats.initial_states = [100]
umbi.to_umb(ats, "data/alt.umb")

ats = umbi.from_umb("data/alt.umb")
print(ats.initial_states)
