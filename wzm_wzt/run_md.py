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
from mpi4py import MPI
from wzm_wzt.run_params import State, GeneralParams, PairParams
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.metadata import site_to_str
from wzm_wzt.run_config import gmxapiConfig
import logging

comm = MPI.COMM_WORLD


def configure_logging(filename):
    logger = logging.getLogger("WZM-WZT")
    logger.setLevel(logging.DEBUG)
    # Format for our loglines
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Setup console logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # Setup file logging as well
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


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
        self.logger = configure_logging("{}/{}.log".format(ensemble_dir, ensemble_num))
        self.__parallel_log("The number of sites: {}".format(self.gmxapi.get("num_test_sites")))
        self.__parallel_log("Set up simulation with state: {}".format(self.gmxapi.state.get_as_dictionary()))

    def __parallel_log(self, message, level="info"):
        if comm.Get_rank() == 0:
            if level == "info":
                self.logger.info(message)

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
        # TODO: if the phase is training, do the resampling
        workdir_list = []
        test_sites = self.gmxapi.state.get("test_sites")
        print(test_sites)
        if test_sites:
            for test_site in test_sites:
                workdir_list.append("{}/{}/{}".format(os.getcwd(), test_site,
                                                      self.gmxapi.state.get("phase", site_name=test_site)))
        else:
            self.gmxapi.helper.change_dir("num_test_sites")
            workdir_list = ["{}/production".format(os.getcwd())]
        print(workdir_list)
        context = gmx.context.ParallelArrayContext(self.gmxapi.workflow, workdir_list=workdir_list)
        with context as session:
            session.run()

        comm.Barrier()
        self.__parallel_log("The MD portion of the simulation has finished.")

    def post_process(self):
        phase = self.gmxapi.state.get("phase", site_name=self.gmxapi.state.names[0])

        if phase == "training":
            test_sites = self.gmxapi.state.get("test_sites")
            assert test_sites
            for test_site in test_sites:
                # Get alpha.
                # TODO: pull this from the context.
                self.gmxapi.helper.change_dir(level="phase", test_site=test_site, phase=phase)
                log_file = "{}.log".format(test_site)
                if not os.path.exists(log_file):
                    raise FileNotFoundError("The log file {} was not written properly".format(log_file))
                with open(log_file, "r") as fh:
                    for line in fh:
                        pass
                    alpha = float(line.split()[5])
                    self.gmxapi.state.set(alpha=alpha, site_name=test_site)
                self.gmxapi.state.set(phase="convergence", site_name=test_site)

        elif phase == "convergence":
            test_sites = self.gmxapi.state.get("test_sites")
            assert test_sites
            fixed_site = self.re_sample()

            for test_site in test_sites:
                # Get alpha.
                # TODO: pull this from the context.
                self.gmxapi.helper.change_dir(level="phase", test_site=test_site, phase=phase)
                log_file = "{}.log".format(test_site)

                if not os.path.exists(log_file):
                    raise FileNotFoundError("The log file {} was not written properly".format(log_file))

                if test_site == fixed_site:
                    on = True
                else:
                    on = False
                self.gmxapi.state.set(phase="production", testing=False, on=on, site_name=test_site)
            
            self.gmxapi.change_to_test_directory()
            log_files = ["{}/convergence/{}.log".format(test_site, test_site) for test_site in test_sites]
            self.gmxapi.state.set(start_time=final_time(log_files), test_sites=[])

        elif phase == "production":
            for name in self.gmxapi.state.names:
                self.gmxapi.state.set(phase="training", site_name=name)

        else:
            raise ValueError(
                "{} is not a valid phase: must be one of 'training', 'convergence', or 'production'".format(phase))

        comm.Barrier()
        self.__parallel_log("Phases have been set to: {}".format(" ".join(
            [self.gmxapi.state.get("phase", site_name=site_name) for site_name in self.gmxapi.state.names])))

        self.gmxapi.state.write_to_json()

    def re_sample(self):
        next_site = " "
        if comm.Get_rank() == 0:
            test_sites = self.gmxapi.state.get("test_sites")
            self.gmxapi.change_to_test_directory()
            log_files = ["{}/convergence/{}.log".format(test_site, test_site) for test_site in test_sites]
            work, probs = work_calculation(log_files)
            self.__parallel_log("Work: {}".format(work))
            self.__parallel_log("Probabilities: {}".format(probs))
            next_site = np.random.choice(a=list(probs.keys()), p=list(probs.values()))
        next_site = comm.bcast(next_site, root=0)
        return next_site


def final_time(log_files: list):
    max_time = 0
    if comm.Get_rank() == 0:
        for fnm in log_files:
            # Find the final time
            with open(fnm) as fh:
                for line in fh:
                    pass
                final_time = float(line.split()[0])
                if final_time > max_time:
                    max_time = final_time
    max_time = comm.bcast(max_time, root=0)
    return max_time


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
                r, target, alpha = float(splitline[1]), float(splitline[2]), float(splitline[3])
                data.append([r, alpha])
        data = np.array(data)
        delta_x = np.sum(np.abs(data[1:, 0] - data[:-1, 0]))

        force_constant = alpha / target  # kJ/nm/mol
        # Now the actual work value:
        work[site_name] = delta_x * force_constant

    boltzmann = {}
    RT = 2.479  # kJ/mol

    for site_name in work.keys():
        boltzmann[site_name] = np.exp(-work[site_name] / RT)

    z = np.sum(list(boltzmann.values()))
    probs = {}
    for site_name in work:
        probs[site_name] = boltzmann[site_name] / z

    return work, probs