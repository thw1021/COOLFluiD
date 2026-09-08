#!/bin/bash
# FireII pipeline v5: frozen chemistry (3000 steps) -> active chemistry (20000 steps)
# 12 cores. Run AFTER Hornung V5 completes.
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

# ============ Phase 2: FireII frozen chemistry (3000 steps) ============
echo "========================================"
echo "=== $(date): Phase 2 - FireII frozen (${NP} cores, 3000 steps) ==="
echo "========================================"
rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/* 2>/dev/null
${MPIRUN} -np ${NP} ${SOLVER} \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_frozen.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/fireii_frozen.log 2>&1
echo "=== $(date): Phase 2 complete (exit=$?) ==="

RESTART_FILE="${CF_ROOT}/plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/fire2-iter_3000.CFmesh"
if [ -f "${RESTART_FILE}" ]; then
  echo "=== Restart file OK: ${RESTART_FILE} ==="
  # ============ Phase 3: FireII active chemistry from restart (20000 steps) ===
  echo "========================================"
  echo "=== $(date): Phase 3 - FireII chemistry (${NP} cores, 20000 steps) ==="
  echo "========================================"
  rm -rf plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_MPP_RUN/* 2>/dev/null
  ${MPIRUN} -np ${NP} ${SOLVER} \
    --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp_run.CFcase \
    --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso > doc/validation/fireii_chem.log 2>&1
  echo "=== $(date): Phase 3 complete (exit=$?) ==="
else
  echo "=== Phase 3 SKIPPED (no restart file) ==="
  ls -la ${CF_ROOT}/plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_FROZEN/ | head
fi

echo ""
echo "=== FIREII PIPELINE COMPLETE ==="
echo "=== $(date) ==="
