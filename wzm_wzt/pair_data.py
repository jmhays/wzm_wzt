"""
Classes to handle
1) pair metadata
2) resampling from DEER distributions at each new BRER iteration.
"""

import numpy
from wzm_wzt.metadata import MetaData
import json


class PairData(MetaData):
    """ """

    def __init__(self, name='pd'):
        super().__init__(name=name)
        self.set_requirements(['distribution', 'bins', 'sites'])

    def load_from_json(self, filename='pair_data.json'):
        data = json.load(open(filename))
        self.set_from_dictionary(data)

    def re_sample(self):
        distribution = self.get('distribution')
        bins = self.get('bins')
        normalized = numpy.divide(distribution, numpy.sum(distribution))
        return numpy.random.choice(bins, p=normalized)
