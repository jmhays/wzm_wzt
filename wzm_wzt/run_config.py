"""Class that defines the gmxapi run configuration for a single iteration of
Wzm-Wzt BRER."""

import gmx
import os, shutil
import warnings
from wzm_wzt.run_params import State
from wzm_wzt.metadata import MetaData
from wzm_wzt.directory_helper import DirectoryHelper
from wzm_wzt.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig


class gmxapiConfig(MetaData):
    def __init__(self):
        super().__init__("gmxapi_config")
        self.set_requirements(["tpr", "ensemble_dir", "ensemble_num", "test_sites"])
        self.state = None
        self.helper = None

    def load_state(self, state: State):
        self.state = state
        self.set(test_sites=[])

        # Now that we've defined a state, we can calculate the number of test sites and set up the workflow
        for site_name in self.state.pair_params:
            pair_params = self.state.pair_params[site_name]
            #if pair_params.get("on") and pair_params.get("testing"):
            if pair_params.get("testing"):
                self._metadata["test_sites"].append(site_name)

        # Check that we're not missing anything...
        assert (not self.state.get_missing_keys())
        assert (not self.get_missing_keys())

        num_test_sites = len(self.get("test_sites"))
        self.set(num_test_sites=num_test_sites)
        tprs = [self.get("tpr")] * num_test_sites
        # tprs = self.get("tpr")
        self.workflow = gmx.workflow.from_tpr(tprs, append_output=False)

    def change_to_test_directory(self):
        # Go through test_sites
        test_sites = self.get("test_sites")

        dir_helper_params = {
            'ensemble_num': self.get("ensemble_num"),
            'iteration': self.state.get("iteration"),
            'test_sites': test_sites
        }
        self.helper = DirectoryHelper(top_dir=self.get("ensemble_dir"), param_dict=dir_helper_params)
        self.helper.build_working_dir()
        self.helper.change_dir(level='num_test_sites')

    def move_cpt(self, site_name):
        current_iter = self.state.get('iteration')
        phase = self.state.get('phase', site_name=site_name)

        # If the cpt already exists, don't overwrite it
        if os.path.exists("{}/state.cpt".format(self.helper.get_dir('phase'))):
            print("Phase is {} and state.cpt already exists: not moving any files".format(phase))

        else:
            member_dir = self.helper.get_dir('ensemble_num')
            prev_iter = current_iter - 1
            prev_num_test_sites = self.helper._param_dict["num_test_sites"] + 1

            if phase in ['training', 'convergence']:
                if prev_iter > -1:
                    # Get the production cpt from previous iteration
                    gmx_cpt = '{}/{}/num_test_sites_{}/{}/production/state.cpt'.format(
                        member_dir, prev_iter, prev_num_test_sites, site_name)
                    shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))

                else:
                    pass  # Do nothing

            else:
                # Get the convergence cpt from current iteration
                gmx_cpt = '{}/{}/convergence/state.cpt'.format(member_dir, current_iter)
                shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))

    def build_plugins(self):
        all_pair_params = self.state.pair_params
        plugins_testing = []
        plugins_fixed = []

        # First add the production plugins to all members of the simulation.
        for name in all_pair_params:
            pair_parameters = all_pair_params[name]
            # If the pair is being restrained but is not part of the testing, then it should be restrained by linear potential.
            if pair_parameters.get("on") and not pair_parameters.get("testing"):
                assert pair_parameters.get("phase") == "production"
                plugin = ProductionPluginConfig()
                plugin.scan_metadata(self.state.general_params)
                plugin.scan_metadata(self.state.pair_params[name])
                assert not plugin.get_missing_keys()
                plugins_fixed.append(plugin.build_plugin())

            elif pair_parameters.get("testing"):
                if pair_parameters.get("phase") == "training":
                    plugin = TrainingPluginConfig()
                else:
                    plugin = ConvergencePluginConfig()

                plugin.scan_metadata(self.state.general_params)
                plugin.scan_metadata(self.state.pair_params[name])
                assert not plugin.get_missing_keys()
                plugins_testing.append(plugin.build_plugin())

        if plugins_fixed:
            self.workflow.add_dependency(plugins_fixed)

        self.workflow.add_dependency(plugins_testing)

    def clean_plugins(self):
        self.workflow = gmx.workflow.from_tpr([self.get("tpr")]*len(self.get("test_sites")), append_output=False)

    def run(self):
        gmx.run(work=self.workflow)

