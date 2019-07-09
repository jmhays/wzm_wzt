"""Unit and regression tests for work calculations
"""

import pytest
import glob
import numpy 
from wzm_wzt.run_md import work_calculation


def test_work_calculation(data_dir):
    log_files = glob.glob("{}/convergence/*log".format(data_dir))
    _, probs = work_calculation(log_files)
    assert numpy.sum(list(probs.values())) == 1