#!/bin/bash
# =============================================================================
# CUBRC 双锥 Run 42 主验证算例 - SLURM 版（上传后 sbatch slurm_dcone.sh）
# NS 轴对称 + N2 两温 TCNEQ (Mutation++ n2_2, ChemNonEqTTv)
# 对比目标：壁面压力/热流 vs CUBRC LENS I 实验 (Lani 2009 论文图 6.18a/6.19a)
# 网格 65280 三角形，残差目标 -5.5 (老求解器参考 -5.84)
# 16 核约 1-2 天；walltime 48 h 留足余量
# =============================================================================
#SBATCH --job-name=dcone42
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --time=48:00:00
#SBATCH --partition=normal        # <-- adjust to your site
#SBATCH --export=ALL

set -e
source ~/.bashrc

CASE_DIR=${SLURM_SUBMIT_DIR:-$(pwd)}
CF=$(cd "$CASE_DIR/../../../../../.." && pwd)
NP=${SLURM_NTASKS:-16}

cd "$CASE_DIR"

echo "=== Double cone Run 42 start $(date) ==="
echo "  CASE_DIR = $CASE_DIR"
echo "  CF root  = $CF"
echo "  NP       = $NP"

mpirun -np "$NP" "$CF/build/optim/apps/Solver/coolfluid-solver" \
  --scase "$CASE_DIR/DConeN2_42_FVM_M++.CFcase" \
  --bdir "$CF" --ldir "$CF/build/optim/dso" 2>&1 | tee dcone_slurm.log

echo "=== Double cone Run 42 complete $(date) ==="

# 收敛检查
CONV=RESULTS_Dcone_TCNEQ_MPP/convergence.plt-P0.Default
if [ -f "$CONV" ]; then
    LAST_RES=$(tail -1 "$CONV" | awk '{print $NF}')
    echo "  final residual: $LAST_RES (target: <= -5.5)"
else
    echo "  [WARN] convergence file not found: $CONV"
fi

echo "Outputs in RESULTS_Dcone_TCNEQ_MPP/:"
echo "  DConeFVM_heat.plt-P0Side0 (wall P/q), convergence.plt-P0.Default, DConeFVM-iter_*.plt"
echo "Post-processing: python3 script/postprocess_run42.py RESULTS_Dcone_TCNEQ_MPP"
echo "  -> wall P/q vs experiment (digitized in script/exp_run42_digitized.dat)"
