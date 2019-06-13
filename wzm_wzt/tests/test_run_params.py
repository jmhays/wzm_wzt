"""
Unit and regression test for the RunParams class.
"""

# Import package, test suite, and other packages as needed
from wzm_wzt.pair_data import PairData
from wzm_wzt.run_params import RunParams, GeneralParams, PairParams
import pytest
import json


def test_general_params(general_parameter_defaults):
    gp = GeneralParams()
    
    gp.set_from_dictionary(general_parameter_defaults)

    assert(not gp.get_missing_keys()) # Make sure we don't have any missing parameters

def test_run_params(raw_pair_data):
    rp = RunParams()

    pd = PairData()
    pd.set_from_dictionary(raw_pair_data)
    
    rp.from_pair_data(pd)
    for pair in rp.pair_params:
        assert(not rp.pair_params[pair].get_missing_keys())