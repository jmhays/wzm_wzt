#!/usr/bin/env python
"""
wzm_wzt.py
Testing correlation structure calculations using ABC transporter Wzm-Wzt.

Handles the primary functions
"""

import json
import os
from wzm_wzt.run_params import State, GeneralParams, PairParams
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.metadata import site_to_str
from wzm_wzt.run_config import gmxapiConfig

ensemble_dir = '/home/jennifer/wzmwzt/tests'
ensemble_num = 0

sites = json.load(open('{}/sites.json'.format(ensemble_dir)))
deer_data = json.load(open('{}/deer_data.json'.format(ensemble_dir)))

state_json = '{}/mem_{}/state.json'.format(ensemble_dir, ensemble_num)
state = State(state_json)

gmx_config_parameters = {
    'tpr': '{}/wzmwzt.tpr'.format(ensemble_dir),
    'ensemble_dir': ensemble_dir,
    'ensemble_num': 0,
    'test_sites': []
}

if __name__ == "__main__":

    if os.path.exists(state_json):
        state.load_from_json(state_json)
        assert not state.get_all_missing_keys()

    else:
        experimental_data = ExperimentalData()
        experimental_data.set_from_dictionary(deer_data)

        general_parameters = GeneralParams()
        general_parameters.set_to_defaults()
        general_parameters.load_experimental_data(experimental_data)

        state.import_general_parameters(general_parameters)

        for site in sites:
            pair_parameters = PairParams(site)
            pair_parameters.set_to_defaults()
            pair_parameters.load_sites(sites[site])
            state.import_pair_parameters(pair_parameters)

        state.write_to_json()
    assert not state.get_all_missing_keys()

    gmxapi_config = gmxapiConfig()
    gmxapi_config.set_from_dictionary(gmx_config_parameters)
    gmxapi_config.initialize(state)

    for name in state.names:
        gmxapi_config.change_to_test_directory(name)
        gmxapi_config.build_plugins(name)
        gmxapi_config.run()