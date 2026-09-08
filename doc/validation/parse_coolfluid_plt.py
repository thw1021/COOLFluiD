#!/usr/bin/env python3
"""Parse COOLFluiD Tecplot .plt file (FEPOINT format) and extract field data."""
import numpy as np
import re
import sys


def parse_plt(filepath):
    """Parse a COOLFluiD Tecplot FEPOINT .plt file.
    Returns: (variables_list, nodes_array, elements_array, zone_info)
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    variables = None
    zones = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('VARIABLES'):
            # parse variable names
            m = re.findall(r'"([^"]+)"', line)
            variables = m
            i += 1
            continue
        if line.startswith('ZONE'):
            # parse zone header
            zone = {}
            # extract T, N, E, F, ET
            for key in ['T', 'N', 'E', 'F', 'ET', 'SOLUTIONTIME']:
                mm = re.search(rf'{key}=([^,\s]+)', line)
                if mm:
                    val = mm.group(1).strip('"')
                    try:
                        zone[key] = int(val)
                    except ValueError:
                        zone[key] = val
            i += 1
            # read N data lines
            n = zone.get('N', 0)
            nodes = []
            for j in range(n):
                parts = lines[i].split()
                nodes.append([float(p) for p in parts])
                i += 1
            zone['nodes'] = np.array(nodes)
            # read E element lines
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


def extract_stagnation_line(variables, nodes):
    """Extract nodes along the stagnation line (y ~ 0, x >= 0).

    The cylinder is at origin, R = 0.0127 m.
    Stagnation point at (R, 0). Flow from +x direction.
    Stagnation line: y ~ 0, x from R outward.
    """
    x_idx = variables.index('x0')
    y_idx = variables.index('x1')

    # Find nodes on y ~ 0 (within tolerance) and x > 0 (stagnation line on +x side)
    tol = 1e-6
    mask = (np.abs(nodes[:, y_idx]) < tol) & (nodes[:, x_idx] > 0)
    stag = nodes[mask]

    # Sort by x
    stag = stag[np.argsort(stag[:, x_idx])]
    return stag


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/tang/packages/COOLFluiD/RESULTS_CNEQ_EULER_N22_V3/HornungN2.plt'

    variables, zones = parse_plt(filepath)
    print(f"Variables ({len(variables)}): {variables}")
    for z in zones:
        print(f"Zone: {z.get('T')}, N={z.get('N')}, E={z.get('E')}, "
              f"nodes shape={z['nodes'].shape}")

    # Use first zone (the volume field)
    zone = zones[0]
    nodes = zone['nodes']

    # Extract stagnation line
    stag = extract_stagnation_line(variables, nodes)
    print(f"\nStagnation line: {len(stag)} nodes")
    print(f"{'x [m]':<14} {'T [K]':<12} {'rho [kg/m3]':<14} "
          f"{'rho_N2':<12} {'rho_N':<12} {'p [Pa]':<12}")

    x_idx = variables.index('x0')
    rho0_idx = variables.index('rho0')   # N2
    rho1_idx = variables.index('rho1')   # N
    T_idx = variables.index('T')
    rho_idx = variables.index('rho')
    p_idx = variables.index('p')

    for row in stag:
        x = row[x_idx]
        T = row[T_idx]
        rho = row[rho_idx]
        rhoN2 = row[rho0_idx]
        rhoN = row[rho1_idx]
        p = row[p_idx]
        print(f"{x:.6e} {T:10.2f} {rho:12.6e} {rhoN2:12.6e} "
              f"{rhoN:12.6e} {p:12.4f}")

    # Save to file
    out_path = filepath.replace('.plt', '_stagline_full.dat')
    np.savetxt(out_path, stag,
               header=' '.join(variables),
               fmt='%.10e')
    print(f"\nSaved to: {out_path}")


if __name__ == '__main__':
    main()
