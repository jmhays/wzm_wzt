"""Class that defines the gmxapi run configuration for a single iteration of
Wzm-Wzt BRER."""

import gmx
from wzm_wzt.run_params import RunParams
from wzm_wzt.metadata import MetaData
from wzm_wzt.directory_helper import DirectoryHelper
from wzm_wzt.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig


class GmxapiConfig(MetaData):
    def __init__(self):
        self.name = 'gmxapi_config'
        self.set_requirements(['tpr', 'ensemble_dir', 'ensemble_num', 'pairs_json'])

    # def get_workflow(self):
    #     assert (not self.get_missing_keys())
    #     return gmx.workflow.from_tpr(self.get('tpr'), append_output=False)


# class RunTestSites:
#     def __init__(self, test_sites, rp: RunParams, gmx_config: GmxapiConfig):
#         self.test_sites = test_sites
#         num_sites = len(test_sites)

#         self.rp = rp
#         self.gmx_config = gmx_config

#         for site in self.test_sites:
#             param_dict={
#                 'ensemble_num': self.gmx_config.get('ensemble_num'),
#                 'iteration': self.rp.get('iteration'),
#                 'phase': self.rp.get('phase'),
#                 'num_sites': num_sites,
#                 'test_site': '_'.join([str(x) for x in site])
#                 }
#             directory_helper = DirectoryHelper(top_dir=self.gmx_config['ensemble_dir'], param_dict=param_dict)
#             directory_helper.build_working_dir()
