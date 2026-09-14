#!/bin/bash
# ============================================================================
# 生产算例：FIRE II 再入 t=1643s（11组元空气 CNEQ 1T, Mutation++ air_11）
# 验证目标：残差 -4.0（内置 Mutation2 参考收敛到 -4.0033）；
#   驻点热流 ~1e6 W/m² 量级；激波层 N/O 解离与 NO 分层合理
# 关键输出（跑完拷回）: RESULT_FIREII_MPP_A11/ 下壁面热流与流场 plt
# 用法: ./run_on_supercomputer.sh [NP]   （默认 32 核；建议 ≥32，walltime 24h）
# ============================================================================
set -e
CASEDIR=$(cd "$(dirname "$0")" && pwd)
CF=$(cd "$CASEDIR/../../../../.." && pwd)
[ -f "$CF/env.supercomputer.sh" ] && source "$CF/env.supercomputer.sh"
NP=${1:-32}
cd "$CASEDIR"
mpirun -np "$NP" "$CF/build/optim/apps/Solver/coolfluid-solver" \
  --scase "$CASEDIR/fire2_1643s_CNEQ_Mpp.CFcase" \
  --bdir "$CF" --ldir "$CF/build/optim/dso" 2>&1 | tee fire2_supercomputer.log
