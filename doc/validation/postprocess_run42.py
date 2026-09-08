#!/usr/bin/env python3
"""
Postprocess DoubleCone Run42 results — extract wall pressure/heat flux
and compare with CUBRC experimental data.

Wall data is in DConeFVM_heat.plt-P0Side0 (or DConeFVM_heat.pltSide0 for smoke).
Format: COOLFluiD Tecplot FEPOINT surface file.

Reference: Lani 2009 PhD thesis, Fig. 6.18/6.19 (PDF p. 183)
  - Wall pressure: 25° cone platform ~9-10 kPa, reattachment peak ~47 kPa @ x≈0.09 m
  - Heat flux: stagnation ~6×10^5 W/m², reattachment peak ~5-6×10^5 W/m²
"""
import os
import sys
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def parse_surf_plt(path):
    """Parse COOLFluiD surface Tecplot .plt file.

    Handles both FEPOINT format (with ZONE header) and simple ASCII format
    (VARIABLES + raw data lines).
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    variables = None
    zones = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('VARIABLES'):
            # Try quoted names first, fall back to unquoted
            m = re.findall(r'"([^"]+)"', line)
            if not m:
                # Unquoted: "VARIABLES = x0 x1 P T ..."
                parts = line.split('=', 1)
                if len(parts) == 2:
                    m = parts[1].split()
            variables = m
            i += 1
            continue
        if line.startswith('ZONE'):
            zone = {}
            for key in ['T', 'N', 'E', 'F', 'ET']:
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
    # If no ZONE found, treat all data lines after VARIABLES as one zone
    if not zones and variables is not None:
        data = []
        for line in lines:
            s = line.strip()
            if not s or s.startswith('TITLE') or s.startswith('VARIABLES') or s.startswith('ZONE'):
                continue
            try:
                parts = s.split()
                row = [float(p) for p in parts]
                if len(row) == len(variables):
                    data.append(row)
            except ValueError:
                continue
        if data:
            zones.append({'nodes': np.array(data), 'T': 'Data', 'N': len(data)})
    return variables, zones


def main():
    if len(sys.argv) < 2:
        print('Usage: postprocess_run42.py <results_dir>')
        print('Example: postprocess_run42.py RESULTS_Dcone_TCNEQ_MPP/')
        sys.exit(1)
    results_dir = sys.argv[1]
    
    # Find wall heat flux file
    heat_file = None
    for name in ['DConeFVM_heat.plt-P0Side0', 'DConeFVM_heat.pltSide0']:
        p = os.path.join(results_dir, name)
        if os.path.isfile(p):
            heat_file = p
            break
    if heat_file is None:
        print(f'ERROR: no wall heat flux file found in {results_dir}', file=sys.stderr)
        sys.exit(1)
    
    print(f'Parsing: {heat_file}')
    variables, zones = parse_surf_plt(heat_file)
    print(f'Variables: {variables}')
    for z in zones:
        print(f'  Zone: {z.get("T")}, N={z.get("N")}, nodes={z["nodes"].shape}')
    
    if not zones:
        print('ERROR: no zones found', file=sys.stderr)
        sys.exit(1)
    
    zone = zones[0]
    nodes = zone['nodes']
    cols = {name: i for i, name in enumerate(variables)}
    
    # Extract wall coordinate and pressure (variable name may be 'p' or 'P')
    p_var = 'p' if 'p' in cols else ('P' if 'P' in cols else None)
    if 'x0' in cols and p_var:
        x = nodes[:, cols['x0']]
        p = nodes[:, cols[p_var]]
    else:
        print(f'ERROR: expected x0 and p/P in variables: {variables}', file=sys.stderr)
        sys.exit(1)
    
    # Plot wall pressure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, p / 1e3, 'b-o', ms=3, lw=1.2, label='COOLFluiD Run42')
    
    # Reference experimental data points (from Lani 2009, Fig. 6.18a)
    # These are approximate digitized values for reference
    exp_x = np.array([0.0, 0.02, 0.04, 0.06, 0.08, 0.09, 0.10, 0.12, 0.14, 0.16])
    exp_p = np.array([10, 9.5, 9.0, 2.0, 1.5, 47, 30, 5, 4, 3])  # kPa (approximate)
    ax.plot(exp_x, exp_p, 'r^', ms=8, label='CUBRC experiment (approx.)')
    
    ax.set_xlabel('x [m]')
    ax.set_ylabel('p_wall [kPa]')
    ax.set_title('DoubleCone Run42 — Wall pressure distribution')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    out_path = os.path.join(results_dir, 'run42_wall_pressure.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f'Saved: {out_path}')
    
    # Save wall data
    out_dat = os.path.join(results_dir, 'run42_wall_data.dat')
    np.savetxt(out_dat, np.column_stack([x, p]),
               header='x [m]   p [Pa]', fmt='%.6e')
    print(f'Saved: {out_dat}')


if __name__ == '__main__':
    main()
