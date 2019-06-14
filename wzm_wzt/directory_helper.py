"""Organizes the directory structure for BRER runs. Creates directories on the
fly.

How the directory structure is organized:
    - This script should be run from your "top" directory (where
      you are planning to run all your ensemble members)
    - The top directory contains ensemble member subdirectories
      This script is intended to handle just ONE ensemble member,
      so we'll only be concerned with a single member subdirectory.
    - The example below shows the directory structure at initialization.

.
└── 0                               # FIRST BRER ITERATION
    ├── num_test_sites_1
    │   └── production
    ├── num_test_sites_2
    │   └── production
    ├── num_test_sites_3
    │   └── production
    ├── num_test_sites_4
    │   └── production
    ├── num_test_sites_5
    │   └── production
    └── num_test_sites_6            # At the first, we test all six different pairs with single target
        ├── 10088_12035             # FIRST PAIR
        │   ├── convergence         # only run training and convergence to get work calc'ns
        │   └── training
        ├── 3673_10088
        │   ├── convergence
        │   └── training
        ├── 3673_12035
        │   ├── convergence
        │   └── training
        ├── 3673_5636
        │   ├── convergence
        │   └── training
        ├── 5636_10088
        │   ├── convergence
        │   └── training
        ├── 5636_12035
        │   ├── convergence
        │   └── training
        ├── production              # run a *SINGLE* production phase once you decide which pair to restrain.
        └── work.json               # store work calculation data
"""

import os


class DirectoryHelper:
    def __init__(self, top_dir, param_dict):
        """Small class for manipulating a standard directory structure for BRER
        runs.

        Parameters
        ----------
        top_dir :
            the path to the directory containing all the ensemble members.
        param_dict :
            a dictionary specifying the ensemble number, the iteration, the number of total test sites, the specific test site of interest, and the phase of the simulation.

        Returns
        -------
        """
        self._top_dir = top_dir
        self._required_parameters = ['ensemble_num', 'iteration', 'num_test_sites', 'test_site', 'phase']
        for required in self._required_parameters:
            if required not in param_dict:
                raise ValueError('Must define {}'.format(required))
        self._param_dict = param_dict

    def get_dir(self, level):
        """Get the directory for however far you want to go down the directory
        tree.

        Parameters
        ----------
        level :
            one of 'top', 'ensemble_num', 'iteration', 'test_site', or 'phase'.
            See the directory structure example provided at the beginning of this class.

        Returns
        -------
        type
            the path to the specified directory 'level' as a str.
        """
        pdict = self._param_dict
        if level == 'top':
            return_dir = self._top_dir
        elif level == 'ensemble_num':
            return_dir = '{}/mem_{}'.format(self._top_dir, pdict['ensemble_num'])
        elif level == 'iteration':
            return_dir = '{}/mem_{}/{}'.format(self._top_dir, pdict['ensemble_num'], pdict['iteration'])
        elif level == 'test_site':
            return_dir = '{}/mem_{}/{}/num_test_sites_{}/{}'.format(self._top_dir, pdict['ensemble_num'],
                                                                    pdict['iteration'], pdict['num_test_sites'],
                                                                    pdict['test_site'])
        elif level == 'phase':
            return_dir = '{}/mem_{}/{}/num_test_sites_{}/{}/{}'.format(self._top_dir, pdict['ensemble_num'],
                                                                       pdict['iteration'], pdict['num_test_sites'],
                                                                       pdict['test_site'], pdict['phase'])
        else:
            raise ValueError('{} is not a valid directory type for BRER simulations'.format('type'))
        return return_dir

    def build_working_dir(self):
        """Checks to see if the working directory for current state of BRER
        simulation exists. If it does not, creates the directory.

        Parameters
        ----------

        Returns
        -------
        """
        os.makedirs(self.get_dir('phase'), exist_ok=True)

    def change_dir(self, level):
        """

        Parameters
        ----------
        level :


        Returns
        -------

        """
        os.chdir(self.get_dir(level))
