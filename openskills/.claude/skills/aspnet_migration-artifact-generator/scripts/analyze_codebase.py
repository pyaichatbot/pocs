#!/usr/bin/env python3
"""analyze_codebase.py

Simple analysis script for ASP.NET codebases. Produces a JSON summary and a human-readable report.

Usage:
  python analyze_codebase.py --path /path/to/project --output report.json
"""
import os
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

EXTS = ['.sln', '.aspx', '.ascx', '.cs', '.config', '.csproj', '.vb', '.sql', '.dll', '.xml']


def find_files(root: Path):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            p = Path(dirpath) / f
            ext = p.suffix.lower()
            files.setdefault(ext, []).append(str(p))
    return files


def parse_sln(sln_path: Path):
    projects = []
    try:
        with sln_path.open('r', encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('Project('):
                    parts = line.split('=')
                    if len(parts) >= 2:
                        name_part = parts[1].strip().split(',')
                        if name_part:
                            proj_name = name_part[0].strip().strip('"')
                            projects.append(proj_name)
    except Exception:
        pass
    return projects


def parse_web_config(path: Path):
    data = {}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # look for connectionStrings
        for cs in root.findall('.//connectionStrings/add'):
            name = cs.attrib.get('name')
            conn = cs.attrib.get('connectionString')
            if name:
                data.setdefault('connectionStrings', {})[name] = conn
        # auth mode
        auth = root.find('.//authentication')
        if auth is not None:
            data['authentication'] = auth.attrib
    except Exception:
        pass
    return data


def find_nuget_in_csproj(path: Path):
    pkgs = []
    try:
        tree = ET.parse(path)
        for pr in tree.findall('.//PackageReference'):
            name = pr.attrib.get('Include') or pr.attrib.get('Update')
            version = pr.attrib.get('Version')
            if name:
                pkgs.append({'name': name, 'version': version})
    except Exception:
        pass
    return pkgs


def analyze(root_path: str):
    root = Path(root_path)
    if not root.exists():
        raise FileNotFoundError(root_path)
    files = find_files(root)
    summary = {
        'root': str(root.resolve()),
        'counts': {k: len(v) for k, v in files.items()},
        'samples': {k: v[:20] for k, v in files.items()},
        'solutions': [],
        'web_configs': {},
        'nuget_packages': [],
        'sql_scripts': files.get('.sql', []),
    }
    # parse sln
    for sln in files.get('.sln', [])[:5]:
        summary['solutions'].append({
            'path': sln,
            'projects': parse_sln(Path(sln)),
        })
    # parse web.config
    for config in files.get('.config', [])[:5]:
        wc = parse_web_config(Path(config))
        if wc:
            summary['web_configs'][config] = wc
    # parse csproj for nuget
    for csproj in files.get('.csproj', [])[:50]:
        pkgs = find_nuget_in_csproj(Path(csproj))
        if pkgs:
            summary['nuget_packages'].append({'csproj': csproj, 'packages': pkgs})
    # detect aspx pages and code-behind
    summary['aspx_count'] = len(files.get('.aspx', []))
    summary['ascx_count'] = len(files.get('.ascx', []))
    summary['code_behind_count'] = len([p for p in files.get('.cs', []) if p.endswith('.aspx.cs') or p.endswith('.ascx.cs')])

    return summary


def main():
    parser = argparse.ArgumentParser(description='Analyze ASP.NET codebase for migration artifacts')
    parser.add_argument('--path', '-p', required=True, help='Path to project root')
    parser.add_argument('--output', '-o', required=False, help='Path to write JSON summary')
    args = parser.parse_args()

    summary = analyze(args.path)
    out = args.output
    if out:
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2)
        print(f'Wrote summary to {out}')
    else:
        print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
