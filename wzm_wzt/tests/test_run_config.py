"""Unit and regression test for the run configuration classes."""

import pytest
import os
from wzm_wzt.run_config import gmxapiConfig
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.run_params import State, PairParams, GeneralParams


def test_gmxapi_config_1(data_dir, tmpdir, state_dict):
    # Set up a state object
    state = State(filename="{}/state.json".format(tmpdir))
    state.set_from_dictionary(state_dict)
    state.pair_params['3673_12035'].set(on=True, testing=False, phase="production")

    assert not state.get_missing_keys()
    for pair in state.pair_params:
        assert not state.pair_params[pair].get_missing_keys()

    gmx_config = gmxapiConfig()
    gmx_config_defaults = {'tpr': '{}/wzmwzt.tpr'.format(data_dir), 'ensemble_dir': tmpdir, 'ensemble_num': 0}
    gmx_config.set_from_dictionary(gmx_config_defaults)
    gmx_config.load_state(state)

    assert not gmx_config.state.get_missing_keys()
    gmx_config.change_to_test_directory()
    with pytest.warns(Warning):
        gmx_config.build_plugins()

    state.pair_params['3673_12035'].set(on=True, testing=True, phase="training")
    state.write_to_json()

def test_gmxapi_config_2(data_dir, tmpdir, state_dict):
    # Set up a state object
    state = State(filename="{}/state.json".format(tmpdir))
    state.set_from_dictionary(state_dict)
    state.pair_params['3673_12035'].set(on=True, testing=False, phase="production")

    assert not state.get_missing_keys()
    for pair in state.pair_params:
        assert not state.pair_params[pair].get_missing_keys()

    gmx_config = gmxapiConfig()
    gmx_config_defaults = {'tpr': '{}/wzmwzt.tpr'.format(data_dir), 'ensemble_dir': tmpdir, 'ensemble_num': 0}
    gmx_config.set_from_dictionary(gmx_config_defaults)
    gmx_config.load_state(state)

    assert not gmx_config.state.get_missing_keys()
    gmx_config.change_to_test_directory()
    gmx_config.initialize_workflow()
    gmx_config.build_plugins()

    #print(gmx_config.workflow.workspec)

    state.pair_params['3673_12035'].set(on=True, testing=True, phase="training")
    state.write_to_json()

def test_initialize_workflow(data_dir, tmpdir, simulation):
    simulation.gmxapi.initialize_workflow(ntmpi=4)