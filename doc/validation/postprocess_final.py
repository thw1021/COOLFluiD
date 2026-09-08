#!/usr/bin/env python3
"""
Post-process final results of the 18h validation campaign:

  1. Hornung V5  (Euler2DNEQ, n2_2, 50000 steps)  -> shock stand-off, states
  2. FireII frozen (NavierStokes2DNEQ, air_11, 1159 steps) -> stag-line T,
     stand-off, wall heat-flux sanity check

ASCII-only output.
"""
import os
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DOC = '/home/tang/packages/COOLFluiD/doc/validation'
TCNEQ = '/home/tang/packages/COOLFluiD/plugins/NEQ/testcases/TCNEQ'
V5_DIR = f'{TCNEQ}/Hornung/results/RESULTS_CNEQ_EULER_N22_V5C'
V5B_DIR = f'{TCNEQ}/Hornung/results/RESULTS_CNEQ_EULER_N22_V5'   # invalid (CFL=10)
FRZ_DIR = f'{TCNEQ}/FireII/results/RESULT_FIREII_FROZEN'
CHEM_DIR = f'{TCNEQ}/FireII/results/RESULT_FIREII_MPP_RUN2'  # run2 (CFL=0.01)

# ---------------- Hornung references ----------------
CYL_R = 0.0127
U_INF = 5590.0
T_INF = 1833.0
RHO_INF = 0.004956
P_INF = 2909.0
MPP_FRZ = dict(T=13913.8, V=854.5, P=144452.3)
MPP_EQU = dict(T=6661.8, V=476.8, P=155742.4)
RHO_RATIO_FRZ = U_INF / MPP_FRZ['V']
RHO_RATIO_EQU = U_INF / MPP_EQU['V']
EXP_STANDOFF_R = 0.22
FROZEN_STANDOFF_R = 0.30
EQUIL_STANDOFF_R = FROZEN_STANDOFF_R * RHO_RATIO_FRZ / RHO_RATIO_EQU
V3_PRIMARY = 0.306          # from revalidate_hornung.py (V3 run)

# ---------------- FireII references ----------------
F_V = 10480.0
F_T = 276.0
F_RHO = 0.00059826 + 0.00018174     # rho_N2 + rho_O2 (frozen composition)
F_RHO_N2 = 0.00059826
F_RHO_O2 = 0.00018174
# FIRE II 1643 s trajectory point literature values:
#  - FIRE II flight test (Cauchon 1967), LAURA/HARA and FUN3D/HARA benchmarks
#  - Radiative stagnation heating at this point ~ 1 MW/m2 (100 W/cm2)
#  - Convective heating benchmark: Sutton-Graves / Anderson correlation
F_V = 10480.0
F_T = 276.0
F_RHO = 0.00059826 + 0.00018174     # rho_N2 + rho_O2 (frozen composition)
F_RHO_N2 = 0.00059826
F_RHO_O2 = 0.00018174
F_SG_K = 1.7415e-4          # Sutton-Graves constant (SI, Earth air): q[W/m2]
# FIRE II flight vehicle forebody sphere radius R_n = 0.9347 m (LAURA/FUN3D).
# The COOLFluiD testcase mesh (fire2_small80x.CFmesh, x1e-6 -> m) has a fitted
# spherical nose of R_n = 0.8433 m (circle fit on forebody wall nodes, rms
# 5e-4 m); both values are used for the Sutton-Graves reference band.
F_RN = 0.9347
F_RN_MESH = 0.8433
# Stagnation convective heating (Sutton-Graves)
F_Q_SG = F_SG_K * np.sqrt(F_RHO / F_RN) * F_V ** 3.0   # W/m2  (literature Rn)
F_Q_SG_MESH = F_SG_K * np.sqrt(F_RHO / F_RN_MESH) * F_V ** 3.0  # (mesh Rn)


def parse_plt(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    variables = None
    nodes = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('VARIABLES'):
            variables = re.findall(r'"([^"]+)"', line)
            if not variables:
                variables = line.replace('VARIABLES', '').split()
            i += 1
            continue
        if line.startswith('ZONE'):
            m = re.search(r'N=(\d+)', line)
            n = int(m.group(1))
            i += 1
            for _ in range(n):
                nodes.append([float(p) for p in lines[i].split()])
                i += 1
            break
        i += 1
    return variables, np.array(nodes)


def extract_stagline(variables, nodes, tol=1e-9):
    iy = variables.index('x1')
    ix = variables.index('x0')
    # cell-centred meshes have cell centres offset from y=0; try progressively
    # looser tolerances until enough points are captured.
    for t in (1e-9, 1e-6, 1e-4, 5e-4, 1e-3, 2e-3):
        mask = np.abs(nodes[:, iy]) < t
        if mask.sum() >= 8:
            break
    stag = nodes[mask]
    return stag[np.argsort(stag[:, ix])]


def hornung_v5():
    print('=' * 74)
    print('HORNUNG V5 (Euler2DNEQ n2_2, 50000 steps, final Res -2.39)')
    print('=' * 74)
    plt_file = os.path.join(V5_DIR, 'HornungN2.plt')
    variables, nodes = parse_plt(plt_file)
    print(f'Loaded {plt_file}: {len(nodes)} P0 states')
    x0 = nodes[:, variables.index('x0')]
    x1 = nodes[:, variables.index('x1')]
    T = nodes[:, variables.index('T')]
    rho = nodes[:, variables.index('rho')]
    print(f'  domain: x0 [{x0.min():.5f}, {x0.max():.5f}] m, '
          f'x1 [{x1.min():.5f}, {x1.max():.5f}] m')
    print(f'  T  range [{T.min():.1f}, {T.max():.1f}] K')
    print(f'  rho range [{rho.min():.6f}, {rho.max():.6f}] kg/m3')

    # ORIENTATION CHECK: where is the cylinder wall and where does the
    # shock sit?  Stagnation line = cells nearest y=0.
    stag = extract_stagline(variables, nodes, tol=1e-9)
    if len(stag) < 5:                       # looser tolerance
        stag = extract_stagline(variables, nodes, tol=1e-6)
    xs = stag[:, variables.index('x0')]
    Ts = stag[:, variables.index('T')]
    rhos = stag[:, variables.index('rho')]
    ps = stag[:, variables.index('p')]
    print(f'  stagnation line: {len(xs)} states, x [{xs.min():.5f}, {xs.max():.5f}]')
    i_wall = int(np.argmin(np.abs(xs) - CYL_R)) if False else None
    # wall = stagnation-line point closest to |x| = R
    i_wall = int(np.argmin(np.abs(np.abs(xs) - CYL_R)))
    print(f'  wall-nearest stag point: x={xs[i_wall]:.5f} m '
          f'(|x|-R={abs(xs[i_wall])-CYL_R:.5f} m) T={Ts[i_wall]:.0f} K '
          f'p={ps[i_wall]:.1f} Pa')
    # far-field point (largest |x - wall|)
    i_ff = int(np.argmax(np.abs(xs - xs[i_wall])))
    print(f'  far-field stag point: x={xs[i_ff]:.5f} m T={Ts[i_ff]:.0f} K '
          f'p={ps[i_ff]:.1f} Pa rho={rhos[i_ff]:.5f}')

    # Which side is freestream? freestream T ~ 1833 K. Shock = T spike.
    i_peak = int(np.argmax(Ts))
    print(f'  stag-line T peak: x={xs[i_peak]:.5f} m, T={Ts[i_peak]:.0f} K')
    # Determine the upstream direction from the peak: shock lies between
    # wall and freestream on the side where T descends to T_inf.
    if i_peak > i_wall:
        band = range(i_peak, len(xs) - 1)
        side = '+x'
    else:
        band = range(i_peak, 0, -1)
        side = '-x'
    # find freestream end of the shock band
    i_inf = i_peak
    for i in band:
        if Ts[i] < 1.02 * T_INF:
            i_inf = i
            break
    print(f'  freestream side: {side}; first cell within 2% of T_inf: '
          f'x={xs[i_inf]:.5f} m T={Ts[i_inf]:.0f} K')

    # standoff measured from wall
    d_mm_peak = (abs(xs[i_peak]) - CYL_R) * 1e3
    d_R_peak = (abs(xs[i_peak]) - CYL_R) / CYL_R
    band_mm = (abs(xs[i_inf]) - abs(xs[i_peak])) * 1e3
    print(f'  shock band (T peak -> freestream): {band_mm:.2f} mm '
          f'(~{abs(i_inf-i_peak)+1} cells)')
    print(f'  PRIMARY standoff (T-peak convention): delta/R = {d_R_peak:.4f} '
          f'({d_mm_peak:.3f} mm)')

    # density midpoint criterion inside band
    seg = np.linspace(i_peak, i_inf, abs(i_inf - i_peak) + 1).astype(int)
    f_post, f_ffm = rhos[i_peak], rhos[i_inf]
    f_mid = 0.5 * (f_post + f_ffm)
    x_mid = None
    rng = range(i_peak, i_inf) if i_inf > i_peak else range(i_peak, i_inf, -1)
    for i in rng:
        a, b = rhos[i], rhos[i + 1] if i_inf > i_peak else rhos[i - 1]
        aa, bb = (rhos[i], rhos[i + 1]) if i_inf > i_peak else (rhos[i], rhos[i - 1])
        if (aa - f_mid) * (bb - f_mid) <= 0:
            den = (aa - bb)
            frac = 0.0 if den == 0 else (aa - f_mid) / den
            xa = xs[i]
            xb = xs[i + 1] if i_inf > i_peak else xs[i - 1]
            x_mid = xa + frac * (xb - xa)
            break
    if x_mid is not None:
        d_R_rho = (abs(x_mid) - CYL_R) / CYL_R
        print(f'  density-midpoint standoff: delta/R = {d_R_rho:.4f}')

    primary = d_R_peak
    print('\n  --- comparison ---')
    print(f'  frozen limit delta/R ~ {FROZEN_STANDOFF_R:.2f} | '
          f'equilibrium ~ {EQUIL_STANDOFF_R:.2f} | experiment {EXP_STANDOFF_R:.2f}')
    print(f'  V3 primary (density midpoint) = {V3_PRIMARY:.3f}')
    err = 100 * (primary - EXP_STANDOFF_R) / EXP_STANDOFF_R
    print(f'  V5 primary (T-peak)           = {primary:.3f}  '
          f'({err:+.0f}% vs experiment)')

    # --- state check at post-shock / wall ---
    print(f'  CFD peak T = {Ts[i_peak]:.0f} K vs frozen RH {MPP_FRZ["T"]:.0f} K '
          f'({100*(Ts[i_peak]/MPP_FRZ["T"]-1):+.1f}%)')
    print(f'  CFD wall p = {ps[i_wall]/1e3:.2f} kPa vs equil {MPP_EQU["P"]/1e3:.1f} kPa '
          f'({100*(ps[i_wall]/MPP_EQU["P"]-1):+.1f}%)')

    # save summary
    with open(os.path.join(V5_DIR, 'hornung_v5_summary.txt'), 'w') as f:
        f.write('Hornung V5 summary (Euler2DNEQ n2_2, 50000 steps)\n')
        f.write(f'delta/R T-peak       = {primary:.4f}\n')
        if x_mid is not None:
            f.write(f'delta/R density-mid  = {d_R_rho:.4f}\n')
        f.write(f'T_peak               = {Ts[i_peak]:.1f} K\n')
        f.write(f'p_wall               = {ps[i_wall]:.1f} Pa\n')
        f.write(f'T_wall               = {Ts[i_wall]:.1f} K\n')
        f.write(f'shock band width     = {band_mm:.2f} mm\n')
    print(f'Saved {V5_DIR}/hornung_v5_summary.txt')

    # --- plot stagnation line ---
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    fig.suptitle('Hornung N2 cylinder V5 (50000 steps) -- stagnation line', fontsize=12)
    ax[0].plot(xs * 1e3, Ts, 'b.-', ms=4, lw=1.2)
    ax[0].axvline(-CYL_R * 1e3 if side == '-x' else CYL_R * 1e3,
                  color='k', ls='--', lw=0.8, label='wall')
    ax[0].axhline(MPP_FRZ['T'], color='gray', ls=':', label='frozen RH T')
    ax[0].axhline(T_INF, color='g', ls=':', label='T_inf')
    ax[0].set_xlabel('x [mm]'); ax[0].set_ylabel('T [K]')
    ax[0].set_title('(a) Temperature'); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)

    ax[1].plot(xs * 1e3, rhos / RHO_INF, 'k.-', ms=4, lw=1.2)
    ax[1].set_xlabel('x [mm]'); ax[1].set_ylabel('rho/rho_inf')
    ax[1].set_title('(b) Density ratio'); ax[1].grid(alpha=0.3)

    ax[2].axhline(FROZEN_STANDOFF_R, color='k', ls='--', label='frozen ~0.30')
    ax[2].axhline(EQUIL_STANDOFF_R, color='k', ls=':', label='equilibrium ~0.17')
    ax[2].plot([0], [EXP_STANDOFF_R], 'r^', ms=11, label='Hornung exp 0.22')
    ax[2].plot([1], [V3_PRIMARY], 'cs', ms=11, label='V3 (0.306)')
    ax[2].plot([2], [primary], 'bo', ms=11, label=f'V5 ({primary:.3f})')
    ax[2].set_xticks([]); ax[2].set_ylabel('delta/R')
    ax[2].set_title('(c) Shock stand-off'); ax[2].legend(fontsize=8)
    ax[2].grid(axis='y', alpha=0.3)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(DOC, 'hornung_v5_stagline.png')
    plt.savefig(out, dpi=150); plt.close()
    print(f'Saved {out}')
    return primary, d_R_rho if x_mid is not None else None, Ts[i_peak], ps[i_wall]


def parse_cfmesh_states(filepath):
    """Parse a COOLFluiD ASCII CFmesh: return cell centres and Rhoivt states.

    The FireII restart mesh has NB_EQ=14 (11 species rho + u v T).
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    hdr = {}
    for l in lines:
        if not l.startswith('!'):
            break
        tok = l.split()
        hdr[tok[0].lstrip('!')] = tok[1:]
    nb_nodes = int(hdr['NB_NODES'][0])
    nb_states = int(hdr['NB_STATES'][0])
    nb_elem = int(hdr['NB_ELEM'][0])
    nb_eq = int(hdr['NB_EQ'][0])
    sec = {}
    cur = None
    for l in lines:
        if l.startswith('!'):
            cur = l.split()[0].lstrip('!')
            sec[cur] = []
            continue
        if cur:
            sec[cur].append(l)
    X = np.empty((nb_nodes, 2))
    for i, l in enumerate(sec['LIST_NODE'][:nb_nodes]):
        p = l.split()
        X[i] = float(p[0]), float(p[1])
    S = np.empty((nb_states, nb_eq))
    for i, l in enumerate(sec['LIST_STATE'][:nb_states]):
        p = l.split()
        S[i] = [float(q) for q in p[:nb_eq]]
    E = np.empty((nb_elem, 5), dtype=int)
    for i, l in enumerate(sec['LIST_ELEM'][:nb_elem]):
        p = l.split()
        E[i] = [int(q) for q in p[:5]]
    cen = X[E[:, :4]].mean(axis=1)          # cell centres
    sid = E[:, 4]                            # state id per cell
    return cen, S[sid]


def fireii_frozen():
    print()
    print('=' * 74)
    print('FIRE II 1643 s FROZEN phase (state read from restart mesh iter_1000)')
    print('=' * 74)
    mesh_file = os.path.join(FRZ_DIR, 'fire2-iter_1000.CFmesh')
    if not os.path.exists(mesh_file):
        mesh_file = os.path.join(os.path.dirname(FRZ_DIR),
                                 'plugins/NEQ/testcases/TCNEQ/FireII/'
                                 'RESULT_FIREII_FROZEN/fire2-iter_1000.CFmesh')
    cen, S = parse_cfmesh_states(mesh_file)
    print(f'Loaded {mesh_file}: {len(S)} cell states (Rhoivt, 11 species)')
    T = S[:, 13]
    u = S[:, 11]
    rho = S[:, :11].sum(axis=1)
    print(f'  domain: x0 [{cen[:,0].min():.4f}, {cen[:,0].max():.4f}] m, '
          f'x1 [{cen[:,1].min():.4f}, {cen[:,1].max():.4f}] m')
    print(f'  T range [{T.min():.1f}, {T.max():.1f}] K   '
          f'u range [{u.min():.1f}, {u.max():.1f}] m/s')
    print(f'  rho range [{rho.min():.3e}, {rho.max():.3e}] kg/m3')
    hot = T > 1e5
    print(f'  overshoot cells (T>1e5 K): {int(hot.sum())} '
          f'({100*hot.mean():.2f}% of domain)')
    # stagnation line (|y| small; first cell-centre row sits at y~0.0086 m)
    for tol in (1e-3, 5e-3, 0.012, 0.02):
        m = np.abs(cen[:, 1]) < tol
        if m.sum() >= 10:
            break
    o = np.argsort(cen[m, 0])
    xs = cen[m, 0][o]
    Ts = T[m][o]
    us = u[m][o]
    print(f'  stag line ({int(m.sum())} cells, |y|<{tol:g} m)')
    i_wall = int(np.argmin(Ts))
    i_ff = int(np.argmax(us))
    i_peak = int(np.argmax(Ts))
    d_R = abs(xs[i_peak] - xs[i_wall]) / F_RN_MESH
    print(f'  wall: x={xs[i_wall]:.4f} T={Ts[i_wall]:.0f} K | '
          f'freestream: x={xs[i_ff]:.4f} u={us[i_ff]:.0f} m/s | '
          f'T peak: x={xs[i_peak]:.4f} T={Ts[i_peak]:.0f} K delta/Rn={d_R:.3f}')
    # frozen normal-shock stagnation temperature (gamma=1.4)
    g = 1.4
    a = np.sqrt(g * 287.05 * F_T)
    M = F_V / a
    T0_frozen = F_T * (1 + 0.5 * (g - 1) * M ** 2)
    print(f'  [ref] frozen ideal-gas stagnation T = {T0_frozen:.0f} K '
          f'(M={M:.1f}); CFD layer T max (excl. overshoot) = '
          f'{T[~hot].max():.0f} K')
    print(f'  [ref] Sutton-Graves q_s = {F_Q_SG/1e4:.0f} W/cm2 (lit. Rn) | '
          f'{F_Q_SG_MESH/1e4:.0f} W/cm2 (mesh Rn)')

    # plot
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    fig.suptitle('FIRE II 1643 s frozen phase (restart state iter_1000) -- '
                 'stagnation line', fontsize=12)
    ax[0].plot(xs * 1e3, Ts, 'b.-', ms=4, lw=1.2)
    ax[0].axhline(640, color='k', ls='--', label='T_wall=640')
    ax[0].axhline(F_T, color='g', ls=':', label='T_inf=276')
    ax[0].set_xlabel('x [mm]'); ax[0].set_ylabel('T [K]')
    ax[0].set_title('(a) Temperature'); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)

    ax[1].plot(xs * 1e3, us / 1e3, 'b.-', ms=4, lw=1.2)
    ax[1].axhline(F_V / 1e3, color='g', ls=':', label='V_inf=10.48 km/s')
    ax[1].set_xlabel('x [mm]'); ax[1].set_ylabel('u [km/s]')
    ax[1].set_title('(b) Velocity'); ax[1].legend(fontsize=7); ax[1].grid(alpha=0.3)

    ax[2].plot(xs * 1e3, rho[m][o] / F_RHO, 'k.-', ms=4, lw=1.2)
    ax[2].set_xlabel('x [mm]'); ax[2].set_ylabel('rho/rho_inf')
    ax[2].set_title('(c) Density ratio'); ax[2].grid(alpha=0.3)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(DOC, 'fireii_frozen_stagline.png')
    plt.savefig(out, dpi=150); plt.close()
    print(f'Saved {out}')


def fireii_chem():
    print()
    print('=' * 74)
    print('FIRE II 1643 s CHEMISTRY (NavierStokes2DNEQ air_11, restart from frozen)')
    print('=' * 74)
    plt_file = os.path.join(CHEM_DIR, 'fire2.plt')
    if not os.path.exists(plt_file):
        print(f'  {plt_file} not found -- chemistry run not finished yet?')
        return
    variables, nodes = parse_plt(plt_file)
    print(f'Loaded {plt_file}: {len(nodes)} P0 states')
    nan_mask = ~np.isfinite(nodes).all(axis=1)
    print(f'  NaN/Inf states: {int(nan_mask.sum())}')

    x0 = nodes[:, variables.index('x0')]
    x1 = nodes[:, variables.index('x1')]
    T = nodes[:, variables.index('T')]
    rho = nodes[:, variables.index('rho')]
    u = nodes[:, variables.index('u')]
    p = nodes[:, variables.index('p')]
    print(f'  domain: x0 [{x0.min():.4f}, {x0.max():.4f}] m, '
          f'x1 [{x1.min():.4f}, {x1.max():.4f}] m')
    print(f'  T range [{T.min():.1f}, {T.max():.1f}] K   '
          f'rho range [{rho.min():.3e}, {rho.max():.3e}] kg/m3')
    print(f'  p range [{p.min():.2f}, {p.max():.2f}] Pa')

    # species check: rho0=N2, rho1=O2 (air_11 ordering N2 O2 N O NO ...)
    rhoN2 = nodes[:, variables.index('rho0')]
    rhoO2 = nodes[:, variables.index('rho1')]
    yN2 = rhoN2 / rho
    yO2 = rhoO2 / rho
    i_maxT = int(np.argmax(T))
    print(f'  max-T state: T={T[i_maxT]:.0f} K, yN2={yN2[i_maxT]:.4f} '
          f'(freestream {F_RHO_N2/F_RHO:.4f}), yO2={yO2[i_maxT]:.4f} '
          f'(freestream {F_RHO_O2/F_RHO:.4f})')

    # stagnation line
    stag = extract_stagline(variables, nodes, tol=1e-9)
    if len(stag) < 5:
        stag = extract_stagline(variables, nodes, tol=1e-6)
    xs = stag[:, variables.index('x0')]
    Ts = stag[:, variables.index('T')]
    us = stag[:, variables.index('u')]
    print(f'  stag line: {len(xs)} states, x [{xs.min():.4f}, {xs.max():.4f}] m')
    i_wall = int(np.argmin(np.abs(Ts - 640.)))
    i_ff = int(np.argmax(us))
    i_peak = int(np.argmax(Ts))
    d_R = abs(xs[i_peak] - xs[i_wall]) / F_RN
    print(f'  wall-nearest stag point: x={xs[i_wall]:.4f} T={Ts[i_wall]:.1f} K')
    print(f'  freestream stag point:  x={xs[i_ff]:.4f} T={Ts[i_ff]:.1f} K '
          f'u={us[i_ff]:.1f} m/s')
    print(f'  stag T peak: x={xs[i_peak]:.4f} T={Ts[i_peak]:.0f} K  '
          f'delta/Rn ~ {d_R:.3f}')

    # --- wall heat flux ---
    wfile = os.path.join(CHEM_DIR, 'wall.plt-P0Wall')
    q_stag = None
    if os.path.exists(wfile):
        w = np.loadtxt(wfile, skiprows=2)
        heatF = w[:, 6]
        Pw = w[:, 2]
        Tw = w[:, 3]
        print(f'  wall file: {len(w)} points, P [{Pw.min():.1f}, {Pw.max():.1f}] Pa, '
              f'T [{Tw.min():.0f}, {Tw.max():.0f}] K')
        i_stag = int(np.argmax(np.abs(Pw)))
        q_stag = heatF[i_stag]
        print(f'  wall heatF range [{heatF.min():.3e}, {heatF.max():.3e}] W/m2')
        print(f'  STAGNATION heat flux (max-P point, P={Pw[i_stag]:.1f} Pa): '
              f'{q_stag:.4e} W/m2 = {q_stag/1e4:.1f} W/cm2')

    # --- comparisons ---
    print(f'\n  Sutton-Graves q_s: {F_Q_SG:.4e} W/m2 = {F_Q_SG/1e4:.1f} W/cm2 '
          f'(literature R_n={F_RN} m)')
    print(f'  Sutton-Graves q_s: {F_Q_SG_MESH:.4e} W/m2 = {F_Q_SG_MESH/1e4:.1f} W/cm2 '
          f'(mesh-fitted R_n={F_RN_MESH} m)')
    if q_stag is not None and F_Q_SG > 0:
        print(f'  CFD/SG ratio: {q_stag/F_Q_SG:.3f} (lit. Rn) | '
              f'{q_stag/F_Q_SG_MESH:.3f} (mesh Rn)')
    # literature anchors for FIRE II 1643 s stagnation heating
    print('  [ref] LAURA/FUN3D convective stagnation heating at 1643 s ~ 6 MW/m2')
    print('        (fully catalytic wall, HARA radiance-calibrated trajectory);')
    print('        radiative ~ 1 MW/m2 (Park 2004 non-Boltzmann reanalysis)')

    # --- save summary + plot ---
    with open(os.path.join(CHEM_DIR, 'fireii_chem_summary.txt'), 'w') as f:
        f.write('FIRE II 1643 s chemistry-restart summary\n')
        f.write(f'T_stag_peak      = {Ts[i_peak]:.1f} K\n')
        f.write(f'delta/Rn         = {d_R:.4f}\n')
        if q_stag is not None:
            f.write(f'q_conv_stag      = {q_stag:.4e} W/m2\n')
            f.write(f'q_conv_stag      = {q_stag/1e4:.2f} W/cm2\n')
            f.write(f'q_SG_litRn       = {F_Q_SG:.4e} W/m2 (Rn={F_RN} m)\n')
            f.write(f'q_SG_meshRn      = {F_Q_SG_MESH:.4e} W/m2 (Rn={F_RN_MESH} m)\n')
            f.write(f'ratio CFD/SG(lit)  = {q_stag/F_Q_SG:.3f}\n')
            f.write(f'ratio CFD/SG(mesh) = {q_stag/F_Q_SG_MESH:.3f}\n')
        f.write(f'p_stag_wall      = {Pw.max() if os.path.exists(wfile) else float("nan"):.1f} Pa\n')
    print(f'Saved {CHEM_DIR}/fireii_chem_summary.txt')

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    fig.suptitle('FIRE II 1643 s chemistry restart -- stagnation line', fontsize=12)
    ax[0].plot(xs, Ts, 'b.-', ms=4, lw=1.2)
    ax[0].axhline(640, color='k', ls='--', label='T_wall=640')
    ax[0].axhline(F_T, color='g', ls=':', label='T_inf=276')
    ax[0].set_xlabel('x [m]'); ax[0].set_ylabel('T [K]')
    ax[0].set_title('(a) Temperature'); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)

    ax[1].plot(xs, stag[:, variables.index('rho0')] / stag[:, variables.index('rho')],
               'r.-', ms=4, lw=1.2, label='y_N2')
    ax[1].plot(xs, stag[:, variables.index('rho1')] / stag[:, variables.index('rho')],
               'b.-', ms=4, lw=1.2, label='y_O2')
    ax[1].set_xlabel('x [m]'); ax[1].set_ylabel('mass fraction')
    ax[1].set_title('(b) Species (chemistry active)'); ax[1].legend(fontsize=7)
    ax[1].grid(alpha=0.3)

    if os.path.exists(wfile):
        w2 = np.loadtxt(wfile, skiprows=2)
        xw = w2[:, 0]
        hw = w2[:, 6]
        order = np.argsort(xw)
        ax[2].plot(xw[order] * 1e3, hw[order] / 1e4, 'k.-', ms=4, lw=1.2)
        ax[2].axhline(F_Q_SG_MESH / 1e4, color='r', ls='--',
                      label=f'Sutton-Graves {F_Q_SG_MESH/1e4:.0f} W/cm2 (mesh Rn)')
        ax[2].axhline(F_Q_SG / 1e4, color='r', ls=':',
                      label=f'Sutton-Graves {F_Q_SG/1e4:.0f} W/cm2 (lit. Rn)')
        ax[2].set_xlabel('x [mm]'); ax[2].set_ylabel('q [W/cm2]')
        ax[2].set_title('(c) Wall heat flux'); ax[2].legend(fontsize=7)
        ax[2].grid(alpha=0.3)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(DOC, 'fireii_chem_stagline.png')
    plt.savefig(out, dpi=150); plt.close()
    print(f'Saved {out}')


if __name__ == '__main__':
    hornung_v5()
    fireii_frozen()
    fireii_chem()
