"""Class that handles the simulation data for Wzm-Wzt simulations.

<doi!>
"""
from wzm_wzt.metadata import MetaData, site_to_str, backup_file
from wzm_wzt.experimental_data import ExperimentalData
import warnings
import json
import os
from mpi4py import MPI


class GeneralParams(MetaData):
    """Stores the parameters that are shared by all restraints in a single
    simulation.

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
            "production_time": 10000  # 10 ns
        }

        if "distribution" not in self._metadata:
            defaults["distribution"] = []
            defaults["bins"] = []

        self.set(**defaults)


class PairParams(MetaData):
    """Stores parameters that are unique to a single restraint. These include:

    Parameters
    ----------
    MetaData : class
        Inherits from MetaData class
    """

    def __init__(self, name):
        """Sets the name and the requirements for particular pair.

        Parameters
        ----------
        name : str
            The name of the particular pair being restrained. For all restraints, we will set this using the site_to_string method,
            i.e., all restraints are labeled based on their atom ids.
        """
        super().__init__(name)
        self.set_requirements(["sites", "logging_filename", "phase", "alpha", "target", "on", "testing"])

    def load_sites(self, sites: list):
        """Loads the atom ids for the restraint. This also sets the logging
        filename, which is named using the atom ids.

        Parameters
        ----------
        sites : list
            A list of the atom ids for a single restraint.

        Example
        -------
        >>> load_sites([3673, 5636])
        """
        self.set(sites=sites, logging_filename="{}.log".format(site_to_str(sites)))

    def set_to_defaults(self):
        """Set all of the pair parameters to their default values if they have
        defaults: sites, logging_filename, and name will not have default
        values."""
        self.set(phase='training', alpha=0.0, target=3.0, on=True, testing=True)


class State(MetaData):
    """Stores all parameters (general and pair-specfic) for a run.
    
    Parameters
    ----------
    MetaData : class
        Inherits from MetaData class

    """

    def __init__(self, filename):
        super().__init__("state")
        self.set_requirements(["general_parameters", "pair_parameters", "test_sites"])
        self.general_params = None
        self.pair_params = {}
        self.json = filename
        self.names = []

    def set(self, site_name=None, **kwargs):
        for key, value in kwargs.items():
            if key in self.general_params.get_requirements():
                self.general_params.set(key, value)
                self._metadata["general_parameters"][key] = value
            elif key == "test_sites":
                self._metadata[key] = value
            elif site_name:
                self.pair_params[site_name].set(key, value)
                self._metadata["pair_parameters"][site_name][key] = value
            else:
                raise KeyError(
                    "You are trying to set a pair-specific parameter {} without providing the pair name".format(key))

    def get(self, key, site_name=None):
        if key in self.general_params.get_requirements():
            answer = self.general_params.get(key)
        elif key == "test_sites":
            answer = self._metadata[key]
        elif site_name:
            answer = self.pair_params[site_name].get(key)
        else:
            raise KeyError(
                "You are trying to get a pair-specific parameter {} without providing the pair name".format(key))
        return answer

    def import_general_parameters(self, general_parameters: GeneralParams):
        incomp_warn = "You are trying to import an incomplete set of parameters: missing"
        if general_parameters.get_missing_keys():
            warnings.warn("{} {}".format(incomp_warn, general_parameters.get_missing_keys()))
        if not general_parameters.get("distribution"):
            warnings.warn("{} distribution".format(incomp_warn))
        if not general_parameters.get("bins"):
            warnings.warn("{} bins".format(incomp_warn))
        self.general_params = general_parameters
        self._metadata["general_parameters"] = general_parameters.get_as_dictionary()

    def import_pair_parameters(self, pair_parameters: PairParams):
        if pair_parameters.get_missing_keys():
            warnings.warn("You are trying to import an incomplete set of pair parameters")
        if "pair_parameters" not in self._metadata:
            self._metadata["pair_parameters"] = {}
        if pair_parameters.name in self.pair_params:
            warnings.warn("You are about to overwrite the pair {}".format(pair_parameters.name))
        self.pair_params[pair_parameters.name] = pair_parameters
        self._metadata["pair_parameters"][pair_parameters.name] = pair_parameters.get_as_dictionary()

        # Update the list of test_sites
        self._metadata["test_sites"] = []
        for site_name in self.pair_params:
            if self.pair_params[site_name].get("testing"):
                self._metadata["test_sites"].append(site_name)
            self.names.append(site_name)

    def write_to_json(self):
        if MPI.COMM_WORLD.Get_rank() == 0:
            backup_file(self.json, 'copy')
            json.dump(self.get_as_dictionary(), open(self.json, "w"))

    def new_iteration(self):
        self.set(iteration=(self._metadata["general_parameters"]["iteration"] + 1), start_time=0.)
        for site_name in self.pair_params:
            self.pair_params[site_name].set_to_defaults()

    def set_from_dictionary(self, dictionary):
        self._metadata = dictionary
        self.general_params = GeneralParams()
        self.general_params.set_from_dictionary(self._metadata["general_parameters"])
        
        self._metadata["test_sites"] = []

        for name in self._metadata["pair_parameters"]:
            self.names.append(name)
            self.pair_params[name] = PairParams(name)
            self.pair_params[name].set_from_dictionary(self._metadata["pair_parameters"][name])
            if self.pair_params[name].get("testing"):
                self._metadata["test_sites"].append(name)

    def load_from_json(self, fnm='state.json'):
        self.set_from_dictionary(json.load(open(fnm)))

    def get_all_missing_keys(self):
        missing = []
        for miss in self.get_missing_keys():
            missing.append(miss)
        for miss in self.general_params.get_missing_keys():
            missing.append(miss)
        for name in self.pair_params.keys():
            for miss in self.pair_params[name].get_missing_keys():
                missing.append(miss)
        return missing