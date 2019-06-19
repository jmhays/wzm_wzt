"""Unit and regression test for the run configuration classes."""

import pytest
import os
from wzm_wzt.run_config import gmxapiConfig
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.run_params import State, PairParams, GeneralParams


def test_gmxapi_config_1(data_dir, tmpdir, state_dict):
    gmx_config_defaults = {'tpr': '{}/wzmwzt.tpr'.format(data_dir), 'ensemble_dir': tmpdir, 'ensemble_num': 0}
    gmx_config = gmxapiConfig()
    gmx_config.set_from_dictionary(gmx_config_defaults)
    #assert not gmx_config.get_missing_keys()

    # Set up a state object
    state = State(filename="{}/state.json".format(gmx_config_defaults["ensemble_dir"]))
    state.set_from_dictionary(state_dict)
    state.pair_params['3673_12035'].set(on=True, testing=False, phase="production")

    assert not state.get_missing_keys()
    for pair in state.pair_params:
        assert not state.pair_params[pair].get_missing_keys()

    gmx_config.initialize(state)
    assert not gmx_config.state.get_missing_keys()

    site_name = '3673_5636'
    gmx_config.change_to_test_directory(site_name)
    gmx_config.build_plugins(site_name)

def test_gmxapi_config_2(data_dir, tmpdir, state_dict):
    gmx_config_defaults = {'tpr': '{}/wzmwzt.tpr'.format(data_dir), 'ensemble_dir': tmpdir, 'ensemble_num': 0}
    gmx_config = gmxapiConfig()
    gmx_config.set_from_dictionary(gmx_config_defaults)
    #assert not gmx_config.get_missing_keys()

    # Set up a state object
    state = State(filename="{}/state.json".format(gmx_config_defaults["ensemble_dir"]))
    state.set_from_dictionary(state_dict)
    state.pair_params['3673_12035'].set(on=True, testing=False, phase="production")
    state.pair_params['10088_12035'].set(on=True, testing=False, phase="production")

    assert not state.get_missing_keys()
    for pair in state.pair_params:
        assert not state.pair_params[pair].get_missing_keys()

    gmx_config.initialize(state)
    assert not gmx_config.state.get_missing_keys()

    site_name = '3673_5636'
    gmx_config.state.pair_params[site_name].set(phase="convergence")
    gmx_config.change_to_test_directory(site_name)
    gmx_config.build_plugins(site_name)

def test_gmxapi_run(data_dir, tmpdir, state_dict):
    gmx_config_defaults = {'tpr': '{}/wzmwzt.tpr'.format(data_dir), 'ensemble_dir': tmpdir, 'ensemble_num': 0}
    gmx_config = gmxapiConfig()
    gmx_config.set_from_dictionary(gmx_config_defaults)
    #assert not gmx_config.get_missing_keys()

    # Set up a state object
    state = State(filename="{}/state.json".format(gmx_config_defaults["ensemble_dir"]))
    state.set_from_dictionary(state_dict)

    assert not state.get_missing_keys()
    for pair in state.pair_params:
        assert not state.pair_params[pair].get_missing_keys()

    gmx_config.initialize(state)
    assert not gmx_config.state.get_missing_keys()

    site_name = '3673_5636' 
    current_dir = os.getcwd()
    gmx_config.change_to_test_directory(site_name)
    gmx_config.build_plugins(site_name)
    gmx_config.run()
    os.chdir(current_dir)
