#!/bin/bash
# COOLFluiD run wrapper - sets all required environment variables
# Usage: run_coolfluid.sh <case_file> <np> [timeout_seconds]
set -e

CASE_FILE="${1:?Usage: $0 <case_file> <np> [timeout_sec]}"
NP="${2:?Usage: $0 <case_file> <np> [timeout_sec]}"
TIMEOUT="${3:-0}"

CF_ROOT=/home/tang/packages/COOLFluiD
MPICH_DIR=/home/tang/packages/mpichInstall
MPP_DIR=/home/tang/packages/Mutationpp
PARMETIS_DIR=/home/tang/packages/ParMETIS/install-mpich
BOOST_DIR=/home/tang/packages/boost_1_85_0/install
PETSC_DIR=/home/tang/packages/petsc
SHIM_DIR=/home/tang/packages/COOLFluiD/doc/validation

export MPP_DIRECTORY=${MPP_DIR}
export MPP_DATA_DIRECTORY=${MPP_DIR}/data
export LD_PRELOAD=${SHIM_DIR}/libfakecuda.so
export LD_LIBRARY_PATH=${CF_ROOT}/install/lib:${CF_ROOT}/build/optim/dso:${MPP_DIR}/install/lib:${MPICH_DIR}/lib:${BOOST_DIR}/lib:${PETSC_DIR}/arch-linux-c-opt/lib:${PARMETIS_DIR}/lib

cd ${CF_ROOT}

MPIRUN=${MPICH_DIR}/bin/mpirun
SOLVER=${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver

if [ "${TIMEOUT}" -gt 0 ]; then
    timeout ${TIMEOUT} ${MPIRUN} -np ${NP} ${SOLVER} \
        --scase ${CASE_FILE} \
        --bdir ${CF_ROOT} \
        --ldir ${CF_ROOT}/build/optim/dso
else
    ${MPIRUN} -np ${NP} ${SOLVER} \
        --scase ${CASE_FILE} \
        --bdir ${CF_ROOT} \
        --ldir ${CF_ROOT}/build/optim/dso
fi
