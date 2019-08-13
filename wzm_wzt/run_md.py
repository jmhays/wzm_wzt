#!/usr/bin/env python
"""
wzm_wzt.py
Testing correlation structure calculations using ABC transporter Wzm-Wzt.

Handles the primary functions
"""

from wzm_wzt.run_params import State, GeneralParams, PairParams
from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.metadata import site_to_str
from wzm_wzt.run_config import gmxapiConfig
import logging
import json
import os, re, shutil
import gmx
import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD


def configure_logging(filename):
    root_logger = logging.getLogger()

    logger = logging.getLogger("WZM-WZT")
    logger.setLevel(logging.DEBUG)
    # Format for our loglines
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Setup console logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
    # Setup file logging as well
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)
    return logger


class Simulation():
    """Run Wzm-Wzt simulations
    """

    def __init__(self, tpr, ensemble_dir, ensemble_num, site_filename, deer_data_filename, mdrun_args={}):
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
        mdrun_args : dict
            dictionary of mdrun commandline arguments. 
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

        test_sites = gmxapi_config.state.get("test_sites")
        phases = [gmxapi_config.state.get("phase", site_name=test_site) for test_site in test_sites]
        if "training" in phases:
            # Do resampling of targets
            target = 0
            if comm.Get_rank() == 0:
                target = gmxapi_config.state.re_sample_targets()
            target = comm.bcast(target, root=0)
            for test_site in test_sites:
                gmxapi_config.state.set(target=target, site_name=test_site)
        self.gmxapi = gmxapi_config

        # print("Hello from rank {}! Test sites are: {}".format(comm.Get_rank(), self.gmxapi.state.get("test_sites")))

        self.gmxapi.state.write_to_json()
        self.logger = configure_logging("{}/{}.log".format(ensemble_dir, ensemble_num))
        self.__parallel_log("The number of sites: {}".format(self.gmxapi.get("num_test_sites")))
        self.__parallel_log("Set up simulation with state: {}".format(self.gmxapi.state.get_as_dictionary()),
                            level="debug")
        self.mdrun_args = mdrun_args
        self.__parallel_log("mdrun commandline arguments: {}".format(mdrun_args), level='debug')

    def __parallel_log(self, message, level="info"):
        if comm.Get_rank() == 0:
            if level == "info":
                self.logger.info(message)
            if level == "debug":
                self.logger.debug(message)

    def build_plugins(self, clean=False):
        """Build the gmxapi plugins.
        
        Parameters
        ----------
        clean : bool, optional
            Delete all previous plugins?, by default False
        """
        if clean:
            self.gmxapi.initialize_workflow(self.mdrun_args)
        self.gmxapi.build_plugins()

    def run(self):
        """Run the gmxapi workflow.
        """
        self.gmxapi.change_to_test_directory()

        # Set up gmxapi run
        workdir_list = []
        test_sites = self.gmxapi.state.get("test_sites")
        if test_sites:
            for test_site in test_sites:
                phase = self.gmxapi.state.get("phase", site_name=test_site)
                workdir_list.append("{}/{}/{}".format(os.getcwd(), test_site, phase))
        else:
            self.gmxapi.helper.change_dir("num_test_sites")
            workdir_list = ["{}/production".format(os.getcwd())]
        context = gmx.context.ParallelArrayContext(self.gmxapi.workflow, workdir_list=workdir_list, communicator=comm)
        with context as session:
            session.run()

        comm.Barrier()
        self.__parallel_log("The MD portion of the simulation has finished.")

    def __training_pp(self):
        test_sites = self.gmxapi.state.get("test_sites")
        assert test_sites
        for test_site in test_sites:
            # Get alpha.
            # TODO: pull this from the context.
            self.gmxapi.helper.change_dir(level="phase", test_site=test_site, phase="training")
            log_file = "{}.log".format(test_site)
            if not os.path.exists(log_file):
                raise FileNotFoundError("The log file {} was not written properly".format(log_file))
            with open(log_file, "r") as fh:
                for line in fh:
                    pass
                alpha = float(line.split()[5])
                self.gmxapi.state.set(alpha=alpha, site_name=test_site)
            self.gmxapi.state.set(phase="convergence", site_name=test_site)

    def __convergence_pp(self):
        self.gmxapi.change_to_test_directory()

        test_sites = self.gmxapi.state.get("test_sites")
        assert test_sites
        fixed_site = self.re_sample()

        for test_site in test_sites:
            if test_site == fixed_site:
                on = True
            else:
                on = False
            self.gmxapi.state.set(phase="production", testing=False, on=on, site_name=test_site)

        # Get the production start_time from the final log files
        log_files = ["{}/convergence/{}.log".format(test_site, test_site) for test_site in test_sites]
        self.gmxapi.state.set(start_time=final_time(log_files), test_sites=[])

        # Move the checkpoint to the production directory
        convergence_cpt = "{}/{}/convergence/state.cpt".format(os.getcwd(), fixed_site)
        production_cpt = "{}/production/state.cpt".format(os.getcwd())
        shutil.copy(convergence_cpt, production_cpt)
        self.__parallel_log("Writing cpt to {}".format(production_cpt))

    def __production_pp(self):
        self.gmxapi.change_to_test_directory()
        test_sites = []
        for name in self.gmxapi.state.names:
            # Set up for the next round of training.
            if not self.gmxapi.state.get("on", site_name=name):
                self.gmxapi.state.set(on=True, testing=True, phase="training", site_name=name)
                test_sites.append(name)

        # Update the iteration number if num_sites is zero
        self.gmxapi.set(num_test_sites=len(test_sites))
        if self.gmxapi.get("num_test_sites") == 0:
            self.gmxapi.state.set(iteration=self.gmxapi.state.get("iteration") + 1)
            for name in self.gmxapi.state.names:
                self.gmxapi.state.set(on=True, testing=True, phase="training", site_name=name)
                test_sites.append(name)
                
        #TODO: don't store the test sites in two places!!
        self.gmxapi.set(test_sites=test_sites)
        self.gmxapi.state.set(test_sites=test_sites)
        # Move the checkpoint to the new training and convergence directories.
        production_cpt = "{}/production/state.cpt".format(os.getcwd())
        self.gmxapi.change_to_test_directory()
        training_cpts = ["{}/{}/training/state.cpt".format(os.getcwd(), test_site) for test_site in test_sites]
        convergence_cpts = ["{}/{}/convergence/state.cpt".format(os.getcwd(), test_site) for test_site in test_sites]
        for training_cpt in training_cpts:
            shutil.copy(production_cpt, training_cpt)
            self.__parallel_log("Writing cpt {} to {}".format(production_cpt, training_cpt))
        for convergence_cpt in convergence_cpts:
            shutil.copy(production_cpt, convergence_cpt)
            self.__parallel_log("Writing cpt {} to {}".format(production_cpt, convergence_cpt))

    def post_process(self):
        phases = [self.gmxapi.state.get("phase", site_name=name) for name in self.gmxapi.state.names]
        if "training" in phases:
            self.__training_pp()
        elif "convergence" in phases:
            self.__convergence_pp()
        elif all(phase == "production" for phase in phases):
            self.__production_pp()
        else:
            raise ValueError(
                "{} is not a valid set of phases".format(phases))

        comm.Barrier()
        self.__parallel_log("Phases have been set to: {}".format(" ".join(
            [self.gmxapi.state.get("phase", site_name=site_name) for site_name in self.gmxapi.state.names])),
                            level="debug")

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
        # Find the final time
        for log_file in log_files:
            with open(log_file) as fh:
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