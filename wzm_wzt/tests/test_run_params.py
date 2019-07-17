"""
Unit and regression test for the RunParams class.
"""

from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.run_params import GeneralParams, PairParams, State
from wzm_wzt.metadata import site_to_str
import pytest
import json
import os

def test_general_params(raw_deer_data):
    experimental_data = ExperimentalData()
    experimental_data.set_from_dictionary(raw_deer_data)

    gp = GeneralParams()
    gp.set_to_defaults()
    gp.load_experimental_data(experimental_data)

    assert not gp.get_missing_keys()
    assert gp.get("distribution")

def test_pair_params(sites):
    if "sites" in sites:
        sites = sites["sites"]
    for site in sites:
        pair_param = PairParams(site)
        pair_param.load_sites(sites[site])
        pair_param.set_to_defaults()
        assert not pair_param.get_missing_keys()

def test_state(raw_deer_data, sites, tmpdir):
    experimental_data = ExperimentalData()
    experimental_data.set_from_dictionary(raw_deer_data)

    gp = GeneralParams()
    gp.load_experimental_data(experimental_data)
    
    state = State(filename="{}/state.json".format(os.getcwd()))

    # Check that a whole bunch of warnings show up
    with pytest.warns(Warning):
        state.import_general_parameters(gp)
    gp.set_to_defaults()
    gp.set(bins=None, distribution=None)
    with pytest.warns(Warning):
        state.import_general_parameters(gp)
    gp.set(bins=[0.1])
    with pytest.warns(Warning):
        state.import_general_parameters(gp)

    # Now warnings for pair parameters
    if "sites" in sites:
        sites = sites["sites"]
    for site in sites:
        pair_param = PairParams(name=site)
        pair_param.set_to_defaults()
        with pytest.warns(Warning):
            state.import_pair_parameters(pair_param)
        pair_param.load_sites(sites[site])
        pair_param.set_to_defaults()
        with pytest.warns(Warning):
            state.import_pair_parameters(pair_param)
    
    assert not state.get_missing_keys()
    assert not state.general_params.get_missing_keys()
    for name in state.pair_params:
        assert not state.pair_params[name].get_missing_keys()
    assert not state.get_all_missing_keys()
    state.write_to_json()
    state.new_iteration()

    #TODO: check that all the appropriate warnings are raised.
