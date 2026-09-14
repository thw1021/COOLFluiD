#!/bin/bash
# =============================================================================
# FIRE II 再入 t=1643s 算例 - SLURM 版（上传后 sbatch slurm_fireii.sh）
# NS 轴对称 + 11 组元空气 CNEQ 1T (Mutation++ air_11, ChemNonEq1T)
# 验证目标：残差 -4.0 (内置 Mutation2 参考收敛到 -4.0033)
# 驻点热流 ~1e6 W/m² 量级；激波层 N/O 解离与 NO 分层合理
# 网格 ~16 万三角形，32 核约数小时；walltime 24 h
# =============================================================================
#SBATCH --job-name=fireii
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --time=24:00:00
#SBATCH --partition=normal        # <-- adjust to your site
#SBATCH --export=ALL

set -e
source ~/.bashrc

CASE_DIR=${SLURM_SUBMIT_DIR:-$(pwd)}
CF=$(cd "$CASE_DIR/../../../../.." && pwd)
NP=${SLURM_NTASKS:-32}

cd "$CASE_DIR"

echo "=== FIRE II t=1643s start $(date) ==="
echo "  CASE_DIR = $CASE_DIR"
echo "  CF root  = $CF"
echo "  NP       = $NP"

mpirun -np "$NP" "$CF/build/optim/apps/Solver/coolfluid-solver" \
  --scase "$CASE_DIR/fire2_1643s_CNEQ_Mpp.CFcase" \
  --bdir "$CF" --ldir "$CF/build/optim/dso" 2>&1 | tee fireii_slurm.log

echo "=== FIRE II complete $(date) ==="

# 收敛检查
CONV=RESULT_FIREII_MPP_A11_A11/convergence.plt.Default
if [ -f "$CONV" ]; then
    LAST_RES=$(tail -1 "$CONV" | awk '{print $NF}')
    echo "  final residual: $LAST_RES (target: <= -4.0)"
else
    echo "  [WARN] convergence file not found: $CONV"
fi

echo "Outputs in RESULT_FIREII_MPP_A11_A11/:"
echo "  wall.pltWall (wall heat flux), fire2.plt (volume), convergence.plt.Default"
echo "Check: stagnation heat flux ~1e6 W/m2, shock standoff, NO peak layer position"
