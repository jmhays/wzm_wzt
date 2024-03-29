"""Unit and regression test for the DirectoryHelper class."""

from wzm_wzt.directory_helper import DirectoryHelper
import os
import pytest


def test_directory(tmpdir):
    """ Checks that directory creation for BRER runs is functional.
    Parameters
    ----------
    tmpdir : str
        temporary pytest directory
    """
    my_home = os.path.abspath(os.getcwd())
    top_dir = tmpdir.mkdir("top_directory")
    param_dict = {
        'ensemble_num': 1,
        #'iteration': 0,
        'test_sites': [[3673, 5636], [3673, 10088], [3673, 12035], [5636, 10088], [5636, 12035], [10088, 12035]]
    }
    with pytest.raises(KeyError):
        assert DirectoryHelper(top_dir, param_dict)

    param_dict['iteration'] = 0
    dir_helper = DirectoryHelper(top_dir, param_dict)
    dir_helper.build_working_dir()

    test_site = '3673_5636'
    phase = 'training'
    # Test all the different levels
    dir_helper.change_dir('phase', test_site=test_site, phase=phase)
    assert (os.getcwd() == '{}/mem_{}/{}/num_test_sites_{}/{}/{}'.format(top_dir, 1, 0, 6, '3673_5636', 'training'))
    dir_helper.change_dir('top')
    assert (os.getcwd() == top_dir)
    dir_helper.change_dir('ensemble_num')
    assert (os.getcwd() == '{}/mem_{}'.format(top_dir, 1))
    dir_helper.change_dir('iteration')
    assert (os.getcwd() == '{}/mem_{}/{}'.format(top_dir, 1, 0))
    dir_helper.change_dir('num_test_sites')
    assert (os.getcwd() == '{}/mem_{}/{}/num_test_sites_6'.format(top_dir, 1, 0))
    dir_helper.change_dir('test_site', test_site=test_site)
    assert (os.getcwd() == '{}/mem_{}/{}/num_test_sites_{}/{}'.format(top_dir, 1, 0, 6, '3673_5636'))

    with pytest.raises(ValueError):
        assert dir_helper.change_dir("bad_dir")

    os.chdir(my_home)
