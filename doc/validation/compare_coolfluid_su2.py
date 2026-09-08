#!/usr/bin/env python3
"""
Cross-comparison of COOLFluiD Hornung N2 cylinder (V3) with SU2 NEMO HEG cylinder.

NOTE: The two cases use DIFFERENT freestream conditions and gas mixtures:
  - COOLFluiD V3: pure N2 (n2_2), V=5590 m/s, T=1833 K, p~2700 Pa, M~6.28
  - SU2 HEG:      air_5,          M=8.803,   T=901 K,  p=476 Pa

The comparison is therefore QUALITATIVE (shape of wall-pressure distribution,
shock structure) and uses normalized quantities where appropriate.
"""
import os
import sys
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CF_RESULTS  = '/home/tang/packages/COOLFluiD/RESULTS_CNEQ_EULER_N22_V3'
CF_SURF_PLT = os.path.join(CF_RESULTS, 'HornungN2.surf.plt')
CF_STAG     = os.path.join(CF_RESULTS, 'HornungN2_stagline_full.dat')
SU2_DIR     = '/home/tang/packages/SU2/nemo_validation/results/heg_cylinder/ord2'
SU2_WALL    = os.path.join(SU2_DIR, 'wall_extract.csv')
OUT_DIR    = CF_RESULTS

# Freestream reference values
CF_P_INF = 2909.0    # Pa (from V3 stagline freestream data)
CF_R      = 0.0127    # m (cylinder radius)
SU2_P_INF = 476.0     # Pa (from SU2 cfg)


# ---------------------------------------------------------------------------
# 1. Parse COOLFluiD surface .plt (FEPOINT format)
# ---------------------------------------------------------------------------
def parse_surf_plt(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    variables = None
    zones = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('VARIABLES'):
            m = re.findall(r'"([^"]+)"', line)
            variables = m
            i += 1
            continue
        if line.startswith('ZONE'):
            zone = {}
            for key in ['T', 'N', 'E', 'F', 'ET', 'SOLUTIONTIME']:
                mm = re.search(rf'{key}=([^,\s]+)', line)
                if mm:
                    try:
                        zone[key] = int(mm.group(1).strip('"'))
                    except ValueError:
                        zone[key] = mm.group(1).strip('"')
            i += 1
            n = zone.get('N', 0)
            nodes = []
            for j in range(n):
                parts = lines[i].split()
                nodes.append([float(p) for p in parts])
                i += 1
            zone['nodes'] = np.array(nodes)
            e = zone.get('E', 0)
            elems = []
            for j in range(e):
                parts = lines[i].split()
                elems.append([int(p) for p in parts])
                i += 1
            zone['elements'] = np.array(elems)
            zones.append(zone)
            continue
        i += 1
    return variables, zones


def compute_theta_deg(x, y, R=CF_R):
    """Compute angle from stagnation point (+x axis), going CCW."""
    theta = np.arctan2(np.abs(y), np.abs(x))   # 0 at +x, pi/2 at +y
    # For the cylinder, the stagnation point is at (R, 0).
    # Points on the surface satisfy x^2 + y^2 = R^2.
    # theta=0 at (R,0), theta=90 at (0,R).
    return np.degrees(theta)


# ---------------------------------------------------------------------------
# 2. Load SU2 wall data
# ---------------------------------------------------------------------------
def load_su2_wall(path):
    """Load SU2 wall_extract.csv: theta_deg, Pressure_kPa, HeatFlux_MWm2."""
    data = np.genfromtxt(path, delimiter=',', skip_header=1)
    return data


# ---------------------------------------------------------------------------
# 3. Comparison plots
# ---------------------------------------------------------------------------
def plot_wall_pressure_comparison(cf_theta, cf_p, su2_data, out_path):
    """Wall pressure distribution: COOLFluiD vs SU2 (normalized by p_inf)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle('Wall pressure distribution — COOLFluiD Hornung N2 (V3) vs SU2 NEMO HEG\n'
                 'COOLFluiD: N2, M~6.28, p_inf~2909 Pa  |  '
                 'SU2: air_5, M=8.803, p_inf=476 Pa',
                 fontsize=10)

    # (a) Absolute pressure
    ax = axes[0]
    ax.plot(cf_theta, cf_p / 1e3, 'b-o', ms=4, lw=1.2, label='COOLFluiD V3 (N2)')
    ax.plot(su2_data[:, 0], su2_data[:, 1], 'r-s', ms=4, lw=1.2, label='SU2 NEMO (air_5)')
    ax.set_xlabel(r'$\theta$ [deg]')
    ax.set_ylabel('p_wall [kPa]')
    ax.set_title('(a) Absolute wall pressure')
    ax.set_xlim(-5, 185)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # (b) Normalized pressure p/p_inf
    ax = axes[1]
    ax.plot(cf_theta, cf_p / CF_P_INF, 'b-o', ms=4, lw=1.2, label='COOLFluiD V3 (N2, M~6.28)')
    ax.plot(su2_data[:, 0], su2_data[:, 1] * 1e3 / SU2_P_INF, 'r-s', ms=4, lw=1.2,
            label='SU2 NEMO (air_5, M=8.803)')
    ax.set_xlabel(r'$\theta$ [deg]')
    ax.set_ylabel(r'$p_{wall}/p_\infty$')
    ax.set_title('(b) Normalized wall pressure')
    ax.set_xlim(-5, 185)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f'Saved: {out_path}')


def plot_stagnation_comparison(cf_stag_path, su2_dir, out_path):
    """Compare stagnation-line temperature/density profiles (qualitative).

    SU2 VTK stores conserved variables (Density_i, Momentum, Energy) —
    Temperature/Pressure would require an EOS call.  If SU2 T/p are not
    directly available in the VTK, we plot only the COOLFluiD stagnation line.
    """
    # COOLFluiD stagnation line
    cf_hdr, cf_data = load_cf_stagline(cf_stag_path)
    cf_x = cf_data[:, 0]   # x0
    cf_T = cf_data[:, 6]   # T
    cf_rho = cf_data[:, 7]   # rho

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle('Stagnation-line profiles — COOLFluiD Hornung N2 (V3)\n'
                 'SU2 NEMO VTK has only conserved vars (no direct T/p) — COOLFluiD only',
                 fontsize=10)

    # (a) Temperature
    ax = axes[0]
    ax.plot(cf_x * 1e3, cf_T, 'b-o', ms=4, lw=1.2, label='COOLFluiD V3 (N2)')
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('T [K]')
    ax.set_title('(a) Temperature along stagnation line')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # (b) Density
    ax = axes[1]
    ax.plot(cf_x * 1e3, cf_rho, 'b-o', ms=4, lw=1.2, label='COOLFluiD V3 (N2)')
    ax.set_xlabel('x [mm]')
    ax.set_ylabel(r'$\rho$ [kg/m$^3$]')
    ax.set_title('(b) Density along stagnation line')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f'Saved: {out_path}')


def load_cf_stagline(path):
    """Load COOLFluiD full stagline file."""
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
                data.append([float(v) for v in s.split()])
            except ValueError:
                pass
    return header, np.array(data)


def extract_su2_stagline(vtk_path):
    """Extract stagnation line (y~0, x>0) from SU2 soln.vtk (ASCII)."""
    if not os.path.isfile(vtk_path):
        return None, None, None
    with open(vtk_path, 'r') as f:
        content = f.read()
    # Parse POINTS
    pts_start = content.find('POINTS')
    if pts_start < 0:
        return None, None, None
    # Find the number of points
    import re
    m = re.search(r'POINTS\s+(\d+)', content[pts_start:pts_start+100])
    if not m:
        return None, None, None
    n_pts = int(m.group(1))
    # Read point coordinates
    pts_lines = content[pts_start:].split('\n')[1:]
    coords = []
    for i in range(n_pts):
        parts = pts_lines[i].split()
        if len(parts) >= 2:
            coords.append([float(parts[0]), float(parts[1])])
    coords = np.array(coords)
    # Parse CELL DATA (temperature, density)
    # SU2 VTK typically has POINT_DATA with Temperature, Density, Pressure
    # Find Temperature data
    t_match = re.search(r'SCALAR Temperature\s+\d+\s+LOOKUP_TABLE default\n(.+?)(?:\n\n|\nSCALAR|\nFIELD|\Z)',
                        content, re.DOTALL)
    rho_match = re.search(r'SCALAR Density\s+\d+\s+LOOKUP_TABLE default\n(.+?)(?:\n\n|\nSCALAR|\nFIELD|\Z)',
                          content, re.DOTALL)
    if t_match:
        t_vals = np.array([float(x) for x in t_match.group(1).split()])
    else:
        return None, None, None
    if rho_match:
        rho_vals = np.array([float(x) for x in rho_match.group(1).split()])
    else:
        rho_vals = np.full_like(t_vals, np.nan)
    # Extract stagnation line: y ~ 0, x > 0
    tol = 0.001   # tolerance in meters
    mask = (np.abs(coords[:, 1]) < tol) & (coords[:, 0] > 0)
    stag_x = coords[mask, 0]
    stag_T = t_vals[mask]
    stag_rho = rho_vals[mask] if rho_vals is not None else None
    # Sort by x
    idx = np.argsort(stag_x)
    return stag_x[idx], stag_T[idx], (stag_rho[idx] if stag_rho is not None else None)


def main():
    print('=' * 72)
    print('COOLFluiD vs SU2 — cross-comparison (qualitative)')
    print('=' * 72)

    # 1. Parse COOLFluiD surface data
    print(f'\nParsing COOLFluiD surface: {CF_SURF_PLT}')
    variables, zones = parse_surf_plt(CF_SURF_PLT)
    print(f'  Variables: {variables}')
    zone = zones[0]
    print(f'  Wall nodes: {zone["nodes"].shape[0]}')

    cols = {name: i for i, name in enumerate(variables)}
    wall_nodes = zone['nodes']
    wall_x = wall_nodes[:, cols['x0']]
    wall_y = wall_nodes[:, cols['x1']]
    wall_p = wall_nodes[:, cols['p']]
    wall_T = wall_nodes[:, cols['T']]

    # Compute theta from (x, y) on the cylinder surface
    cf_theta = compute_theta_deg(wall_x, wall_y)

    # 2. Load SU2 wall data
    print(f'\nLoading SU2 wall: {SU2_WALL}')
    su2_wall = load_su2_wall(SU2_WALL)
    print(f'  SU2 wall points: {len(su2_wall)}')

    # 3. Wall pressure comparison
    out1 = os.path.join(OUT_DIR, 'compare_wall_pressure_coolfluid_su2.png')
    plot_wall_pressure_comparison(cf_theta, wall_p, su2_wall, out1)

    # 4. Stagnation line comparison
    out2 = os.path.join(OUT_DIR, 'compare_stagline_coolfluid_su2.png')
    plot_stagnation_comparison(CF_STAG, SU2_DIR, out2)

    # 5. Summary
    print('\n--- Summary ---')
    print(f'COOLFluiD V3 stagnation pressure: {wall_p[0]:.1f} Pa '
          f'({wall_p[0]/CF_P_INF:.1f} x p_inf)')
    print(f'SU2 NEMO stagnation pressure:    {su2_wall[0,1]*1e3:.1f} Pa '
          f'({su2_wall[0,1]*1e3/SU2_P_INF:.1f} x p_inf)')
    print(f'COOLFluiD V3 stagnation T:        {wall_T[0]:.1f} K')
    print('\nNote: Conditions differ (N2 vs air_5, different M and T_inf).')
    print('Comparison is qualitative — both show bow shock with post-shock')
    print('heating and stagnation pressure peak.')


if __name__ == '__main__':
    main()
