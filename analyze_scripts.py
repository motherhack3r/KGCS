#!/usr/bin/env python3
"""
Analyze scripts/ directory to categorize files and identify organization needs.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

scripts_dir = Path("scripts")

# Analyze each script
scripts_info = {}

for script_file in sorted(scripts_dir.glob("*.py")):
    if script_file.name.startswith("."):
        continue
    
    with open(script_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read(500)  # First 500 chars for quick analysis
        
    # Determine purpose based on filename and content
    name = script_file.name
    
    # Categorize
    category = "utility"
    if "validate" in name:
        category = "validation"
    elif "combine" in name or "merge" in name:
        category = "pipeline"
    elif "regenerate" in name or "run_all" in name:
        category = "pipeline"
    elif "cleanup" in name or "export" in name:
        category = "utility"
    elif "reload" in name or "extract" in name:
        category = "database"
    elif "verify" in name:
        category = "verification"
    elif "create" in name:
        category = "data_generation"
    
    scripts_info[name] = {
        "category": category,
        "path": str(script_file),
        "size": script_file.stat().st_size,
        "description": ""
    }

# Print analysis
print("\n" + "="*80)
print("SCRIPTS DIRECTORY ANALYSIS")
print("="*80 + "\n")

categories = defaultdict(list)
for name, info in scripts_info.items():
    categories[info["category"]].append(name)

for category in sorted(categories.keys()):
    print(f"\n{category.upper().replace('_', ' ')} ({len(categories[category])} files):")
    print("-" * 60)
    for script in sorted(categories[category]):
        size_kb = scripts_info[script]["size"] / 1024
        print(f"  • {script:40s} ({size_kb:6.1f} KB)")

# Detailed script purposes
print("\n" + "="*80)
print("DETAILED SCRIPT PURPOSES")
print("="*80 + "\n")

script_descriptions = {
    "run_all_etl.py": "Main ETL orchestrator - runs all 13 transformation stages [PRODUCTION]",
    "validate_all_standards.py": "Validates all ETL outputs with SHACL [PRODUCTION]",
    "validate_shacl_stream.py": "Streaming SHACL validator for large files [PRODUCTION]",
    "validate_etl_pipeline_order.py": "Validates ETL dependency order [PRODUCTION]",
    "validate_shacl_parallel.py": "Parallel SHACL validation runner [PRODUCTION]",
    "combine_pipeline.py": "Combines all pipeline stages into single file [PRODUCTION]",
    "verify_combined_capec.py": "Verifies CAPEC enhancement in combined pipeline [PRODUCTION]",
    "extract_neo4j_stats.py": "Extracts statistics from Neo4j database [UTILITY]",
    "reload_neo4j.py": "Reloads data into Neo4j [UTILITY]",
    "create_phase3_samples.py": "Creates sample data for testing [UTILITY]",
    "export_ttl_to_csv.py": "Exports RDF/TTL to CSV format [UTILITY]",
    "cleanup_workspace.py": "Cleans up temporary files [UTILITY]",
    "regenerate_pipeline.py": "Regenerates pipeline with timeout handling [PRODUCTION]",
}

for script in sorted(script_descriptions.keys()):
    if script in scripts_info:
        print(f"\n{script}")
        print(f"  {script_descriptions[script]}")

# Check for duplicates/overlaps
print("\n" + "="*80)
print("ANALYSIS & RECOMMENDATIONS")
print("="*80 + "\n")

print("ORGANIZATION OPPORTUNITIES:\n")

print("1. VALIDATION SCRIPTS (5 files)")
print("   These could be consolidated into scripts/validation/ subdirectory:")
print("   ✓ validate_all_standards.py")
print("   ✓ validate_shacl_stream.py")
print("   ✓ validate_etl_pipeline_order.py")
print("   ✓ validate_shacl_parallel.py")
print("   ✓ regenerate_pipeline.py (contains validation)")
print("")

print("2. PIPELINE SCRIPTS (2 core files)")
print("   These could remain at root or be grouped:")
print("   ✓ run_all_etl.py (main entry point)")
print("   ✓ combine_pipeline.py")
print("")

print("3. UTILITY/SUPPORT SCRIPTS (4 files)")
print("   These could be moved to scripts/utilities/:")
print("   ✓ extract_neo4j_stats.py")
print("   ✓ reload_neo4j.py")
print("   ✓ create_phase3_samples.py")
print("   ✓ export_ttl_to_csv.py")
print("   ✓ cleanup_workspace.py")
print("")

print("4. VERIFICATION SCRIPTS (1 file)")
print("   Could stay at root or be grouped with validation:")
print("   ✓ verify_combined_capec.py")
print("")

print("5. LEGACY/ARCHIVED FILES")
print("   Already have scripts/.archive/ (good! but could add note in README)")
print("")

print("CURRENT ORGANIZATION ASSESSMENT:")
print("-" * 60)
print("Status: ⚠️  MODERATE CLEANUP NEEDED")
print("")
print("Issues:")
print("  • 14 scripts in root scripts/ directory (becoming cluttered)")
print("  • Mixed purposes without clear logical grouping")
print("  • No clear distinction between core/production vs utilities")
print("  • .archive/ exists but utilities not organized")
print("")
print("Recommendation:")
print("  Organize into subdirectories by purpose:")
print("    scripts/")
print("    ├── run_all_etl.py              (main entry)")
print("    ├── combine_pipeline.py          (pipeline core)")
print("    ├── verify_combined_capec.py    (verification core)")
print("    ├── validation/                  (validation scripts)")
print("    ├── utilities/                   (support scripts)")
print("    ├── .archive/                    (legacy files)")
print("    └── README.md                    (new - document purpose of each)")
print("")
print("Benefit: Much clearer organization, easier to find what you need")
