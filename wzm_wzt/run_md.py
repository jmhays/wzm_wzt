#!/usr/bin/env python
"""
wzm_wzt.py
Testing correlation structure calculations using ABC transporter Wzm-Wzt.

Handles the primary functions
"""

import json
import os, re
import gmx
import numpy as np
from wzm_wzt.run_params import State, GeneralParams, PairParams
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.metadata import site_to_str
from wzm_wzt.run_config import gmxapiConfig


class Simulation():
    """Run Wzm-Wzt simulations
    """

    def __init__(self, tpr, ensemble_dir, ensemble_num, site_filename, deer_data_filename):
        """Initialize the run.
        
        Parameters
        ----------
        tpr : str
            path to tpr
        ensemble_dir : str
            path to top-level ensemble directory
        ensemble_num : int
            ensemble member you want to run
        site_filename : str
            path to json file containing atom ids for restraints
        deer_data_filename : str
            path to json file containing DEER data for restraints.
        """
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
        """Build the gmxapi plugins.
        
        Parameters
        ----------
        clean : bool, optional
            Delete all previous plugins?, by default False
        """
        if clean:
            self.gmxapi.clean_plugins()
        self.gmxapi.build_plugins()

    def run(self):
        """Run the gmxapi workflow.
        """
        self.gmxapi.change_to_test_directory()
        workdir_list = []
        test_sites = self.gmxapi.state.get("test_sites")
        for test_site in test_sites:
            workdir_list.append("{}/{}/{}".format(os.getcwd(), test_site,
                                                  self.gmxapi.state.get("phase", site_name=test_site)))

        context = gmx.context.ParallelArrayContext(self.gmxapi.workflow, workdir_list=workdir_list)
        with context as session:
            session.run()

    def re_sample(self):
        test_sites = self.gmxapi.state.get("test_sites")
        self.gmxapi.change_to_test_directory()
        log_files = ["{}/convergence/{}.log".format(test_site, test_site) for test_site in test_sites]
        _, probs = work_calculation(log_files)
        next_site = np.random.choice(a=list(probs.keys()), p=list(probs.values()))
        return next_site

def work_calculation(log_files: list):
    work = {}
    for fnm in log_files:
        site_name = re.search("[0-9]+_[0-9]+", fnm).group(0)
        data = []

        # Calculate the total path distance
        with open(fnm) as log_file:
            newline = log_file.readline()  # read the header
            while 1:
                newline = log_file.readline()
                if not newline:
                    break
                splitline = newline.split()
                r, alpha = float(splitline[1]), float(splitline[3])
                data.append([r, alpha])
        data = np.array(data)
        delta_x = np.sum(np.abs(data[1:, 0] - data[:-1, 0]))

        # Now the actual work value:
        work[site_name] = delta_x * alpha

    z = np.sum(list(work.values()))
    probs = {}
    for site_name in work:
        probs[site_name] = work[site_name] / z

    return work, probs