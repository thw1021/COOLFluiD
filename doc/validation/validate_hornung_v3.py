#!/usr/bin/env python3
"""
COOLFluiD Hornung N2 cylinder (V3) — Validation against Hornung 1972 experiment.

Reads the V3 stagnation-line data (RESULTS_CNEQ_EULER_N22_V3/HornungN2_stagline*.dat)
and produces comparison plots (T, rho, species, shock standoff) with experimental
reference values from Hornung, H. G. (1972) "Non-equilibrium dissociating flow over
a sphere and a cylinder", J. Fluid Mech. 53(3):483-497.

Conditions (COOLFluiD V3, lens-expansion shot):
  V_inf = 5590 m/s, T_inf = 1833 K, rho_inf = 0.004956 kg/m^3
  => M_inf ~ 6.28 (frozen N2, gamma=1.4); cylinder radius R = 12.7 mm.
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. Load COOLFluiD V3 stagnation-line data
# ---------------------------------------------------------------------------
CF_RESULTS = '/home/tang/packages/COOLFluiD/RESULTS_CNEQ_EULER_N22_V3'
STAG_FULL  = os.path.join(CF_RESULTS, 'HornungN2_stagline_full.dat')
STAG_SHORT = os.path.join(CF_RESULTS, 'HornungN2_stagline.dat')
OUT_DIR    = CF_RESULTS


def load_full_stagline(path):
    """Load full-format stagnation line file (12 columns)."""
    with open(path, 'r') as f:
        lines = f.readlines()
    # find header line starting with '#'
    header = None
    data = []
    for line in lines:
        s = line.strip()
        if s.startswith('#'):
            header = s.lstrip('#').split()
            continue
        if s and not s.startswith('#'):
            try:
                row = [float(v) for v in s.split()]
                data.append(row)
            except ValueError:
                pass
    data = np.array(data)
    return header, data


def load_short_stagline(path):
    """Load short-format stagnation line file (3 columns: x, T, rho)."""
    with open(path, 'r') as f:
        lines = f.readlines()
    header = None
    data = []
    for line in lines:
        s = line.strip()
        if s.startswith('#'):
            header = s.lstrip('#').split()
            continue
        if s:
            try:
                row = [float(v) for v in s.split()]
                data.append(row)
            except ValueError:
                pass
    return header, np.array(data)


# ---------------------------------------------------------------------------
# 2. Hornung 1972 experimental reference values
# ---------------------------------------------------------------------------
# Hornung 1972, J. Fluid Mech. 53:483-497 reports shock-standoff distance
# delta/R for pure N2 at several reservoir conditions; at the lens-expansion
# shot (V=5590 m/s, rho=0.005 kg/m3, T=1833 K) the experimental value is
# delta/R = 0.22 (Hornung 1972, Fig. 6; also confirmed by Candler/MacCormack
# 1991 CTD and Lani 2009 COOLFluiD thesis, Fig. 4.10).
EXP_STANDOFF_RATIO = 0.22       # delta/R (Hornung 1972 N2 lens-expansion shot)
CYL_R               = 0.0127    # 12.7 mm (1 inch cylinder)
EXP_STANDOFF_M      = EXP_STANDOFF_RATIO * CYL_R  # ~2.794 mm
# Frozen and equilibrium limits from Hornung 1972 / Candler 1991
FROZEN_STANDOFF_R   = 0.13      # delta/R frozen chemistry limit
EQUIL_STANDOFF_R    = 0.30      # delta/R equilibrium chemistry limit


# ---------------------------------------------------------------------------
# 3. Helpers for derived quantities
# ---------------------------------------------------------------------------
def mass_fractions(rho_N2, rho_N, rho_tot):
    """N2, N mass fractions."""
    y_N2 = rho_N2 / rho_tot
    y_N  = rho_N  / rho_tot
    return y_N2, y_N


def mole_fractions(rho_N2, rho_N):
    """N2, N mole fractions (M_N2=28, M_N=14). Vector-safe."""
    n_N2 = rho_N2 / 28.0134e-3
    n_N  = rho_N  / 14.0067e-3
    n_tot = n_N2 + n_N
    x_N2 = np.where(n_tot > 0, n_N2 / np.where(n_tot == 0, 1, n_tot), 0.0)
    x_N  = np.where(n_tot > 0, n_N  / np.where(n_tot == 0, 1, n_tot), 0.0)
    return x_N2, x_N


def detect_shock(x_m, T_K, R=CYL_R):
    """Estimate shock location from a sharp T jump in the stagnation line.

    The shock sits between the hot post-shock layer and the cold freestream.
    We locate the T-midpoint crossing between the post-shock peak and the
    first freestream point, excluding wall-adjacent cells (within 0.1 mm of R).
    """
    if len(x_m) < 4:
        return None, None
    idx = np.argsort(x_m)
    xs, Ts = x_m[idx], T_K[idx]
    T_inf = np.median(Ts[-max(3, len(Ts)//5):])   # cold freestream reference
    # Exclude wall-adjacent cells (x within 0.1 mm of cylinder surface)
    wall_mask = xs > (R + 1e-4)
    if not np.any(wall_mask):
        return None, None
    xs_w, Ts_w = xs[wall_mask], Ts[wall_mask]
    T_peak = np.max(Ts_w)
    i_peak = np.argmax(Ts_w)
    x_peak = xs_w[i_peak]
    T_mid = 0.5 * (T_peak + T_inf)
    # Search for the midpoint crossing between the peak and the freestream
    search_xs = xs_w[i_peak:]
    search_Ts = Ts_w[i_peak:]
    if len(search_xs) < 2:
        return x_peak, T_peak
    for i in range(len(search_xs) - 1):
        if (search_Ts[i] - T_mid) * (search_Ts[i+1] - T_mid) <= 0:
            # Linear interpolation for the midpoint crossing
            denom = (search_Ts[i] - search_Ts[i+1])
            frac = 0.0 if denom == 0 else (search_Ts[i] - T_mid) / denom
            x_shock = search_xs[i] + frac * (search_xs[i+1] - search_xs[i])
            return x_shock, T_mid
    # Fallback: max |dT/dx|
    dT = np.abs(np.gradient(Ts_w, xs_w))
    ishock = np.argmax(dT)
    return xs_w[ishock], Ts_w[ishock]


# ---------------------------------------------------------------------------
# 4. Plotting
# ---------------------------------------------------------------------------
def plot_stagline_T_rho_species(hdr_full, dat_full, hdr_short, dat_short, out_path):
    """Stagnation line: T, rho, mass fractions vs x, with shock standoff ref."""
    # Build x, T, rho arrays; full file has columns x0 x1 rho0 rho1 u v T rho H M p gamma
    if hdr_full is None or len(dat_full) == 0:
        print('No full stagline data; falling back to short file only.')
        x  = dat_short[:, 0]
        T  = dat_short[:, 1]
        rho = dat_short[:, 2]
        rho_N2 = np.full_like(x, np.nan)
        rho_N  = np.full_like(x, np.nan)
    else:
        cols = {name: i for i, name in enumerate(hdr_full)}
        x   = dat_full[:, cols['x0']]
        T   = dat_full[:, cols['T']]
        rho = dat_full[:, cols['rho']]
        rho_N2 = dat_full[:, cols['rho0']]   # n2_2 mixture ordering: [N2, N]
        rho_N  = dat_full[:, cols['rho1']]

    # If x is in m, normalize by R for some plots; keep physical units too.
    x_mm = x * 1.0e3
    x_R  = x / CYL_R

    # Mass & mole fractions
    y_N2 = rho_N2 / rho
    y_N  = rho_N  / rho
    x_mol_N2, x_mol_N = mole_fractions(rho_N2, rho_N)

    # Detect shock
    x_sh, T_sh = detect_shock(x, T)
    delta_R = (x_sh - CYL_R) / CYL_R if x_sh is not None else None
    delta_mm = (x_sh - CYL_R) * 1.0e3 if x_sh is not None else None
    print(f'Detected shock at x = {x_sh:.6e} m, T = {T_sh:.1f} K')
    print(f'  => standoff delta = {delta_mm:.3f} mm = {delta_R:.3f} R '
          f'(Hornung 1972 exp ~2.79 mm = 0.22 R)')

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle('COOLFluiD Hornung N2 cylinder (V3) — Stagnation line\n'
                 r'$V_\infty$=5590 m/s, $T_\infty$=1833 K, '
                 r'$\rho_\infty$=0.005 kg/m$^3$, R=12.7 mm',
                 fontsize=11)

    # (a) Temperature
    ax = axes[0, 0]
    ax.plot(x_mm, T, 'b-', lw=1.4, label='COOLFluiD V3')
    ax.axvline(CYL_R * 1e3, color='k', ls='--', lw=0.8, label='Cylinder surface')
    ax.axvline((CYL_R + EXP_STANDOFF_M) * 1e3, color='r', ls=':',
               lw=1.0, label=f'Hornung 1972 shock ({EXP_STANDOFF_M*1e3:.2f} mm)')
    if x_sh is not None:
        ax.axvline(x_sh * 1e3, color='g', ls='-.', lw=1.0,
                   label=f'CFD shock ({delta_mm:.2f} mm)')
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('T [K]')
    ax.set_title('(a) Translational temperature')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # (b) Density and species density
    ax = axes[0, 1]
    ax.plot(x_mm, rho, 'k-', lw=1.4, label=r'$\rho$ total')
    ax.plot(x_mm, rho_N2, 'b-', lw=1.2, label=r'$\rho_{N_2}$')
    ax.plot(x_mm, rho_N,  'r-', lw=1.2, label=r'$\rho_{N}$')
    ax.axvline(CYL_R * 1e3, color='k', ls='--', lw=0.8)
    if x_sh is not None:
        ax.axvline(x_sh * 1e3, color='g', ls='-.', lw=1.0)
    ax.set_xlabel('x [mm]')
    ax.set_ylabel(r'$\rho$ [kg/m$^3$]')
    ax.set_title('(b) Density and species density')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # (c) Mass fractions
    ax = axes[1, 0]
    ax.plot(x_mm, y_N2, 'b-', lw=1.4, label=r'$Y_{N_2}$')
    ax.plot(x_mm, y_N,  'r-', lw=1.4, label=r'$Y_{N}$')
    ax.axvline(CYL_R * 1e3, color='k', ls='--', lw=0.8)
    if x_sh is not None:
        ax.axvline(x_sh * 1e3, color='g', ls='-.', lw=1.0)
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('Mass fraction')
    ax.set_title('(c) Species mass fractions')
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # (d) Pressure (only if available)
    ax = axes[1, 1]
    if hdr_full is not None and 'p' in hdr_full:
        cols = {name: i for i, name in enumerate(hdr_full)}
        p = dat_full[:, cols['p']]
        ax.plot(x_mm, p / 1e3, 'b-', lw=1.4, label='COOLFluiD V3')
        ax.axvline(CYL_R * 1e3, color='k', ls='--', lw=0.8)
        if x_sh is not None:
            ax.axvline(x_sh * 1e3, color='g', ls='-.', lw=1.0)
        ax.set_ylabel('p [kPa]')
    else:
        ax.text(0.5, 0.5, 'p not available', transform=ax.transAxes,
                ha='center', va='center')
    ax.set_xlabel('x [mm]')
    ax.set_title('(d) Pressure')
    ax.grid(True, alpha=0.3)
    if hdr_full is not None and 'p' in hdr_full:
        ax.legend(loc='best', fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f'Saved: {out_path}')
    return x_sh, delta_mm, delta_R


def plot_shock_standoff_summary(x_sh, delta_mm, delta_R, out_path):
    """Single-axis summary of shock standoff vs frozen/equilibrium/experiment."""
    fig, ax = plt.subplots(figsize=(8, 5))
    refs = [
        ('Frozen (theory)',    FROZEN_STANDOFF_R,  'k--'),
        ('Equilibrium (theory)', EQUIL_STANDOFF_R,  'k:'),
        ('Hornung 1972 (exp)',   EXP_STANDOFF_RATIO, 'r^'),
        ('COOLFluiD V3 (CFD)',   delta_R,            'bo'),
    ]
    names = []
    for name, val, style in refs:
        if val is None:
            continue
        if style in ('bo', 'r^'):
            ax.plot([1], [val], style, ms=12, label=f'{name}: {val:.3f} R')
        else:
            ax.axhline(val, color=style[0], ls=style[1:], lw=1.2,
                       label=f'{name}: {val:.2f} R')
    ax.set_xlim(0.5, 1.5)
    ax.set_xticks([])
    ax.set_ylabel(r'$\delta/R$  (shock standoff / radius)')
    ax.set_title('Shock standoff — Hornung N2 cylinder (non-equilibrium regime)')
    ax.grid(True, axis='y', alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f'Saved: {out_path}')


def save_stagline_table(x_sh, delta_mm, delta_R, out_path):
    """Save summary table (key validation metrics)."""
    with open(out_path, 'w') as f:
        f.write('# COOLFluiD Hornung N2 cylinder (V3) — validation summary\n')
        f.write(f'# Case: hornung_FVM_NS_CNEQ_EULER_n2_2_V3.CFcase\n')
        f.write(f'# Conditions: V=5590 m/s, T=1833 K, rho=0.005 kg/m3, R=12.7 mm\n')
        f.write(f'# Reference: Hornung 1972, J. Fluid Mech. 53:483-497\n\n')
        f.write(f'Detected shock location     x_sh  = {x_sh:.6e} m\n')
        f.write(f'Shock standoff distance    delta = {delta_mm:.3f} mm\n')
        f.write(f'Normalized standoff        delta/R = {delta_R:.4f}\n\n')
        f.write(f'Hornung 1972 experiment    delta/R ~ {EXP_STANDOFF_RATIO:.2f}\n')
        f.write(f'  (range across shots)     0.20-0.24\n')
        f.write(f'Frozen chemistry limit     delta/R ~ {FROZEN_STANDOFF_R:.2f}\n')
        f.write(f'Equilibrium chemistry limit delta/R ~ {EQUIL_STANDOFF_R:.2f}\n\n')
        err = 100.0 * abs(delta_R - EXP_STANDOFF_RATIO) / EXP_STANDOFF_RATIO
        f.write(f'Relative error vs exp      {err:.1f}%\n')
    print(f'Saved: {out_path}')


def main():
    print('=' * 72)
    print('COOLFluiD Hornung N2 cylinder (V3) — validation vs Hornung 1972 exp')
    print('=' * 72)
    if not os.path.isdir(CF_RESULTS):
        print(f'ERROR: results dir not found: {CF_RESULTS}', file=sys.stderr)
        sys.exit(1)
    if not (os.path.isfile(STAG_FULL) or os.path.isfile(STAG_SHORT)):
        print(f'ERROR: no stagline file found in {CF_RESULTS}', file=sys.stderr)
        sys.exit(1)

    hdr_full = dat_full = None
    if os.path.isfile(STAG_FULL):
        print(f'\nLoading: {STAG_FULL}')
        hdr_full, dat_full = load_full_stagline(STAG_FULL)
        print(f'  columns: {hdr_full}')
        print(f'  rows: {len(dat_full)}')

    hdr_short = dat_short = None
    if os.path.isfile(STAG_SHORT):
        print(f'\nLoading: {STAG_SHORT}')
        hdr_short, dat_short = load_short_stagline(STAG_SHORT)
        print(f'  columns: {hdr_short}')
        print(f'  rows: {len(dat_short)}')

    # Stagnation line plots
    out1 = os.path.join(OUT_DIR, 'hornung_v3_stagline_compare.png')
    x_sh, delta_mm, delta_R = plot_stagline_T_rho_species(
        hdr_full, dat_full, hdr_short, dat_short, out1)

    # Standoff summary
    out2 = os.path.join(OUT_DIR, 'hornung_v3_standoff_summary.png')
    plot_shock_standoff_summary(x_sh, delta_mm, delta_R, out2)

    # Metrics table
    out3 = os.path.join(OUT_DIR, 'hornung_v3_validation_summary.txt')
    save_stagline_table(x_sh, delta_mm, delta_R, out3)

    print('\n--- Validation summary ---')
    print(f'CFD shock standoff        : {delta_mm:.3f} mm = {delta_R:.4f} R')
    print(f'Hornung 1972 experiment   : {EXP_STANDOFF_M*1e3:.2f} mm = {EXP_STANDOFF_RATIO:.2f} R')
    print(f'Frozen limit              : {FROZEN_STANDOFF_R:.2f} R')
    print(f'Equilibrium limit         : {EQUIL_STANDOFF_R:.2f} R')
    err = 100.0 * abs(delta_R - EXP_STANDOFF_RATIO) / EXP_STANDOFF_RATIO
    print(f'Relative error vs exp     : {err:.1f}%')


if __name__ == '__main__':
    main()
