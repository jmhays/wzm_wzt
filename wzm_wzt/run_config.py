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

    # def move_cpt(self, site_name):
    #     current_iter = self.state.get('iteration')
    #     phase = self.state.get('phase', site_name=site_name)

    #     # If the cpt already exists, don't overwrite it
    #     if os.path.exists("{}/state.cpt".format(self.helper.get_dir('phase'))):
    #         print("Phase is {} and state.cpt already exists: not moving any files".format(phase))

    #     else:
    #         member_dir = self.helper.get_dir('ensemble_num')
    #         prev_iter = current_iter - 1
    #         prev_num_test_sites = self.helper._param_dict["num_test_sites"] + 1

    #         if phase in ['training', 'convergence']:
    #             if prev_iter > -1:
    #                 # Get the production cpt from previous iteration
    #                 gmx_cpt = '{}/{}/num_test_sites_{}/{}/production/state.cpt'.format(
    #                     member_dir, prev_iter, prev_num_test_sites, site_name)
    #                 shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))

    #             else:
    #                 pass  # Do nothing

    #         else:
    #             # Get the convergence cpt from current iteration
    #             gmx_cpt = '{}/{}/convergence/state.cpt'.format(member_dir, current_iter)
    #             shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))

    def build_plugins(self):
        if not self.workflow:
            warnings.warn("You have not initialized a workflow. Automatically setting one up for you...")
            self.initialize_workflow()

        all_pair_params = self.state.pair_params
        plugins_testing = []
        plugins_fixed = []
        test_sites_ordered = []
        phases = []

        # First add the production plugins to all members of the simulation.
        for name in all_pair_params:
            pair_parameters = all_pair_params[name]
            # If the pair is being restrained but is not part of the testing, then it should be restrained by linear potential.
            if pair_parameters.get("on"):
                if not pair_parameters.get("testing"):
                    assert pair_parameters.get("phase") == "production"
                    phases.append("production")
                    plugin = ProductionPluginConfig()
                    plugin.scan_metadata(self.state.general_params)
                    plugin.scan_metadata(self.state.pair_params[name])
                    assert not plugin.get_missing_keys()
                    plugins_fixed.append(plugin.build_plugin())
                else:
                    test_sites_ordered.append(name)
                    if pair_parameters.get("phase") == "training":
                        plugin = TrainingPluginConfig()
                        phases.append("training")
                    else:
                        plugin = ConvergencePluginConfig()
                        phases.append("convergence")

                    plugin.scan_metadata(self.state.general_params)
                    plugin.scan_metadata(self.state.pair_params[name])
                    assert not plugin.get_missing_keys()
                    plugins_testing.append(plugin.build_plugin())

        self.state.set(test_sites=test_sites_ordered)

        if plugins_fixed:
            for fixed_plugin in plugins_fixed:
                if "training" in phases or "convergence" in phases:
                    self.workflow.add_dependency([fixed_plugin] * self.get("num_test_sites"))
                else:
                    self.workflow.add_dependency(fixed_plugin)
        if plugins_testing:
            self.workflow.add_dependency(plugins_testing)

    def initialize_workflow(self):
        phases = [self.state.get("phase", site_name=name) for name in self.state.names]
        if "training" in phases or "convergence" in phases:
            self.workflow = gmx.workflow.from_tpr([self.get("tpr")] * self.get("num_test_sites"), append_output=False)
        else:
            end_time = self.state.get('production_time') + self.state.get('start_time')
            self.workflow = gmx.workflow.from_tpr(self.get("tpr"), end_time=end_time, append_output=False)

    def run(self):
        gmx.run(work=self.workflow)
