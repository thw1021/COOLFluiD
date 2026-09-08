#!/bin/bash
# Full pipeline v3: Hornung V5 → FireII frozen → FireII chemistry
# All on 12 cores, total ~7-9 hours (within 18h limit)
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
MPIRUN=${MPICH_DIR}/bin/mpirun
SOLVER=${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver
NP=12

# ============ Phase 1: Hornung V5 (fine mesh, 50000 steps) ============
echo "========================================"
echo "=== $(date): Phase 1 - Hornung V5 (${NP} cores, 50000 steps) ==="
echo "========================================"
rm -rf plugins/NEQ/testcases/TCNEQ/Hornung/RESULTS_CNEQ_EULER_N22_V5/* 2>/dev/null
${MPIRUN} -np ${NP} ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/hornung_v5_full.log 2>&1
echo "=== $(date): Phase 1 complete (exit=$?) ==="
echo ""

# ============ Phase 2: FireII frozen chemistry (3000 steps) ============
echo "========================================"
echo "=== $(date): Phase 2 - FireII frozen chemistry (${NP} cores, 3000 steps) ==="
echo "========================================"
rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/* 2>/dev/null
${MPIRUN} -np ${NP} ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_frozen.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/fireii_frozen.log 2>&1
echo "=== $(date): Phase 2 complete (exit=$?) ==="
echo ""

# Check for restart file
RESTART_FILE="${CF_ROOT}/plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/fire2-iter_3000.CFmesh"
echo "=== Looking for restart file: ${RESTART_FILE} ==="
ls -la ${RESTART_FILE} 2>/dev/null || echo "Restart file not found - listing result files:"
ls -la ${CF_ROOT}/plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/ 2>/dev/null | head -10

# ============ Phase 3: FireII chemistry from restart (20000 steps) ============
if [ -f "${RESTART_FILE}" ]; then
  echo "========================================"
  echo "=== $(date): Phase 3 - FireII chemistry (${NP} cores, 20000 steps) ==="
  echo "========================================"
  rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_MPP_RUN/* 2>/dev/null
  ${MPIRUN} -np ${NP} ${SOLVER} \
    --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase \
    --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/fireii_chem.log 2>&1
  echo "=== $(date): Phase 3 complete (exit=$?) ==="
else
  echo "=== Phase 3 skipped (no restart file) ==="
fi

echo ""
echo "=== ALL PHASES COMPLETE ==="
echo "=== $(date) ==="
