"""Class that defines the gmxapi run configuration for a single iteration of
Wzm-Wzt BRER."""

import gmx
import os, shutil
import warnings
import numpy
import logging
from wzm_wzt.run_params import State
from wzm_wzt.metadata import MetaData
from wzm_wzt.directory_helper import DirectoryHelper
from wzm_wzt.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig
from mpi4py import MPI

comm = MPI.COMM_WORLD


class gmxapiConfig(MetaData):
    def __init__(self):
        super().__init__("gmxapi_config")
        self.set_requirements(["tpr", "ensemble_dir", "ensemble_num", "test_sites", "num_test_sites"])
        self.state = None
        self.helper = None
        self.workflow = None

    def load_state(self, state: State):
        self.state = state
        test_sites = []
        sites_on = 0  # for counting the number of sites that are turned on

        # Now that we've defined a state, we can calculate the number of test sites and set up the workflow
        for site_name in self.state.pair_params:
            pair_params = self.state.pair_params[site_name]
            if pair_params.get("on"):
                sites_on += 1
            if pair_params.get("testing"):
                test_sites.append(site_name)

        self._metadata["test_sites"] = test_sites
        self.state.set(test_sites=test_sites)

        phase = pair_params.get("phase")

        # Check that we're not missing anything...
        assert (not self.state.get_missing_keys())

        test_num_test_sites = len(self.state.get("test_sites"))
        # Now we need to correct in case the number of test sites is zero (meaning we're in production)
        if test_num_test_sites == 0:
            assert phase == "production"
            num_test_sites = len(self.state.pair_params) - sites_on + 1
        else:
            num_test_sites = test_num_test_sites

        self.set(num_test_sites=num_test_sites)

        assert (not self.get_missing_keys())
        # Do resampling of targets if training phase

    def change_to_test_directory(self):
        # Go through test_sites
        test_sites = self.get("test_sites")
        dir_helper_params = {
            'ensemble_num': self.get("ensemble_num"),
            'iteration': self.state.get("iteration"),
            'test_sites': test_sites,
            'num_test_sites': self.get("num_test_sites")
        }

        self.helper = DirectoryHelper(top_dir=self.get("ensemble_dir"), param_dict=dir_helper_params)
        self.helper.build_working_dir()
        self.helper.change_dir(level='num_test_sites')

    def build_plugins(self, mdrun_args={}):
        if not self.workflow:
            warnings.warn("You have not initialized a workflow. Automatically setting one up for you...")
            self.initialize_workflow(mdrun_args=mdrun_args)

        all_pair_params = self.state.pair_params
        names = sorted(list(all_pair_params.keys()))

        plugins_testing = {}
        plugins_fixed = {}
        phases = []

        # Have to check whether any phases are in training or convergence.
        # If so, we have to set the production time really high just in case
        # there are any linear restraints.
        production_time = None
        for name in names:
            phase = all_pair_params[name].get("phase")
            if phase == 'training' or phase == 'convergence':
                production_time = 10E8  # ten microseconds
                break

        # First add the production plugins to all members of the simulation.
        for name in names:
            pair_parameters = all_pair_params[name]
            # If the pair is being restrained but is not part of the testing, then it should be restrained by linear potential.
            if pair_parameters.get("on"):
                if not pair_parameters.get("testing"):
                    assert pair_parameters.get("phase") == "production"
                    phases.append("production")

                    plugin = ProductionPluginConfig()
                    plugin.scan_metadata(self.state.general_params)
                    plugin.scan_metadata(self.state.pair_params[name])

                    if production_time is not None:
                        logging.getLogger("WZM-WZT").info(
                            "Some of your plugins are in the training phase. That means I have to set the variable \"production_time\" arbitrarily high. Setting to {} ps"
                            .format(production_time))
                        plugin.set_parameters(production_time=production_time)

                    assert not plugin.get_missing_keys()

                    plugins_fixed[name] = plugin.build_plugin()

                else:
                    if pair_parameters.get("phase") == "training":
                        plugin = TrainingPluginConfig()
                        phases.append("training")
                    else:
                        plugin = ConvergencePluginConfig()
                        phases.append("convergence")

                    plugin.scan_metadata(self.state.general_params)
                    plugin.scan_metadata(self.state.pair_params[name])
                    assert not plugin.get_missing_keys()

                    plugins_testing[name] = plugin.build_plugin()

        if plugins_fixed:
            for fixed_plugin in plugins_fixed.values():
                if "training" in phases or "convergence" in phases:
                    self.workflow.add_dependency([fixed_plugin] * self.get("num_test_sites"))
                else:
                    self.workflow.add_dependency(fixed_plugin)
        if plugins_testing:
            assert sorted(list(plugins_testing.keys())) == self.get("test_sites")
            plugins_testing_list = []
            for test_site in self.get("test_sites"):
                plugins_testing_list.append(plugins_testing[test_site])
            self.workflow.add_dependency(plugins_testing_list)

    def initialize_workflow(self, mdrun_args={}):
        phases = [self.state.get("phase", site_name=name) for name in self.state.names]

        args_for_from_tpr = {"append_output": False}
        tprs = None
        if comm.Get_rank() == 0:
            for key, value in mdrun_args.items():
                args_for_from_tpr[key] = value

            if "training" in phases or "convergence" in phases:
                tprs = [self.get("tpr")] * self.get("num_test_sites")

            else:
                end_time = self.state.get('production_time') + self.state.get('start_time')
                args_for_from_tpr["end_time"] = end_time
                tprs = self.get("tpr")

        args_for_from_tpr = comm.bcast(args_for_from_tpr, root=0)
        tprs = comm.bcast(tprs, root=0)
        logging.getLogger("WZM-WZT").debug(
            "Rank {} will pass tprs: {} and arguments: {} to gmx.workflow.from_tpr".format(
                comm.Get_rank(), tprs, args_for_from_tpr))
        self.workflow = gmx.workflow.from_tpr(tprs, **args_for_from_tpr)

    def run(self):
        gmx.run(work=self.workflow)
