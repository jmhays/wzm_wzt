"""
Class that handles the simulation data for Wzm-Wzt simulations
<doi!>
"""
from wzm_wzt.metadata import MetaData, site_to_str
from wzm_wzt.experimental_data import ExperimentalData
import json


class GeneralParams(MetaData):
    """Stores the parameters that are shared by all restraints in a single simulation.
    These include some of the "Voth" parameters: tau, A, tolerance
    """

    def __init__(self):
        super().__init__("general")
        self.set_requirements([
            "ensemble_num", "iteration", "start_time", "A", "tau", "tolerance", "num_samples", "sample_period",
            "production_time", "distribution", "bins"
        ])

    def load_experimental_data(self, experimental_data: ExperimentalData):
        assert not experimental_data.get_missing_keys()
        self.set(distribution=experimental_data.get('distribution'), bins=experimental_data.get('bins'))

    def set_to_defaults(self):
        defaults = {
            "ensemble_num": 1,
            "iteration": 0,
            "start_time": 0,
            "A": 50,
            "tau": 50,
            "tolerance": 0.25,
            "num_samples": 50,
            "sample_period": 100,
            "production_time": 10000,  # 10 ns
            "distribution": [],
            "bins": []
        }
        self.set(**defaults)


class PairParams(MetaData):
    def __init__(self, name):
        super().__init__(name)
        self.set_requirements(["sites", "logging_filename", "phase", "alpha", "target", "on", "testing"])
    def load_sites(self, sites: list):
        self.set(sites=sites, logging_filename="{}.log".format(site_to_str(sites)))
    def set_to_defaults(self):
        self.set(phase='training', alpha=0.0, target=3.0, on=False, testing=True)


# class Pairs(MetaData):
#     def __init__(self, name):
#         super().__init__(name)
#         self.name = name
#         self.pair_params = []

#     def from_list_of_pairs(self, pairs: list):
#         """Takes a list of Pairs and loads the data into the multi-pair class Pairs.

#         Parameters
#         ----------
#         pairs : list
#             a list of Pair objects.
#         """
#         for pair in pairs:
#             self._metadata[pair.name] = pair.get_as_dictionary()

#     def from_experimental_data(self, ed: ExperimentalData):
#         for site in ed.get("sites"):
#             site_name = site_to_str(site)
#             pair = PairParams(site_name)
#             pair.set("sites", site)
#             pair.set("logging_filename", "{}.log".format(site_name))
#             self._metadata[site_name] = pair.get_as_dictionary()

# class State(MetaData):
#     def __init__(self):
#         super().__init__("state")
#         self.set_requirements(["general_parameters", "pair_parameters"])
#         self.general_params = None
#         self.pair_params = None

#     def import_general_parameters(self, general_parameters: GeneralParams):
#         if general_parameters.get_missing_keys():
#             raise Warning("You are trying to import an incomplete set of general parameters")
#         self.general_parameters = general_parameters
#         self._metadata["general_parameters"] = general_parameters.get_as_dictionary()

#     def import_pair_parameters(self, pairs: Pairs):
#         self._metadata["sites"] = pairs.get_as_dictionary()
