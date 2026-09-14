#!/bin/bash
# =============================================================================
# Hornung HEG 圆柱预检算例 - SLURM 版（上传后 sbatch slurm_hornung.sh）
# N2 化学非平衡 (Mutation++ n2_2, ChemNonEq1T, Euler2DNEQ)
# 通过判据：残差 -3.00009；激波脱体 0.209 R (±0.01)；激波后峰值 T≈9800 K
# 网格 800 四边形，~38000 步收敛，4 核约 15 分钟
# =============================================================================
#SBATCH --job-name=hornung
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --time=01:00:00
#SBATCH --partition=normal        # <-- adjust to your site
#SBATCH --export=ALL

set -e
source ~/.bashrc

CASE_DIR=${SLURM_SUBMIT_DIR:-$(pwd)}
CF=$(cd "$CASE_DIR/../../../../.." && pwd)
NP=${SLURM_NTASKS:-4}

cd "$CASE_DIR"

echo "=== Hornung pre-check start $(date) ==="
echo "  CASE_DIR = $CASE_DIR"
echo "  CF root  = $CF"
echo "  NP       = $NP"

mpirun -np "$NP" "$CF/build/optim/apps/Solver/coolfluid-solver" \
  --scase "$CASE_DIR/hornung_FVM_NS_CNEQ_EULER_n2_2_V3.CFcase" \
  --bdir "$CF" --ldir "$CF/build/optim/dso" 2>&1 | tee hornung_slurm.log

echo "=== Hornung run complete $(date) ==="

# 收敛检查：convergence.plt.Default 末行残差应 ≤ -3.0
CONV=RESULTS_CNEQ_EULER_N22_V3/convergence.plt.Default
if [ -f "$CONV" ]; then
    LAST_RES=$(tail -1 "$CONV" | awk '{print $NF}')
    echo "  final residual: $LAST_RES (target: <= -3.0)"
else
    echo "  [WARN] convergence file not found: $CONV"
fi

echo "Post-processing: python3 script/postprocess_hornung.py RESULTS_CNEQ_EULER_N22_V3/HornungN2.CFmesh"
echo "  -> standoff distance (target: 0.209 R), peak T (target: ~9800 K)"
