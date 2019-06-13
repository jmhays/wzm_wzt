"""
Unit and regression test for the DirectoryHelper class.
"""

from wzm_wzt.directory_helper import DirectoryHelper
import os
import pytest


def test_directory(tmpdir):
    """
    Checks that directory creation for BRER runs is functional.
    :param tmpdir: temporary pytest directory
    """
    my_home = os.path.abspath(os.getcwd())
    top_dir = tmpdir.mkdir("top_directory")
    param_dict = {
        'ensemble_num': 1,
        'iteration': 0,
        'num_test_sites': 6,
        'test_site': '3673_5636',
        'phase': 'training'
    }

    dir_helper = DirectoryHelper(top_dir, param_dict)
    dir_helper.build_working_dir()
    dir_helper.change_dir('phase')
    assert (os.getcwd() == '{}/mem_{}/{}/num_test_sites_{}/{}/{}'.format(top_dir, 1, 0, 6, '3673_5636', 'training'))

    os.chdir(my_home)
