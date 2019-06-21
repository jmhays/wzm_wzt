#!/bin/bash
set -ev

pushd $HOME
git clone --depth=1 --no-single-branch https://github.com/kassonlab/gmxapi.git
pushd gmxapi
git fetch origin pull/224/head:pr-224
git checkout pr-224
rm -rf build
mkdir -p build
pushd build
cmake ../ -DCMAKE_CXX_COMPILER=$CXX \
    -DCMAKE_C_COMPILER=$CC \
    -DPYTHON_EXECUTABLE=$PYTHON
make -j2 install
make -j2 docs
popd
popd
mpiexec -n 2 $PYTHON -m mpi4py -m pytest --log-cli-level=DEBUG --pyargs gmx -s --verbose
popd
