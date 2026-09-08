#!/bin/bash
# Monitor the FireII chemistry run: every 10 min, record iter/Res/Tmax/q_stag
# into a trend log so the relaxation toward a physical shock layer can be
# quantified. Runs until the solver process exits (or 5 h guard).
source ~/.bashrc
TREND=/home/tang/packages/COOLFluiD/doc/validation/fireii_chem_trend.log
PLT=/home/tang/packages/COOLFluiD/RESULT_FIREII_MPP_RUN/fire2.plt
WALL=/home/tang/packages/COOLFluiD/RESULT_FIREII_MPP_RUN/wall.plt-P0Wall
LOG=/home/tang/packages/COOLFluiD/doc/validation/fireii_chem.log
echo "time iter Res Tmax q_stag" >> ${TREND}
WAITED=0
while pgrep -f "coolfluid-solver.*fire2_1643s_CNEQ_Mpp_run" > /dev/null; do
  ITER=$(grep -E "^Iter:" ${LOG} | tail -1 | awk '{print $2}')
  RES=$(grep -E "^Iter:" ${LOG} | tail -1 | awk '{print $4}')
  TMAX=$(python3 - << PYEOF
import re, numpy as np
def tmax(fn):
    with open('${PLT}') as f:
        lines = f.readlines()
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
  echo "$(date +%H:%M) ${ITER} ${RES} ${TMAX} ${QSTAG}" >> ${TREND}
  sleep 600
  WAITED=$((WAITED+10))
  if [ ${WAITED} -ge 300 ]; then
    echo "$(date +%H:%M) monitor 5h guard exit" >> ${TREND}
    break
  fi
done
echo "$(date +%H:%M) solver exited; monitor done" >> ${TREND}
