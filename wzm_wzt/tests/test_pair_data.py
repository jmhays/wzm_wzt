"""Unit and regression test for the PairData class."""

# Import package, test suite, and other packages as needed
from wzm_wzt.pair_data import PairData
import pytest
import json

def test_pair_data_import(data_dir):
    pd = PairData()
    pd.load_from_json('{}/pair_data.json'.format(data_dir))

def test_pair_data_resample(raw_pair_data):
    pd = PairData()
    pd.set_from_dictionary(raw_pair_data)
    assert(isinstance(pd.re_sample(), float))
