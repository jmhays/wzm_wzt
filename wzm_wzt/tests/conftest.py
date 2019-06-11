import pytest
import os


@pytest.fixture()
def data_dir():
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return '{}/data'.format(parent_dir)


@pytest.fixture()
def raw_pair_data():
    """
    Three DEER distributions for testing purposes.
    :return:
    """
    return {
        "sites": [[3673, 5636], [3673, 10088], [3673, 12035], [5636, 10088], [5636, 12035], [10088, 12035]],
        "name":
        "228_349",
        "sigma":
        0.1,
        "distribution": [
            2.800984867171206e-51, 5.557660374406905e-45, 4.0583192201003636e-39, 1.090846713663674e-33,
            1.0796526915922044e-28, 3.936616284840753e-24, 5.2919517259460373e-20, 2.625943096630879e-16,
            4.81895962943138e-13, 3.280392420400716e-10, 8.323596864528224e-08, 7.935786432439835e-06,
            0.00028820125087823044, 0.004084929453744159, 0.02365050161313983, 0.061157625279825156,
            0.08387780669427429, 0.08006406865329556, 0.07020692418748725, 0.06843742353582569, 0.08261454922303547,
            0.11643133596816045, 0.1639455666777189, 0.2081676103619389, 0.22982274103142228, 0.224280696977606,
            0.20316940797973848, 0.18346775221406386, 0.17911207322915743, 0.19016757905853232, 0.2052453644885256,
            0.21676710602642388, 0.22309630743994388, 0.2210991601220343, 0.2128670419292219, 0.21238408380672208,
            0.2289695012914307, 0.2533361357620096, 0.268596589701337, 0.265946803678829, 0.25179531520576154,
            0.24430170576958943, 0.2580226694344741, 0.2930422512107887, 0.33692656509211005, 0.3709809047336551,
            0.38702892705083697, 0.3850249366883848, 0.3663667261353682, 0.33710859995298953, 0.30596805569223795,
            0.27753324889231423, 0.2508528150174008, 0.22739418525695945, 0.20633425835189317, 0.18439405565412664,
            0.1608919684047545, 0.1369815211265326, 0.11316431529371078, 0.09154710395986608, 0.07467775922040452,
            0.062117921442900716, 0.05242300427544114, 0.04424381024482809, 0.036116301295616444, 0.027251101894880794,
            0.01844634401442044, 0.010739551570860106, 0.004989239279245434, 0.001669532365610447,
            0.00035515827545105916, 4.2406743194369226e-05, 2.8818185437923897e-06, 4.7192084725462494e-07,
            4.040479990764334e-07, 3.975835744101022e-07, 3.551664790208909e-07, 2.2881717774348945e-07,
            8.10307618361586e-08, 1.3080763392563271e-08
        ],
        "bins": [
            0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0,
            2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1,
            4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.0, 6.1, 6.2,
            6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9
        ]
    }
