#!/bin/bash
# Smoke test both FireII and Hornung V5 (10 steps each)
# Must be run with dangerouslyDisableSandbox
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
export LD_LIBRARY_PATH=${CF_ROOT}/install/lib:${CF_ROOT}/build/optim/dso:${MPP_DIR}/install/lib:${MPICH_DIR}/lib:${BOOST_DIR}/lib:${PETSC_DIR}/arch-linux-c-opt/lib:${PARMETIS_DIR}/lib}

cd ${CF_ROOT}

#--- FireII smoke test (10 steps) ---
echo "===== FireII smoke test (10 steps) ====="
# Temporarily change to 10 steps
sed -i 's/MaxNumberSteps.nbSteps = 20000/MaxNumberSteps.nbSteps = 10/' plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase
rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_MPP_RUN/* 2>/dev/null
timeout 300 ${MPICH_DIR}/bin/mpirun -np 1 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | grep -iE "Iter:|Res:|CFL|assert|Exception|RUN PHASE|Writing|converg|Abort|KSP" | tail -15
# Restore
sed -i 's/MaxNumberSteps.nbSteps = 10/MaxNumberSteps.nbSteps = 20000/' plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase
echo "===== FireII smoke test done ====="
echo ""

#--- Hornung V5 smoke test (10 steps) ---
echo "===== Hornung V5 smoke test (10 steps) ====="
sed -i 's/MaxNumberSteps.nbSteps = 50000/MaxNumberSteps.nbSteps = 10/' plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase
rm -rf RESULTS_CNEQ_EULER_N22_V5/* 2>/dev/null
timeout 300 ${MPICH_DIR}/bin/mpirun -np 1 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | grep -iE "Iter:|Res:|CFL|assert|Exception|RUN PHASE|Writing|converg|Abort|KSP" | tail -15
# Restore
sed -i 's/MaxNumberSteps.nbSteps = 10/MaxNumberSteps.nbSteps = 50000/' plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase
echo "===== Hornung V5 smoke test done ====="
