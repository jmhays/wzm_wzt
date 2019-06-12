"""Classe to handle 1) pair metadata 2) resampling from DEER distribution at
each new BRER iteration."""

import numpy
from wzm_wzt.metadata import MetaData
import json


class PairData(MetaData):
    """Stores Wzm-Wzt convolved distributions.

    Resamples from the single convolved distribution.
    """

    def __init__(self, name='pd'):
        super().__init__(name=name)
        self.set_requirements(['distribution', 'bins', 'sites'])

    def load_from_json(self, filename='pair_data.json'):
        """Loads DEER distribution metadata from json.

        Parameters
        ----------
        filename : str, optional
            DEER metadata: see the data directory for an example json, by default 'pair_data.json'
        """
        data = json.load(open(filename))
        self.set_from_dictionary(data)

    def re_sample(self):
        distribution = self.get('distribution')
        bins = self.get('bins')
        normalized = numpy.divide(distribution, numpy.sum(distribution))
        return numpy.random.choice(bins, p=normalized)
