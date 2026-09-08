#!/bin/bash
# Chain runner 3: wait for FireII chemistry run2 to finish, then launch
# Hornung V5c (CFL capped at 1.0 to avoid the V5b CFL=10 destabilisation).
source ~/.bashrc
export CF_ROOT=/home/tang/packages/COOLFluiD
export MPICH_DIR=/home/tang/packages/mpichInstall
export MPP_DIR=/home/tang/packages/Mutationpp
export PARMETIS_DIR=/home/tang/packages/ParMETIS/install-mpich
export BOOST_DIR=/home/tang/packages/boost_1_85_0/install
export PETSC_DIR=/home/tang/packages/petsc
export SHIM_DIR=${CF_ROOT}/doc/validation
export MPP_DIRECTORY=${MPP_DIR}
export MPP_DATA_DIRECTORY=${MPP_DIR}/data
export LD_PRELOAD=${SHIM_DIR}/libfakecuda.so
export LD_LIBRARY_PATH=${CF_ROOT}/install/lib:${CF_ROOT}/build/optim/dso:${MPP_DIR}/install/lib:${MPICH_DIR}/lib:${BOOST_DIR}/lib:${PETSC_DIR}/arch-linux-c-opt/lib:${PARMETIS_DIR}/lib
cd ${CF_ROOT}

LOG=doc/validation/v5c_chain.log
echo "=== $(date): chain3 started, waiting for FireII chemistry run2 ===" >> ${LOG}

WAITED=0
while pgrep -f "coolfluid-solver.*fire2_1643s_CNEQ_Mpp_run2" > /dev/null; do
  sleep 120
  WAITED=$((WAITED+2))
  if [ ${WAITED} -ge 300 ]; then
    echo "=== $(date): 5h guard hit, killing run2 wait ===" >> ${LOG}
    break
  fi
done
echo "=== $(date): run2 finished (waited ${WAITED} min), launching Hornung V5c ===" >> ${LOG}

${MPICH_DIR}/bin/mpirun -np 12 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5c.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/hornung_v5c.log 2>&1
echo "=== $(date): Hornung V5c complete (exit=$?) ===" >> ${LOG}
