#!/bin/bash
# Chain runner: wait for the FireII chemistry run to finish, then launch
# Hornung V5b (ScalingFactor fix) on 12 cores. Keeps total core usage at 12.
source ~/.bashrc
export CF_ROOT=/home/tang/packages/COOLFluiD
export MPICH_DIR=/home/tang/packages/mpichInstall
export MPP_DIR=/home/tang/packages/Mutationpp
export PARMETIS_DIR=/home/tang/packages/ParMETIS/install-mpich
export BOOST_DIR=/home/tang/packages/boost_1_85_0/install
export PETSC_DIR=/home/tang/packages/petsc
export SHIM_DIR=/home/tang/packages/COOLFluiD/doc/validation
export MPP_DIRECTORY=${MPP_DIR}
export MPP_DATA_DIRECTORY=${MPP_DIR}/data
export LD_PRELOAD=${SHIM_DIR}/libfakecuda.so
export LD_LIBRARY_PATH=${CF_ROOT}/install/lib:${CF_ROOT}/build/optim/dso:${MPP_DIR}/install/lib:${MPICH_DIR}/lib:${BOOST_DIR}/lib:${PETSC_DIR}/arch-linux-c-opt/lib:${PARMETIS_DIR}/lib
cd ${CF_ROOT}

LOG=doc/validation/hornung_v5b_chain.log
echo "=== $(date): chain started, waiting for FireII chemistry ===" >> ${LOG}

# Wait for the chemistry solver to exit (max 6 h guard)
WAITED=0
while pgrep -f "coolfluid-solver.*fire2_1643s_CNEQ_Mpp_run" > /dev/null; do
  sleep 120
  WAITED=$((WAITED+2))
  if [ ${WAITED} -ge 360 ]; then
    echo "=== $(date): 6h guard hit, killing chemistry wait ===" >> ${LOG}
    break
  fi
done
echo "=== $(date): chemistry finished (waited ${WAITED} min) ===" >> ${LOG}

# Preserve the broken-scale V5 results for the report, then rerun
if [ -d RESULTS_CNEQ_EULER_N22_V5 ]; then
  rm -rf RESULTS_CNEQ_EULER_N22_V5_BROKEN_SCALE
  mv RESULTS_CNEQ_EULER_N22_V5 RESULTS_CNEQ_EULER_N22_V5_BROKEN_SCALE
fi

${MPICH_DIR}/bin/mpirun -np 12 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/hornung_v5b.log 2>&1
echo "=== $(date): Hornung V5b complete (exit=$?) ===" >> ${LOG}
