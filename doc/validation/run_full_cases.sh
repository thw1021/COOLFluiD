#!/bin/bash
# Full production runs: Hornung V5 then FireII, 12 cores each
# Total estimated time: ~4-6h (well within 18h)
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
MPIRUN=${MPICH_DIR}/bin/mpirun
SOLVER=${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver

# ============ 1. Hornung V5 (fine mesh, 50000 steps) ============
echo "========================================"
echo "=== $(date): Starting Hornung V5 (12 cores, 50000 steps) ==="
echo "========================================"
rm -rf RESULTS_CNEQ_EULER_N22_V5/* 2>/dev/null
${MPIRUN} -np 12 ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | tee doc/validation/hornung_v5_full.log
echo "=== $(date): Hornung V5 finished ==="
echo ""

# ============ 2. FireII (20000 steps) ============
echo "========================================"
echo "=== $(date): Starting FireII (12 cores, 20000 steps) ==="
echo "========================================"
rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_MPP_RUN/* 2>/dev/null
${MPIRUN} -np 12 ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | tee doc/validation/fireii_full.log
echo "=== $(date): FireII finished ==="
echo ""
echo "=== ALL RUNS COMPLETE ==="
