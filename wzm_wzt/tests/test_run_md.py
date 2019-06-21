import pytest

from wzm_wzt.run_md import Simulation
import os

def test_simulation(tmpdir, data_dir):
    ensemble_num = 0
    ensemble_dir = "{}".format(tmpdir)
    os.makedirs("{}/mem_{}".format(ensemble_dir, ensemble_num))

    site_filename = "{}/sites.json".format(data_dir)
    deer_data_filename = "{}/deer_data.json".format(data_dir)
    tpr = "{}/wzmwzt.tpr".format(data_dir)

    sim = Simulation(tpr, ensemble_dir, ensemble_num, site_filename, deer_data_filename)
    sim.build_plugins(clean=True)
    print(sim.gmxapi.workflow.workspec)
    #sim.run()