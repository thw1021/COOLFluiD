#!/bin/bash
# Generic chemistry-phase monitor: every 10 min, record iter/Res/Tmax/q_stag.
# Usage: monitor_fireii_chem2.sh <result_dir> <solver_log> <trend_file>
source ~/.bashrc
RDIR=${1:-/home/tang/packages/COOLFluiD/RESULT_FIREII_MPP_RUN2}
SLOG=${2:-/home/tang/packages/COOLFluiD/doc/validation/fireii_chem2.log}
TREND=${3:-/home/tang/packages/COOLFluiD/doc/validation/fireii_chem2_trend.log}
PLT=${RDIR}/fire2.plt
WALL=${RDIR}/wall.plt-P0Wall
echo "time iter Res Tmax q_stag" >> ${TREND}
WAITED=0
while true; do
  if ! pgrep -f "coolfluid-solver.*fire2_1643s_CNEQ_Mpp_run2" > /dev/null; then
    # run2 not started yet (or finished) -- wait unless it already finished
    if [ ${WAITED} -gt 0 ]; then
      echo "$(date +%H:%M) solver exited; monitor done" >> ${TREND}
      break
    fi
    sleep 120
    continue
  fi
  ITER=$(grep -E "^Iter:" ${SLOG} 2>/dev/null | tail -1 | sed 's/Iter: *\([0-9]*\).*/\1/')
  RES=$(grep -E "^Iter:" ${SLOG} 2>/dev/null | tail -1 | sed 's/.*Res: \[[ ]*\([-0-9.e+]*\).*/\1/')
  TMAX=$(python3 - << PYEOF
import re
def tmax(fn):
    try:
        with open('${PLT}') as f:
            lines = f.readlines()
    except IOError:
        return 'nan'
    it = [i for i,l in enumerate(lines) if l.startswith('VARIABLES')][0]
    vars_ = re.findall(r'"([^"]+)"', lines[it])
    iT = vars_.index('T')
    iz = [i for i,l in enumerate(lines) if l.startswith('ZONE')][0]
    n = int(re.search(r'N=(\d+)', lines[iz]).group(1))
    vals = []
    for l in lines[iz+1:iz+1+n]:
        p = l.split()
        if len(p) >= len(vars_):
            try: vals.append(float(p[iT]))
            except ValueError: pass
    return max(vals) if vals else float('nan')
print('%.4g' % tmax('${PLT}'))
PYEOF
)
  QSTAG=$(python3 - << PYEOF
import numpy as np
try:
    w = np.loadtxt('${WALL}', skiprows=2)
    print('%.4g' % w[np.argmax(np.abs(w[:,2])), 6])
except Exception:
    print('nan')
PYEOF
)
  echo "$(date +%H:%M) ${ITER:-nan} ${RES:-nan} ${TMAX} ${QSTAG}" >> ${TREND}
  sleep 600
  WAITED=$((WAITED+10))
  if [ ${WAITED} -ge 240 ]; then
    echo "$(date +%H:%M) monitor 4h guard exit" >> ${TREND}
    break
  fi
done
