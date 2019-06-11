#!/bin/bash
set -ev

export GMX_DOUBLE=OFF
export GMX_MPI=OFF
export GMX_THREAD_MPI=ON
export GMXAPI=ON

export CCACHE_DIR=$HOME/.ccache_gromacs
ccache -s

pushd $HOME
[ -d gromacs-gmxapi ] || git clone --depth=1 --no-single-branch https://github.com/kassonlab/gromacs-gmxapi.git
pushd gromacs-gmxapi
git branch -a
git checkout release-2019
rm -rf build  # get rid of any possible lingering build directories
mkdir build
pushd build
cmake ../ -DCMAKE_CXX_COMPILER=$CXX \
    -DCMAKE_C_COMPILER=$CC \
    -DGMX_DOUBLE=$GMX_DOUBLE \
    -DGMX_MPI=$GMX_MPI \
    -DGMX_THREAD_MPI=$GMX_THREAD_MPI \
    -DGMXAPI=$GMXAPI \
    -DCMAKE_INSTALL_PREFIX=$HOME/install/gromacs-gmxapi
make -j2 install
popd
popd
popd