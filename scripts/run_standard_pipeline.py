#!/usr/bin/env python3
"""Interactive helper to run a single pipeline step for a selected standard.

Prompts:
 - standard (e.g., capec, attack, cve, d3fend)
 - step (download, etl, shacl, load-nodes, load-rels, stats)
 - optional DB name for loader/stats

The script prints the command it will run and asks for confirmation before executing.
"""
import subprocess
import sys
import os
from shutil import which

STEPS = ["download", "etl", "shacl", "load-nodes", "load-rels", "stats"]

def prompt(prompt_text, default=None):
    if default:
        return input(f"{prompt_text} [{default}]: ").strip() or default
    return input(f"{prompt_text}: ").strip()


def run_command(cmd, shell=False):
    print("Running:", " ".join(cmd) if isinstance(cmd, (list, tuple)) else cmd)
    try:
        subprocess.check_call(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return False
    return True


def main():
    print("Run single pipeline step for a standard (interactive)")
    standard = prompt("Standard (e.g. capec, attack, cve, d3fend)")
    if not standard:
        print("No standard provided, aborting")
        return 1

    print("Available steps:")
    for i, s in enumerate(STEPS, 1):
        print(f"  {i}. {s}")
    step_in = prompt("Select step name or number")
    if step_in.isdigit():
        step_idx = int(step_in) - 1
        if not (0 <= step_idx < len(STEPS)):
            print("Invalid step number")
            return 1
        step = STEPS[step_idx]
    else:
        step = step_in
    if step not in STEPS:
        print("Invalid step")
        return 1

    db_name = None
    if step.startswith("load") or step == "stats":
        db_name = prompt("Neo4j database name (leave blank to auto-detect)", default="")

    # Build command templates
    python_exe = sys.executable
    commands = []
    if step == "download":
        commands.append([python_exe, "-m", "src.ingest.download_manager", "--standards", standard])
    elif step == "etl":
        # Run the per-standard ETL module directly (avoid running all ETLs)
        etl_module_path = os.path.join("src", "etl", f"etl_{standard}.py")
        if os.path.exists(etl_module_path):
            output_path = os.path.join("data", standard, "samples", f"{standard}-output.ttl")
            commands.append([python_exe, "-m", f"src.etl.etl_{standard}", "--input", os.path.join("data", standard, "raw"), "--output", output_path])
        else:
            # Fallback to run_all_etl if per-standard ETL module not found
            commands.append([python_exe, os.path.join("scripts", "run_all_etl.py"), "--standard", standard])
    elif step == "shacl":
        # best-effort: validate per-standard shapes if a helper exists
        validate_script = os.path.join("scripts", "validation", "validate_all_standards.py")
        if os.path.exists(validate_script):
            commands.append([python_exe, validate_script, "--standard", standard])
        else:
            print("No validation helper found (scripts/validation/validate_all_standards.py). Skipping.")
    elif step == "load-nodes":
        # Use PowerShell loader wrapper if available, otherwise suggest manual command
        ps_script = os.path.join(".", "scripts", "load_nodes_all.ps1")
        if os.path.exists(ps_script):
            cmd = ["pwsh", "-NoProfile", "-Command", f"& '{ps_script}' -PythonExe {python_exe} -DbVersion {db_name or ''} -FastParse -ProgressNewline -ParseHeartbeatSeconds 20"]
            commands.append(cmd)
        else:
            print("PowerShell loader not found: scripts/load_nodes_all.ps1")
    elif step == "load-rels":
        ps_script = os.path.join(".", "scripts", "load_rels_all.ps1")
        if os.path.exists(ps_script):
            cmd = ["pwsh", "-NoProfile", "-Command", f"& '{ps_script}' -PythonExe {python_exe} -DbVersion {db_name or ''} -FastParse -ProgressNewline -ParseHeartbeatSeconds 20"]
            commands.append(cmd)
        else:
            print("PowerShell loader not found: scripts/load_rels_all.ps1")
    elif step == "stats":
        stats_script = os.path.join("scripts", "utilities", "extract_neo4j_stats.py")
        cmd = [python_exe, stats_script]
        if db_name:
            cmd += ["--db", db_name]
        cmd += ["--pretty"]
        commands.append(cmd)

    if not commands:
        print("No commands to run for the selected step")
        return 1

    for cmd in commands:
        print("\nCommand:")
        print(" ".join(cmd) if isinstance(cmd, (list, tuple)) else cmd)
        ok = prompt("Run this command? (y/N)", default="N")
        if ok.lower() == 'y':
            run_command(cmd)
        else:
            print("Skipped.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
