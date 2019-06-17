"""Class that defines the gmxapi run configuration for a single iteration of
Wzm-Wzt BRER."""

import gmx
# from wzm_wzt.run_params import RunParams
from wzm_wzt.metadata import MetaData
#from wzm_wzt.directory_helper import DirectoryHelper
#from wzm_wzt.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig


class gmxapiConfig(MetaData):
    def __init__(self):
        self.name = "gmxapi_config"
        self.set_requirements(["tpr", "ensemble_dir", "ensemble_num", "pairs_json"])

    def get_workflow(self):
        assert (not self.get_missing_keys())
        return gmx.workflow.from_tpr(self.get("tpr"), append_output=False)
