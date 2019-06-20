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
    sim.set_current_test_site('3673_10088')
    sim.build_plugins()
    print(sim.gmxapi.workflow.workspec)
    sim.set_current_test_site('3673_12035')
    with pytest.warns(Warning):
        sim.build_plugins(clean=True)
    print(sim.gmxapi.workflow.workspec)