import pytest

from wzm_wzt.run_md import Simulation
import os
import logging

try:
    from mpi4py import MPI
    withmpi_only = \
        pytest.mark.skipif(not MPI.Is_initialized() or MPI.COMM_WORLD.Get_size() < 6,
                           reason="Test requires at least 6 MPI ranks, but MPI is not initialized or too small.")
except ImportError:
    withmpi_only = pytest.mark.skip(reason="Test requires at least 6 MPI ranks, but mpi4py is not available.")


@withmpi_only
def test_simulation(tmpdir, data_dir):

    ensemble_num = 0
    ensemble_dir = "{}".format(tmpdir)
    os.makedirs("{}/mem_{}".format(ensemble_dir, ensemble_num), exist_ok=True)

    site_filename = "{}/sites.json".format(data_dir)
    deer_data_filename = "{}/deer_data.json".format(data_dir)
    tpr = "{}/wzmwzt.tpr".format(data_dir)

    statefile = "{}/mem_{}/state.json".format(ensemble_dir, ensemble_num)
    if os.path.exists(statefile):
        os.remove(statefile)
    sim = Simulation(tpr, ensemble_dir, ensemble_num, site_filename, deer_data_filename)
    sim.gmxapi.state.set(**{
        "A": 5,
        "tau": 0.1,
        "tolerance": 100,
        "num_samples": 2,
        "sample_period": 0.1,
        "production_time": 0.2
    })
    sim.build_plugins(clean=True)
    sim.run()