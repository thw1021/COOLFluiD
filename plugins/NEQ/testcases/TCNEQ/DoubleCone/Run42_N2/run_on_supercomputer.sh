#!/bin/bash
# ============================================================================
# 主验证算例：CUBRC 双锥 Run 42（N2 两温 TCNEQ, Mutation++ n2_2）
# 对比目标：壁面压力/热流 vs 实验（Lani 2009 论文图 6.18a/6.19a）
#   25°锥平台 P≈9-10 kPa；交接峰 P≈45-50 kPa @x≈0.105m；再附着峰 q≈(4-6)e5 W/m²
# 停止条件：残差 -5.5（Mutation2OLD 参考收敛到 -5.84）
# 关键输出（跑完拷回）: RESULTS_Dcone_TCNEQ_MPP/ 下
#   DConeFVM_heat.plt-P0Side0（壁面P/q）、convergence.plt-P0.Default、DConeFVM-iter_*.plt
# 后处理: python3 $CF/postproc/postprocess_run42.py RESULTS_Dcone_TCNEQ_MPP
# 用法: ./run_on_supercomputer.sh [NP]   （默认 16 核；建议 16-32，walltime≥48h）
# ============================================================================
set -e
CASEDIR=$(cd "$(dirname "$0")" && pwd)
CF=$(cd "$CASEDIR/../../../../../.." && pwd)
[ -f "$CF/env.supercomputer.sh" ] && source "$CF/env.supercomputer.sh"
NP=${1:-16}
cd "$CASEDIR"
mpirun -np "$NP" "$CF/build/optim/apps/Solver/coolfluid-solver" \
  --scase "$CASEDIR/DConeN2_42_FVM_M++.CFcase" \
  --bdir "$CF" --ldir "$CF/build/optim/dso" 2>&1 | tee dcone_supercomputer.log
