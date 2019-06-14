"""Unit and regression test for the run configuration classes."""

import pytest
from wzm_wzt.run_config import GmxapiConfig

def test_gmxapi_config(data_dir, tmpdir):
    gmx_config_defaults = {
        'tpr': '{}/wzmwzt.tpr'.format(data_dir),
        'ensemble_dir': tmpdir,
        'ensemble_num': 0,
        'pairs_json': '{}/pair_data.json'.format(data_dir)
    }
    gmx_config = GmxapiConfig()
    gmx_config.set_from_dictionary(gmx_config_defaults)
    assert not gmx_config.get_missing_keys()

    gmx_config.get_workflow()
