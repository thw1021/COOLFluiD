#!/bin/bash
# ============================================================================
# 预检算例：HEG 圆柱 Hornung（N2 化学非平衡, Mutation++ n2_2, Euler CNEQ）
# 通过判据（本地已验证，超算应复现）：
#   - 收敛残差 -3.00009（约 38000 步）
#   - 激波脱体距离 0.209 R（R=12.7mm）；激波后峰值 T ≈ 9800 K
# 后处理: python3 $CF/postproc/postprocess_hornung.py RESULTS_CNEQ_EULER_N22_V3/HornungN2.CFmesh
# 用法: ./run_on_supercomputer.sh [NP]   （默认 4 核；建议 4-8）
# ============================================================================
set -e
CASEDIR=$(cd "$(dirname "$0")" && pwd)
CF=$(cd "$CASEDIR/../../../../.." && pwd)
[ -f "$CF/env.supercomputer.sh" ] && source "$CF/env.supercomputer.sh"
NP=${1:-4}
cd "$CASEDIR"
mpirun -np "$NP" "$CF/build/optim/apps/Solver/coolfluid-solver" \
  --scase "$CASEDIR/hornung_FVM_NS_CNEQ_EULER_n2_2_V3.CFcase" \
  --bdir "$CF" --ldir "$CF/build/optim/dso" 2>&1 | tee hornung_supercomputer.log
