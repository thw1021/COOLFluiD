#!/bin/bash
# ==============================================================================
# Supercomputer submission script — DoubleCone Run42 N2 TCNEQ (Mutation++)
# COOLFluiD high-enthalpy validation
#
# Estimated cost: >=16 cores, 1-2 days wall time
# Mesh: ~50000 cells, 2-temperature (TCNEQ) N2 model, 5 equations (2 species + 3 Euler + Tv)
#
# Usage:
#   PBS:  qsub run_dcone_supercomputer.sh
#   SLURM: sbatch run_dcone_supercomputer.sh
#
# IMPORTANT: On the supercomputer, the CUDA shim (libfakecuda.so) is NOT needed
# if GPUs are available. If no GPU, ensure COOLFluiD was built with CPU-only
# support or provide the shim.
# ==============================================================================

# --- PBS directives (uncomment for PBS) ---
#PBS -N DCone_Run42
#PBS -l nodes=4:ppn=8          # 32 cores
#PBS -l walltime=48:00:00
#PBS -q normal
#PBS -V

# --- SLURM directives (uncomment for SLURM) ---
#SBATCH --job-name=DCone_Run42
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8   # 32 cores
#SBATCH --time=48:00:00
#SBATCH --partition=normal

# --- Environment ---
source ~/.bashrc

CF_ROOT=/home/tang/packages/COOLFluiD
MPICH_DIR=/home/tang/packages/mpichInstall
MPP_DIR=/home/tang/packages/Mutationpp
PARMETIS_DIR=/home/tang/packages/ParMETIS/install-mpich
BOOST_DIR=/home/tang/packages/boost_1_85_0/install
PETSC_DIR=/home/tang/packages/petsc

export MPP_DIRECTORY=${MPP_DIR}
export MPP_DATA_DIRECTORY=${MPP_DIR}/data

# LD_PRELOAD: only needed if CUDA driver is flaky on the compute node
# export LD_PRELOAD=${CF_ROOT}/doc/validation/libfakecuda.so

export LD_LIBRARY_PATH=${CF_ROOT}/install/lib:${CF_ROOT}/build/optim/dso:${MPP_DIR}/install/lib:${MPICH_DIR}/lib:${BOOST_DIR}/lib:${PETSC_DIR}/arch-linux-c-opt/lib:${PARMETIS_DIR}/lib

cd ${CF_ROOT}

# --- Run ---
NP=${SLURM_NTASKS:-32}   # SLURM auto-sets SLURM_NTASKS; fallback 32 for PBS
echo "Starting DoubleCone Run42 with ${NP} cores at $(date)"

${MPICH_DIR}/bin/mpirun -np ${NP} \
  ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/DConeN2_42_FVM_M++.CFcase \
  --bdir ${CF_ROOT} \
  --ldir ${CF_ROOT}/build/optim/dso \
  2>&1 | tee ${CF_ROOT}/RESULTS_Dcone_TCNEQ_MPP/run.log

echo "Finished at $(date)"

# --- Postprocessing ---
# After the run completes, extract wall pressure/heat flux and compare with
# CUBRC experimental data (Lani 2009, Fig. 6.18/6.19, PDF p. 183):
#   python3 ${CF_ROOT}/doc/validation/postprocess_run42.py RESULTS_Dcone_TCNEQ_MPP/
#
# Experimental data (digitized): exp_run42_digitized.dat
