#!/usr/bin/env python
"""
wzm_wzt.py
Testing correlation structure calculations using ABC transporter Wzm-Wzt.

Handles the primary functions
"""

import json
import os
import gmx
from wzm_wzt.run_params import State, GeneralParams, PairParams
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.metadata import site_to_str
from wzm_wzt.run_config import gmxapiConfig


class Simulation():
    def __init__(self, tpr, ensemble_dir, ensemble_num, site_filename, deer_data_filename):
        sites = json.load(open(site_filename))
        deer_data = json.load(open(deer_data_filename))

        state_json = '{}/mem_{}/state.json'.format(ensemble_dir, ensemble_num)
        state = State(state_json)

        gmx_config_parameters = {
            'tpr': tpr,
            'ensemble_dir': ensemble_dir,
            'ensemble_num': ensemble_num,
            'test_sites': []
        }

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

        assert not state.get_all_missing_keys()

        gmxapi_config = gmxapiConfig()
        gmxapi_config.set_from_dictionary(gmx_config_parameters)
        gmxapi_config.load_state(state)

        self.gmxapi = gmxapi_config
        self.gmxapi.state.write_to_json()

    def build_plugins(self, clean=False):
        if clean:
            self.gmxapi.clean_plugins()
        self.gmxapi.build_plugins()

    def run(self):
        self.gmxapi.change_to_test_directory()
        workdir_list = []
        test_sites = self.gmxapi.state.get("test_sites")
        for test_site in test_sites:
            workdir_list.append("{}/{}/{}".format(os.getcwd(), test_site,
                                                  self.gmxapi.state.get("phase", site_name=test_site)))

        context = gmx.context.ParallelArrayContext(self.gmxapi.workflow, workdir_list=workdir_list)
        with context as session:
            session.run()

