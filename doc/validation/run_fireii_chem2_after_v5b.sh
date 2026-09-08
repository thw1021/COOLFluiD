#!/bin/bash
# Chain runner 2: wait for the Hornung V5b rerun to finish, then relaunch the
# FireII chemistry phase (run2) on 12 cores.
#   run1 blew up at step 3090 right after the CFL 0.01->0.05 jump (NaN residual
#   was treated as "converged" and the run exited early).
#   run2 restarts from the clean snapshot fire2-iter_3000.CFmesh and holds
#   CFL=0.01 constant (proven stable for 2000+ consecutive steps).
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

LOG=doc/validation/fireii_chem2_chain.log
echo "=== $(date): chain2 started, waiting for Hornung V5b ===" >> ${LOG}

# Wait for the V5b solver to exit (max 4 h guard)
WAITED=0
while pgrep -f "coolfluid-solver.*hornung_FVM_NS_CNEQ_EULER_n2_2_V5" > /dev/null; do
  sleep 120
  WAITED=$((WAITED+2))
  if [ ${WAITED} -ge 240 ]; then
    echo "=== $(date): 4h guard hit, killing V5b wait ===" >> ${LOG}
    break
  fi
done
echo "=== $(date): V5b finished (waited ${WAITED} min), launching chemistry run2 ===" >> ${LOG}

${MPICH_DIR}/bin/mpirun -np 12 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run2.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/fireii_chem2.log 2>&1
echo "=== $(date): chemistry run2 complete (exit=$?) ===" >> ${LOG}
