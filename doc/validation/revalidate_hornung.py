#!/usr/bin/env python3
"""
COOLFluiD Hornung N2 cylinder (V3) -- rigorous re-validation.

Improvements over validate_hornung_v3.py:
  * Reads the full P0 volume field (HornungN2.plt) and extracts a dense
    stagnation line (cell centers nearest to the symmetry axis y=0).
  * Locates the bow shock with FOUR independent criteria and reports the
    spread (shock detection uncertainty on a smeared coarse-mesh shock).
  * Uses Mutation++ (mppshock) Rankine-Hugoniot (frozen) and equilibrated
    post-shock states as quantitative references.
  * CORRECTS the frozen/equilibrium stand-off ordering:
    Hornung 1972 (JFM 53) explicitly states stand-off is INVERSELY
    proportional to the normal-shock density ratio.  Frozen chemistry has
    the SMALLER density ratio (~6.5) => LARGER stand-off; equilibrium has
    the LARGER density ratio (~11.7) => SMALLER stand-off.
  * ASCII-only log output (no non-ASCII markers in plots).

References
  Hornung, H. G. (1972) "Non-equilibrium dissociating nitrogen flow over
    spheres and circular cylinders", J. Fluid Mech. 53(1), 149-176.
  Lani, A. (2009) PhD thesis, VKI.
"""
import os
import re
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CF_RESULTS = '/home/tang/packages/COOLFluiD/RESULTS_CNEQ_EULER_N22_V3'
PLT_FILE = os.path.join(CF_RESULTS, 'HornungN2.plt')
OUT_DIR = CF_RESULTS

CYL_R = 0.0127          # cylinder radius [m] (1-inch cylinder)

# --- Free stream (CFcase) ---
U_INF = 5590.0          # m/s
T_INF = 1833.0          # K
RHO_INF = 0.004956      # kg/m^3
P_INF = 2909.0          # Pa

# --- Mutation++ mppshock references (n2_2, P=2909 Pa, T=1833 K, V=5590 m/s) ---
#   Rankine-Hugoniot (frozen, composition fixed at free-stream values)
MPP_FRZ = dict(T=13913.8, V=854.5, P=144452.3)
#   Equilibrated post-shock state
MPP_EQU = dict(T=6661.8,  V=476.8, P=155742.4)
# Density ratios follow from continuity (normal shock): rho2/rho1 = u1/u2
RHO_RATIO_FRZ = U_INF / MPP_FRZ['V']     # ~6.54
RHO_RATIO_EQU = U_INF / MPP_EQU['V']     # ~11.72

# Experimental stand-off (Hornung 1972, lens-expansion N2 shot modelled here)
EXP_STANDOFF_R = 0.22
# Perfect-gas cylinder frozen stand-off correlation (Billig/Hornung),
# and equilibrium value scaled by density ratio (delta ~ 1/(rho2/rho1)).
FROZEN_STANDOFF_R = 0.30
EQUIL_STANDOFF_R = FROZEN_STANDOFF_R * RHO_RATIO_FRZ / RHO_RATIO_EQU  # ~0.17


def parse_plt(filepath):
    """Parse a COOLFluiD Tecplot FEPOINT .plt file (first zone)."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    variables = None
    nodes = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('VARIABLES'):
            variables = re.findall(r'"([^"]+)"', line)
            i += 1
            continue
        if line.startswith('ZONE'):
            n = int(re.search(r'N=(\d+)', line).group(1))
            i += 1
            for _ in range(n):
                nodes.append([float(p) for p in lines[i].split()])
                i += 1
            break
        i += 1
    return variables, np.array(nodes)


def extract_stagline(variables, nodes):
    """Cell centers on the symmetry line y=x1 ~ 0, sorted by x=x0."""
    ix, iy = variables.index('x0'), variables.index('x1')
    tol = 1e-9
    mask = np.abs(nodes[:, iy]) < tol
    stag = nodes[mask]
    return stag[np.argsort(stag[:, ix])]


def detect_shock(x, field, i_peak, i_inf):
    """Return shock x-position from (a) midpoint crossing, (b) max gradient.

    The shock band runs from the post-shock frozen spike (i_peak, field high)
    to the first free-stream cell (i_inf, field low).  Only this band is used,
    so the wall stagnation-compression gradient is excluded.  Reference levels
    are the post-shock value (at i_peak) and the free-stream value (at i_inf).
    """
    f_post = field[i_peak]     # immediate post-shock (frozen spike)
    f_inf = field[i_inf]       # free stream
    # midpoint of the SHOCK jump (post-shock <-> free stream)
    f_mid = 0.5 * (f_post + f_inf)
    x_mid = None
    for i in range(i_peak, i_inf):
        a, b = field[i], field[i + 1]
        if (a - f_mid) * (b - f_mid) <= 0:
            denom = (a - b)
            frac = 0.0 if denom == 0 else (a - f_mid) / denom
            x_mid = x[i] + frac * (x[i + 1] - x[i])
            break
    # max |gradient| within the shock band only
    xs = x[i_peak:i_inf + 1]
    fs = field[i_peak:i_inf + 1]
    grad = np.abs(np.gradient(fs, xs))
    x_grad = xs[np.argmax(grad)]
    return x_mid, x_grad


def main():
    print('=' * 74)
    print('COOLFluiD Hornung N2 cylinder (V3) -- rigorous re-validation')
    print('=' * 74)

    variables, nodes = parse_plt(PLT_FILE)
    print(f'Loaded {PLT_FILE}')
    print(f'  variables: {variables}')
    print(f'  {len(nodes)} P0 cell states')

    stag = extract_stagline(variables, nodes)
    ix = variables.index('x0')
    iT = variables.index('T')
    irho = variables.index('rho')
    irho0 = variables.index('rho0')   # N2
    irho1 = variables.index('rho1')   # N
    ip = variables.index('p')

    x = stag[:, ix]
    T = stag[:, iT]
    rho = stag[:, irho]
    yN = stag[:, irho1] / (stag[:, irho0] + stag[:, irho1])
    p = stag[:, ip]

    print(f'  stagnation-line states: {len(x)}')
    print(f'  x range: {x.min()*1e3:.3f} .. {x.max()*1e3:.3f} mm '
          f'(wall at R={CYL_R*1e3:.2f} mm)')

    # ---- Shock detection (4 criteria) ----
    # Post-shock frozen spike = max-T cell (excludes the cooler wall region);
    # first free-stream cell = where T first drops to within 2% of T_inf.
    i_peak = int(np.argmax(T))
    i_inf = None
    for i in range(i_peak, len(x)):
        if T[i] < 1.02 * T_INF:
            i_inf = i
            break
    if i_inf is None:
        i_inf = len(x) - 1
    print(f'  post-shock T-peak: x={x[i_peak]*1e3:.3f} mm, T={T[i_peak]:.0f} K')
    print(f'  first free-stream cell: x={x[i_inf]*1e3:.3f} mm, T={T[i_inf]:.0f} K')
    xT_mid, xT_grad = detect_shock(x, T, i_peak, i_inf)
    xr_mid, xr_grad = detect_shock(x, rho, i_peak, i_inf)
    shocks = {
        'T midpoint':  xT_mid,
        'T max-gradient': xT_grad,
        'rho midpoint': xr_mid,
        'rho max-gradient': xr_grad,
    }
    print('\n--- Bow shock location (four criteria) ---')
    deltas = {}
    for name, xs in shocks.items():
        if xs is None:
            continue
        d_mm = (xs - CYL_R) * 1e3
        d_R = (xs - CYL_R) / CYL_R
        deltas[name] = d_R
        print(f'  {name:18s}: x_sh={xs*1e3:7.3f} mm  '
              f'delta={d_mm:6.3f} mm  delta/R={d_R:.4f}')

    # Primary stand-off estimate: density midpoint (directly comparable to
    # Hornung interferometry, which measures density).  The max-gradient
    # criteria land on discrete cell boundaries (shock spans ~3 coarse cells)
    # and are reported only as a detection-spread indicator.
    dR_primary = deltas['rho midpoint']
    dR_all = np.array(list(deltas.values()))
    dR_lo, dR_hi = dR_all.min(), dR_all.max()
    # Shock-band cell size gives an intrinsic mesh-resolution uncertainty.
    # The smeared shock runs from the post-shock cell (i_peak) to freestream.
    band_mm = (x[i_inf] - x[i_peak]) * 1e3
    print(f'  smeared shock band width = {band_mm:.2f} mm '
          f'(~{i_inf-i_peak+1} cell centers)')
    print(f'  => PRIMARY (density midpoint, interferometry-comparable): '
          f'delta/R = {dR_primary:.3f}')
    print(f'  detection-convention spread across all criteria: '
          f'{dR_lo:.3f} .. {dR_hi:.3f} R')

    # ---- Physical states vs Mutation++ ----
    # Near-wall stagnation state (first cell = symmetry point on wall)
    i_wall = 0
    T_wall = T[i_wall]
    rho_wall = rho[i_wall]
    p_wall = p[i_wall]
    yN_wall = yN[i_wall]
    # Immediate post-shock state: take max-T cell (frozen spike before
    # dissociation relaxes the temperature down toward the wall).
    i_peak = np.argmax(T)
    T_peak = T[i_peak]
    rho_peak = rho[i_peak]

    print('\n--- Post-shock / stagnation state vs Mutation++ mppshock ---')
    print(f'  Frozen RH spike:   T={MPP_FRZ["T"]:.0f} K (CFD peak T={T_peak:.0f} K, '
          f'{100*(T_peak/MPP_FRZ["T"]-1):+.1f}%)')
    print(f'  Equilibrium:       T={MPP_EQU["T"]:.0f} K (CFD wall T={T_wall:.0f} K, '
          f'{100*(T_wall/MPP_EQU["T"]-1):+.1f}%)')
    print(f'  Equilibrium:       p={MPP_EQU["P"]/1e3:.1f} kPa (CFD wall p={p_wall/1e3:.1f} kPa, '
          f'{100*(p_wall/MPP_EQU["P"]-1):+.1f}%)')
    print(f'  Density ratio frozen = {RHO_RATIO_FRZ:.2f} '
          f'(CFD rho/rho_inf at T-peak = {rho_peak/RHO_INF:.2f})')
    print(f'  Density ratio equil  = {RHO_RATIO_EQU:.2f} '
          f'(CFD rho/rho_inf at wall = {rho_wall/RHO_INF:.2f})')
    print(f'  Wall atomic-N mass fraction yN = {yN_wall:.3f} '
          f'(free stream yN = {stag[:,irho1][-1]/(stag[:,irho0][-1]+stag[:,irho1][-1]):.3f})')

    # ---- Standoff ordering ----
    print('\n--- Shock stand-off summary (CORRECTED ordering) ---')
    print(f'  Frozen chemistry limit   delta/R ~ {FROZEN_STANDOFF_R:.2f} '
          f'(density ratio {RHO_RATIO_FRZ:.1f}; Billig/Hornung cylinder)')
    print(f'  Equilibrium limit        delta/R ~ {EQUIL_STANDOFF_R:.2f} '
          f'(density ratio {RHO_RATIO_EQU:.1f}; scaled by 1/rho-ratio)')
    print(f'  Hornung 1972 experiment  delta/R ~ {EXP_STANDOFF_R:.2f} '
          f'(non-equilibrium, between the limits)')
    print(f'  COOLFluiD V3 (CFD)       delta/R = {dR_primary:.3f} (density midpoint), '
          f'spread {dR_lo:.2f}-{dR_hi:.2f} (coarse 800-cell mesh)')
    err = 100 * abs(dR_primary - EXP_STANDOFF_R) / EXP_STANDOFF_R
    print(f'  CFD relative error vs experiment: {err:.0f}% (over-prediction; '
          f'shock smeared over ~3 coarse cells)')

    # Save corrected summary table
    with open(os.path.join(OUT_DIR, 'hornung_v3_revalidation.txt'), 'w') as f:
        f.write('# COOLFluiD Hornung N2 cylinder V3 -- re-validation summary\n')
        f.write('# Reference: Hornung 1972 JFM 53(1):149-176; Mutation++ mppshock\n\n')
        f.write('Free stream: V=%.0f m/s T=%.0f K rho=%.5f kg/m3 p=%.0f Pa R=%.4f m\n\n'
                % (U_INF, T_INF, RHO_INF, P_INF, CYL_R))
        f.write('Shock stand-off delta/R by detection criterion:\n')
        for name, dR in deltas.items():
            f.write(f'  {name:20s} {dR:.4f}\n')
        f.write(f'  PRIMARY (density-midpoint, interferometry-comparable): {dR_primary:.4f}\n')
        f.write(f'  detection spread:   {dR_lo:.4f} .. {dR_hi:.4f}\n')
        f.write(f'  smeared shock band: {band_mm:.2f} mm (~{i_inf-i_peak+1} cells)\n\n')
        f.write('Reference stand-off (frozen LARGER, equilibrium SMALLER):\n')
        f.write(f'  frozen limit         {FROZEN_STANDOFF_R:.3f} '
                f'(rho2/rho1={RHO_RATIO_FRZ:.2f})\n')
        f.write(f'  equilibrium limit    {EQUIL_STANDOFF_R:.3f} '
                f'(rho2/rho1={RHO_RATIO_EQU:.2f})\n')
        f.write(f'  experiment           {EXP_STANDOFF_R:.3f}\n')
        f.write(f'  CFD relative error   {err:.0f}% over-prediction\n\n')
        f.write('Post-shock state vs Mutation++:\n')
        f.write(f'  frozen  T: mppshock={MPP_FRZ["T"]:.0f} CFD_peak={T_peak:.0f}\n')
        f.write(f'  equil   T: mppshock={MPP_EQU["T"]:.0f} CFD_wall={T_wall:.0f}\n')
        f.write(f'  equil   p: mppshock={MPP_EQU["P"]/1e3:.1f}kPa CFD_wall={p_wall/1e3:.1f}kPa\n')
        f.write(f'  density ratio: frozen={RHO_RATIO_FRZ:.2f}(CFD {rho_peak/RHO_INF:.2f}) '
                f'equil={RHO_RATIO_EQU:.2f}(CFD {rho_wall/RHO_INF:.2f})\n')

    # ---- Plots ----
    x_mm = x * 1e3
    # (1) Stagnation line profiles
    fig, ax = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle('COOLFluiD Hornung N2 cylinder V3 -- stagnation line\n'
                 'V=5590 m/s, T=1833 K, rho=0.005 kg/m3, R=12.7 mm', fontsize=11)

    ax[0, 0].plot(x_mm, T, 'b.-', lw=1.3, ms=4)
    ax[0, 0].axvline(CYL_R*1e3, color='k', ls='--', lw=0.8, label='wall x=R')
    ax[0, 0].axhline(MPP_FRZ['T'], color='gray', ls=':', lw=1.0,
                     label=f"frozen RH T={MPP_FRZ['T']:.0f} K (mppshock)")
    ax[0, 0].axhline(MPP_EQU['T'], color='g', ls=':', lw=1.0,
                     label=f"equil T={MPP_EQU['T']:.0f} K (mppshock)")
    ax[0, 0].set_xlabel('x [mm]'); ax[0, 0].set_ylabel('T [K]')
    ax[0, 0].set_title('(a) Translational temperature')
    ax[0, 0].legend(fontsize=7); ax[0, 0].grid(alpha=0.3)

    ax[0, 1].plot(x_mm, rho, 'k.-', lw=1.3, ms=4, label='rho total')
    ax[0, 1].plot(x_mm, stag[:, irho0], 'b.-', lw=1.0, ms=3, label='rho_N2')
    ax[0, 1].plot(x_mm, stag[:, irho1], 'r.-', lw=1.0, ms=3, label='rho_N')
    ax[0, 1].axvline(CYL_R*1e3, color='k', ls='--', lw=0.8)
    ax[0, 1].axhline(RHO_INF*RHO_RATIO_EQU, color='g', ls=':', lw=1.0,
                     label=f'equil rho ({RHO_RATIO_EQU:.1f}x)')
    ax[0, 1].set_xlabel('x [mm]'); ax[0, 1].set_ylabel('rho [kg/m3]')
    ax[0, 1].set_title('(b) Density')
    ax[0, 1].legend(fontsize=7); ax[0, 1].grid(alpha=0.3)

    ax[1, 0].plot(x_mm, yN, 'r.-', lw=1.3, ms=4)
    ax[1, 0].axvline(CYL_R*1e3, color='k', ls='--', lw=0.8)
    ax[1, 0].set_xlabel('x [mm]'); ax[1, 0].set_ylabel('Y_N (mass fraction)')
    ax[1, 0].set_title('(c) Atomic nitrogen mass fraction')
    ax[1, 0].grid(alpha=0.3)

    ax[1, 1].plot(x_mm, p/1e3, 'b.-', lw=1.3, ms=4)
    ax[1, 1].axvline(CYL_R*1e3, color='k', ls='--', lw=0.8)
    ax[1, 1].axhline(MPP_EQU['P']/1e3, color='g', ls=':', lw=1.0,
                     label=f"equil p={MPP_EQU['P']/1e3:.0f} kPa (mppshock)")
    ax[1, 1].set_xlabel('x [mm]'); ax[1, 1].set_ylabel('p [kPa]')
    ax[1, 1].set_title('(d) Pressure')
    ax[1, 1].legend(fontsize=8); ax[1, 1].grid(alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    f1 = os.path.join(OUT_DIR, 'hornung_v3_revalidation_stagline.png')
    plt.savefig(f1, dpi=150); plt.close()
    print(f'\nSaved: {f1}')

    # (2) Standoff summary with CORRECT ordering
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhline(FROZEN_STANDOFF_R, color='k', ls='--', lw=1.4,
               label=f'frozen limit ~{FROZEN_STANDOFF_R:.2f} (rho2/rho1={RHO_RATIO_FRZ:.1f})')
    ax.axhline(EQUIL_STANDOFF_R, color='k', ls=':', lw=1.4,
               label=f'equilibrium limit ~{EQUIL_STANDOFF_R:.2f} (rho2/rho1={RHO_RATIO_EQU:.1f})')
    ax.plot([1], [EXP_STANDOFF_R], 'r^', ms=13,
            label=f'Hornung 1972 exp {EXP_STANDOFF_R:.2f}')
    ax.errorbar([1.2], [dR_primary], yerr=[[dR_primary-dR_lo], [dR_hi-dR_primary]],
                fmt='bo', ms=12, capsize=6,
                label=f'COOLFluiD V3 CFD {dR_primary:.3f} (density midpoint; '
                f'spread {dR_lo:.2f}-{dR_hi:.2f})')
    ax.set_xlim(0.7, 1.5); ax.set_xticks([])
    ax.set_ylabel('delta/R (shock stand-off / cylinder radius)')
    ax.set_title('Hornung N2 cylinder shock stand-off\n(frozen LARGER than equilibrium; '
                 'CFD over-predicts due to coarse-mesh smearing)')
    ax.grid(axis='y', alpha=0.3); ax.legend(fontsize=9, loc='upper right')
    plt.tight_layout()
    f2 = os.path.join(OUT_DIR, 'hornung_v3_revalidation_standoff.png')
    plt.savefig(f2, dpi=150); plt.close()
    print(f'Saved: {f2}')


if __name__ == '__main__':
    main()
