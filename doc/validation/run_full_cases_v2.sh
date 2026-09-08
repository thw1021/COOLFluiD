#!/bin/bash
# Full production runs v2: FireII frozen → Hornung V5 → FireII chemistry
# Phase 1: FireII frozen chemistry (3000 steps, ~30 min)
# Phase 2: Hornung V5 fine mesh (50000 steps, ~3-4h)
# Phase 3: FireII chemistry from restart (20000 steps, ~3-4h)
# Total: ~7-9h (well within 18h limit)
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

# ============ Phase 1: FireII frozen chemistry (3000 steps) ============
echo "========================================"
echo "=== $(date): Phase 1 - FireII frozen chemistry (12 cores, 3000 steps) ==="
echo "========================================"
rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/* 2>/dev/null
${MPIRUN} -np 12 ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_frozen.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | tee doc/validation/fireii_frozen.log
echo "=== $(date): Phase 1 complete ==="
echo ""

# Check if frozen-chemistry restart file exists
RESTART_FILE="${CF_ROOT}/plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/fire2-iter_3000.CFmesh"
if [ ! -f "${RESTART_FILE}" ]; then
  echo "ERROR: Frozen chemistry restart file not found at ${RESTART_FILE}"
  echo "Looking for alternative files..."
  ls -la ${CF_ROOT}/plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/ 2>/dev/null
  echo "Skipping Phase 3 (FireII chemistry)"
else
  echo "Found restart file: ${RESTART_FILE}"
fi

# ============ Phase 2: Hornung V5 (fine mesh, 50000 steps) ============
echo "========================================"
echo "=== $(date): Phase 2 - Hornung V5 (12 cores, 50000 steps) ==="
echo "========================================"
rm -rf plugins/NEQ/testcases/TCNEQ/Hornung/RESULTS_CNEQ_EULER_N22_V5/* 2>/dev/null
${MPIRUN} -np 12 ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V5.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | tee doc/validation/hornung_v5_full.log
echo "=== $(date): Phase 2 complete ==="
echo ""

# ============ Phase 3: FireII chemistry from restart (20000 steps) ============
if [ -f "${RESTART_FILE}" ]; then
  echo "========================================"
  echo "=== $(date): Phase 3 - FireII chemistry (12 cores, 20000 steps) ==="
  echo "========================================"
  rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_MPP_RUN/* 2>/dev/null
  ${MPIRUN} -np 12 ${SOLVER} \
    --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase \
    --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso 2>&1 | tee doc/validation/fireii_chem.log
  echo "=== $(date): Phase 3 complete ==="
else
  echo "=== Phase 3 skipped (no restart file) ==="
fi

echo ""
echo "=== ALL PHASES COMPLETE ==="
echo "=== $(date) ==="
