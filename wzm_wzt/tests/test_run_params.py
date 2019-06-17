"""
Unit and regression test for the RunParams class.
"""

from wzm_wzt.experimental_data import ExperimentalData
from wzm_wzt.run_params import GeneralParams, PairParams
from wzm_wzt.metadata import site_to_str
import pytest
import json
import os

def test_general_params(raw_deer_data):
    experimental_data = ExperimentalData()
    experimental_data.set_from_dictionary(raw_deer_data)

    gp = GeneralParams()
    gp.load_experimental_data(experimental_data)
    gp.set_to_defaults()

    assert not gp.get_missing_keys()

def test_pair_params(sites):
    if "sites" in sites:
        sites = sites["sites"]
    for site in sites:
        pair_param = PairParams(name=site_to_str(site))
        pair_param.load_sites(site)
        pair_param.set_to_defaults()
        assert not pair_param.get_missing_keys()

# def test_from_pair_list(raw_deer_data):
#     ed = ExperimentalData()
#     ed.set_from_dictionary(raw_deer_data)

#     pair_list = []
#     for site in ed.get("sites"):
#         pair = PairParams(site_to_str(site))
#         pair.set(**{
#             "on": True,
#             "sites": site,
#             "logging_filename": pair.name,
#             "alpha": 0,
#             "target": 3.
#         })
#         assert not pair.get_missing_keys()
#         pair_list.append(pair)
#     pairs = Pairs("pairs")
#     pairs.from_list_of_pairs(pair_list)
#     return pairs

# def test_from_experimental_data(raw_deer_data):
#     ed = ExperimentalData()
#     ed.set_from_dictionary(raw_deer_data)

#     pairs = Pairs("pairs")
#     pairs.from_experimental_data(raw_deer_data)

#     assert not pairs.get_missing_keys()

# def test_state(raw_deer_data, general_parameter_defaults):
#     state = State()
#     state.set_from_dictionary(general_parameter_defaults)

#     pairs = Pairs("pairs")
#     pairs.from_experimental_data(raw_deer_data)

#     state.import_pair_data(pairs)
#     assert not state.get_missing_keys()
#     json.dump(state.get_as_dictionary(), open("{}/state.json".format(os.getcwd()), 'w'))
