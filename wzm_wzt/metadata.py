"""
Abstract class for handling all BRER metadata. State and PairData classes inherit from this class.
"""
from abc import ABC
import json


def site_to_str(site):
    return "_".join([str(x) for x in site])

class MetaData(ABC):

    def __init__(self, name):
        """Construct metadata object and give it a name

        Parameters
        ----------
        name :
            All metadata classes should have names that associate them with a particular pair.

        Returns
        -------

        """
        self.__name = name
        self.__required_parameters = []
        self._metadata = {}

    @property
    def name(self):
        """ """
        return self.__name

    @name.getter
    def name(self):
        """ """
        return self.__name
    
    @name.setter
    def name(self, name):
        self.__name = name

    def set_requirements(self, list_of_requirements: list):
        """

        Parameters
        ----------
        list_of_requirements: list :


        Returns
        -------

        """
        self.__required_parameters = list_of_requirements

    def get_requirements(self):
        """ """
        return self.__required_parameters

    def set(self, key=None, value=None, **kwargs):
        """

        Parameters
        ----------
        key :

        value :


        Returns
        -------

        """

        if key and value:
            self._metadata[key] = value

        else:
            for key in kwargs:
                if key in self.__required_parameters:
                    self._metadata[key] = kwargs[key]

    def get(self, key):
        """

        Parameters
        ----------
        key :


        Returns
        -------

        """
        return self._metadata[key]

    def set_from_dictionary(self, data):
        """

        Parameters
        ----------
        data :


        Returns
        -------

        """
        self._metadata = data

    def get_as_dictionary(self):
        """ """
        return self._metadata

    def get_missing_keys(self):
        """ """
        missing = []
        for required in self.__required_parameters:
            if required not in self._metadata.keys():
                missing.append(required)
        return missing