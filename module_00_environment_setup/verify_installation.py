#!/usr/bin/env python3
"""verify_installation.py — Check that all required (and optional) packages
for the fMRI tutorial are importable, and report their version numbers.

Exit codes
----------
0 : all *required* packages were found.
1 : one or more *required* packages are missing.
"""

import argparse
import importlib
import sys


REQUIRED_PACKAGES = ["numpy", "pandas", "nibabel", "matplotlib"]
OPTIONAL_PACKAGES = ["nilearn", "bids", "nipype", "pydicom", "heudiconv"]

# Maps import name → human-readable package name for packages where they differ.
# Add entries here as new packages with non-matching import names are included.
DISPLAY_NAMES = {
    "bids": "pybids",
}


def check_package(import_name: str) -> tuple[bool, str]:
    """Try to import *import_name* and return (found, version_string)."""
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "unknown")
        return True, version
    except ImportError:
        return False, ""


def print_table(title: str, packages: list[str], results: dict[str, tuple[bool, str]]) -> None:
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    print(f"  {'Package':<20} {'Status':<12} {'Version'}")
    print(f"  {'-'*46}")
    for pkg in packages:
        found, version = results[pkg]
        display = DISPLAY_NAMES.get(pkg, pkg)
        status = "AVAILABLE" if found else "MISSING"
        icon = "✅" if found else "❌"
        version_str = version if found else "—"
        print(f"  {icon} {display:<18} {status:<12} {version_str}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that fMRI tutorial Python packages are installed.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--required-only",
        action="store_true",
        help="Only check required packages (skip optional).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress table output; only print a summary line.",
    )
    args = parser.parse_args()

    all_packages = REQUIRED_PACKAGES + ([] if args.required_only else OPTIONAL_PACKAGES)
    results: dict[str, tuple[bool, str]] = {}
    for pkg in all_packages:
        results[pkg] = check_package(pkg)

    if not args.quiet:
        print_table("REQUIRED PACKAGES", REQUIRED_PACKAGES, results)
        if not args.required_only:
            print_table("OPTIONAL PACKAGES", OPTIONAL_PACKAGES, results)

    missing_required = [p for p in REQUIRED_PACKAGES if not results[p][0]]

    if missing_required:
        display_missing = [DISPLAY_NAMES.get(p, p) for p in missing_required]
        print(f"\n❌  Missing required packages: {', '.join(display_missing)}")
        print("    Install them with:")
        print("      conda install -c conda-forge " + " ".join(display_missing))
        return 1

    print("\n✅  All required packages are available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
