"""Unit and regression test for the ExperimentalData class."""

# Import package, test suite, and other packages as needed
from wzm_wzt.experimental_data import ExperimentalData
import pytest
import json

def test_experimental_data_import(data_dir):
    ed = ExperimentalData()
    ed.load_from_json("{}/deer_data.json".format(data_dir))
    assert not ed.get_missing_keys()
    assert ed.get("distribution")

def test_experimental_data_resample(raw_deer_data):
    ed = ExperimentalData()
    ed.set_from_dictionary(raw_deer_data)
    assert(isinstance(ed.re_sample(), float))
