import pytest
import umby


def test_ats_parser():
    ats = umby.from_umb("data/nand-20-1.tar.gz")
    assert ats.num_players == 1
    assert ats.num_states == 78332
    assert ats.state_choices[50] == [50]
    assert ats.choice_branches[52] == [94, 95]
    assert ats.index.file_data.tool == "umby"
