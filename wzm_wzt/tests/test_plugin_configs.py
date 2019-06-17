"""Unit and regression test for the PluginConfigs classes."""

# Import package, test suite, and other packages as needed
import pytest
from wzm_wzt.pair_data import PairData
from wzm_wzt.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig
import json
import os


def test_build_plugins(general_parameter_defaults, raw_pair_data):
    """Build all three test plugins and check that they have all the required
    data to run.

    Parameters
    ----------
    general_parameter_defaults : dict
        A set of general parameters (as defined by the GeneralParam class). Provided in conftest.py
    raw_pair_data : dict
        A set of pair-specific parameters. Provided in conftest.py
    """
    tpc = TrainingPluginConfig()
    cpc = ConvergencePluginConfig()
    ppc = ProductionPluginConfig()

    # Pick one site for testing plugins
    sites = raw_pair_data['sites']
    sites = sites[0]
    site_name = '_'.join([str(x) for x in sites])

    pair_param_dict = {'logging_filename': '{}.log'.format(site_name), 'target': 3.0, 'sites': sites, 'alpha': 100.}

    tpc.scan_dictionary(general_parameter_defaults)
    pair_param_dict['phase'] = 'training'
    tpc.scan_dictionary(pair_param_dict)
    assert not tpc.get_missing_keys()

    cpc.scan_dictionary(general_parameter_defaults)
    pair_param_dict['phase'] = 'convergence'
    cpc.scan_dictionary(pair_param_dict)
    assert not cpc.get_missing_keys()

    ppc.scan_dictionary(general_parameter_defaults)
    pair_param_dict['phase'] = 'production'
    ppc.scan_dictionary(pair_param_dict)
    assert not ppc.get_missing_keys()

    tpc.build_plugin()
    cpc.build_plugin()
    ppc.build_plugin()