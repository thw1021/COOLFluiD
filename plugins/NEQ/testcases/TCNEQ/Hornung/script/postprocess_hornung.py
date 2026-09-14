#!/usr/bin/env python3
"""Post-process COOLFluiD Hornung (HEG) cylinder Euler-CNEQ result:
parse the ASCII CFmesh field, build cell centres, extract the stagnation-line
profile and compute the shock stand-off distance from the cylinder nose.

Usage: python3 postprocess_hornung.py <CFmesh file>
"""
import sys, re
import numpy as np

def parse_cfmesh(path):
    lines = open(path).read().splitlines()
    hdr = {}
    sec = {}
    cur = None
    for l in lines:
        if l.startswith("!"):
            key = l.split()[0][1:]
            cur = key
            sec[key] = []
            if key in ("NB_NODES","NB_STATES","NB_ELEM","NB_DIM","NB_EQ"):
                hdr[key] = int(l.split()[1])
            continue
        if cur:
            sec[cur].append(l)
    nb_nodes, nb_elem = hdr["NB_NODES"], hdr["NB_ELEM"]
    xy = np.array([[float(v) for v in l.split()[:2]] for l in sec["LIST_NODE"][:nb_nodes]])
    elems = np.array([[int(v) for v in l.split()[:4]] for l in sec["LIST_ELEM"][:nb_elem]])
    nst = hdr["NB_STATES"]
    states = np.array([[float(v) for v in l.split()[:5]] for l in sec["LIST_STATE"][:nst]])
    return xy, elems, states

def main(path):
    xy, elems, st = parse_cfmesh(path)
    cen = xy[elems].mean(axis=1)          # (nb_elem, 2)
    x, y = cen[:, 0], cen[:, 1]
    ns = st.shape[1] - 3                  # 2 species -> vars [rho0,rho1,u,v,T]
    rho = st[:, :ns].sum(axis=1)
    T = st[:, ns+2]

    # nose: stagnation node on y=0 (MIN x: flow comes from +x, u<0)
    onaxis = np.abs(xy[:, 1]) < 1e-12
    ax_nodes = np.where(onaxis)[0]
    x_nose = xy[onaxis, 0].min()
    # stagnation-line cells: elements containing any axis node
    mask = np.isin(elems, ax_nodes).any(axis=1)
    line = np.where(mask)[0]
    order = line[np.argsort(x[line])]
    xs, Ts, rhos = x[order], T[order], rho[order]
    # shock: steepest T rise upstream
    dT = np.diff(Ts)
    i_sh = int(np.argmax(dT))
    x_shock = 0.5 * (xs[i_sh] + xs[i_sh+1])
    standoff = x_shock - x_nose
    print(f"cells on stagnation line : {len(xs)}")
    print(f"nose x                   : {x_nose:.6f} m  (R = 0.0127 m)")
    print(f"shock x                  : {x_shock:.6f} m")
    print(f"stand-off / R            : {standoff/0.0127:.4f}")
    print(f"stand-off distance       : {standoff*1000:.3f} mm")
    print(f"freestream (first cell)  : T = {Ts[0]:.1f} K, rho = {rhos[0]:.4g} kg/m3")
    print(f"max T on line            : {Ts.max():.1f} K")
    out = path.rsplit(".",1)[0] + "_stagline.dat"
    np.savetxt(out, np.column_stack([xs, Ts, rhos]), header="x[m] T[K] rho[kg/m3]")
    print("profile saved:", out)

if __name__ == "__main__":
    main(sys.argv[1])
