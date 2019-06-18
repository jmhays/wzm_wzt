"""Class that defines the gmxapi run configuration for a single iteration of
Wzm-Wzt BRER."""

import gmx
from wzm_wzt.run_params import State
from wzm_wzt.metadata import MetaData
from wzm_wzt.directory_helper import DirectoryHelper
from wzm_wzt.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig


class gmxapiConfig(MetaData):
    def __init__(self):
        self.name = "gmxapi_config"
        self.set_requirements(["tpr", "ensemble_dir", "ensemble_num", "test_sites"])
        self.workflow = None
        self.state = None

    def initialize(self, state: State):
        self.state = state
        self.set(test_sites = [])

        # Now that we've defined a state, we can calculate the number of test sites and set up the workflow
        for site_name in self.state.pair_params:
            pair_params = self.state.pair_params[site_name]
            #if pair_params.get("on") and pair_params.get("testing"):
            if pair_params.get("testing"):
                self._metadata["test_sites"].append(site_name)

        # Check that we're not missing anything...
        assert (not self.state.get_missing_keys())
        assert (not self.get_missing_keys())

        # tprs = [self.get("tpr")]*num_test_sites
        tprs = self.get("tpr")
        self.workflow = gmx.workflow.from_tpr(tprs, append_output=False)

    def change_to_test_directory(self, site_name):
        # Go through test_sites
        test_sites = self.get("test_sites")
        num_test_sites = len(test_sites)

        dir_helper_params = {
            'ensemble_num': self.get("ensemble_num"),
            'iteration': self.state.get("iteration"),
            'num_test_sites': num_test_sites,
            'test_site': site_name,
            'phase': self.state.get("phase", site_name)
        }
        directory_helper = DirectoryHelper(top_dir=self.get("ensemble_dir"), param_dict=dir_helper_params)
        directory_helper.build_working_dir()
        directory_helper.change_dir(level="phase")

    def build_plugins(self, site_name):
        all_pair_params = self.state.pair_params

        for name in all_pair_params:
            pair_parameters = all_pair_params[name]
            # Are we restraining this pair?
            if pair_parameters.get("on") and not pair_parameters.get("testing"):
                plugin = ProductionPluginConfig()
            elif name == site_name and pair_parameters.get("testing"):
                if pair_parameters.get("phase") == "training":
                    plugin = TrainingPluginConfig()
                else:
                    plugin = ConvergencePluginConfig()
                self.state.pair_params[name].set(on=True)
            else:
                self.state.pair_params[name].set(on=False)

            if pair_parameters.get("on"):
                #print(self.state.pair_params[name].get("alpha"))
                #print(self.state.pair_params[name].get_as_dictionary())
                #print(plugin.get_as_dictionary())
                plugin.scan_metadata(self.state.general_params)
                #print(plugin.get_as_dictionary())
                #print(plugin.get_as_dictionary())
                #print(plugin.get_missing_keys())
                #self.workflow.add_dependency(plugin.build_plugin())

    def run(self):
        gmx.run(self.workflow)

    # TODO: once gmxapi enables assignment of an array of plugins to an array of simulations, we can use this code to run test sites in parallel
    # def build_plugins(self):
    #     """

    #     Parameters
    #     ----------
    #     sites_settings : dict
    #         [description]
    #     """

    #     if not self.state:
    #         raise ValueError("A State object has not yet been defined.")

    #     all_pair_params = self.state.pair_params

    #     for name in all_pair_params:
    #         pair_parameters = all_pair_params[name]
    #         # Are we restraining this pair?
    #         if pair_parameters.get("on"):
    #             # Are we testing the pair or just holding it fixed?
    #             if not pair_parameters.get("testing"):
    #                 # If holding fixed, build a production plugin
    #                 plugin = ProductionPluginConfig()
    #             else:
    #                 if pair_parameters.get("phase") == "training":
    #                     plugin = TrainingPluginConfig()
    #                 else:
    #                     plugin = ConvergencePluginConfig()

    #             plugin.scan_metadata(pair_parameters)
    #             plugin.scan_metadata(self.state.general_parameters)
    #             assert not plugin.get_missing_keys()
    #             self.workflow.add_dependency(plugin.build_plugin())
