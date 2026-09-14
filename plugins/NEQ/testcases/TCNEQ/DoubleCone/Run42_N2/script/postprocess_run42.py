#!/usr/bin/env python3
"""Post-process COOLFluiD double-cone Run 42 wall data and compare with
digitized CUBRC LENS I experimental data (Lani 2009 thesis Figs 6.18a/6.19a).

Usage: python3 postprocess_run42.py <RESULTS_DIR>
  <RESULTS_DIR>/DConeFVM_heat.plt-P0Side0  (or .../DConeFVM_heat.pltSide0)
Columns: x0 x1 P T rho Cp heatF Stanton yplus Cf muWall heatFRad

Outputs: dcone_wall_comparison.png + printed key metrics.
"""
import sys, os, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_wall(path):
    rows = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(("TITLE", "VARIABLES", "ZONE")):
                continue
            parts = s.split()
            try:
                rows.append([float(p) for p in parts[:12]])
            except ValueError:
                continue
    a = np.array(rows)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 6]  # x, y, P, heatF

def main(resdir):
    cands = (glob.glob(os.path.join(resdir, "DConeFVM_heat.plt-P0Side0")) +
             glob.glob(os.path.join(resdir, "DConeFVM_heat.pltSide0")))
    if not cands:
        sys.exit(f"no wall heat file found in {resdir}")
    x, y, P, q = load_wall(cands[0])
    order = np.argsort(x)
    x, P, q = x[order], P[order], q[order]

    exp = np.loadtxt(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp_run42_digitized.dat"))
    xe, Pe, Qe = exp[:, 0], exp[:, 1], exp[:, 2]

    # key metrics
    def at(xq, xs, vs):
        i = np.argmin(np.abs(xs - xq))
        return vs[i]
    metrics = {
        "cone1 plateau P @x=0.07 [Pa]": at(0.07, x, P),
        "cone1 plateau q @x=0.04 [W/m2]": at(0.04, x, q),
        "peak P [Pa]": P.max(),
        "x of peak P [m]": x[np.argmax(P)],
        "peak q [W/m2]": q.max(),
        "x of peak q [m]": x[np.argmax(q)],
        "cone2 P @x=0.13 [Pa]": at(0.13, x, P),
        "cone2 q @x=0.13 [W/m2]": at(0.13, x, q),
    }
    print("== Run 42 wall metrics (Mutation++ run) ==")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4g}")
    print("== experimental reference (digitized) ==")
    print(f"  cone1 plateau P ~ {np.median(Pe[(xe>0.06)&(xe<0.09)]):.4g} Pa")
    print(f"  junction peak P ~ {Pe.max():.4g} Pa @ x={xe[np.argmax(Pe)]:.3f} m")
    print(f"  reattachment peak q ~ {Qe.max():.4g} W/m2 @ x={xe[np.argmax(Qe)]:.3f} m")

    fig, axs = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    axs[0].plot(x, P/1e3, "r-", label="COOLFluiD FVM + Mutation++")
    axs[0].plot(xe, Pe/1e3, "bs", mfc="none", label="Run 42 experiment (digitized)")
    axs[0].set_ylabel("Pw [kPa]"); axs[0].legend(); axs[0].grid(alpha=0.3)
    axs[0].set_title("Double cone Run 42: surface pressure (thesis Fig 6.18a)")
    axs[1].plot(x, q, "r-", label="COOLFluiD FVM + Mutation++")
    axs[1].plot(xe, Qe, "bs", mfc="none", label="Run 42 experiment (digitized)")
    axs[1].set_ylabel("Q [W/m2]"); axs[1].set_xlabel("x [m]"); axs[1].legend(); axs[1].grid(alpha=0.3)
    axs[1].set_title("Surface heat flux (thesis Fig 6.19a)")
    out = os.path.join(resdir, "dcone_wall_comparison.png")
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print("saved:", out)

if __name__ == "__main__":
    main(sys.argv[1])
