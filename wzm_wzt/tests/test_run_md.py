import pytest

from wzm_wzt.run_md import Simulation, final_time
from wzm_wzt.metadata import site_to_str
import os
import logging
import shutil
import glob

try:
    from mpi4py import MPI
    withmpi_only = \
        pytest.mark.skipif(not MPI.Is_initialized() or MPI.COMM_WORLD.Get_size() < 6,
                           reason="Test requires at least 6 MPI ranks, but MPI is not initialized or too small.")
except ImportError:
    withmpi_only = pytest.mark.skip(reason="Test requires at least 6 MPI ranks, but mpi4py is not available.")


@withmpi_only
def test_simulation(simulation):
    """Test that a simulation runs, provided you have enough mpi threads.
    
    Parameters
    ----------
    simulation : Simulation
        Simulation object defined in conftest.py
    """
    simulation.gmxapi.state.set(**{
        "A": 5,
        "tau": 0.1,
        "tolerance": 100,
        "num_samples": 2,
        "sample_period": 0.1,
        "production_time": 0.2
    })
    simulation.build_plugins(clean=True)
    simulation.run()


def test_resampling(tmpdir, data_dir, simulation):
    # Make a directory structure that can support the resampling operation
    simulation.gmxapi.change_to_test_directory()

    # Move and rename some existing log files to mimic what might be found in a real run
    logs_data_dir = glob.glob("{}/convergence/*.log".format(data_dir))

    counter = 0
    for site in simulation.gmxapi.get("test_sites"):
        name = site
        shutil.copy(logs_data_dir[counter], "{}/convergence/{}.log".format(name, name))
        if counter == len(logs_data_dir) - 1:
            counter = 0
        else:
            counter += 1

    # Finally, do the actual resampling!
    simulation.re_sample()

def test_final_time(tmpdir, data_dir, simulation):
    # Make a directory structure that can support the resampling operation
    simulation.gmxapi.change_to_test_directory()

    # Move and rename some existing log files to mimic what might be found in a real run
    log = "{}/convergence/052_210.log".format(data_dir)

    time = final_time(log)
    assert time == 259.356
