#!/usr/bin/env python3
"""Script to compile QRC resource files for the application.

This script automatically compiles .qrc files in the resources directory
to Python resource modules, making icons and other resources available
to the application.
"""

import os
import subprocess
import sys
from pathlib import Path


def compile_qrc_files():
    """Compile all .qrc files in the resources directory."""
    # Get the resources directory (script is in scripts/ folder, resources in src/yt_database/resources/)
    script_dir = Path(__file__).parent.parent  # Go up to project root
    resources_dir = script_dir / "src" / "yt_database" / "resources"

    if not resources_dir.exists():
        print(f"Error: Resources directory not found: {resources_dir}")
        return False

    success = True
    qrc_files = list(resources_dir.glob("*.qrc"))

    if not qrc_files:
        print("No .qrc files found in resources directory")
        return True

    print(f"Found {len(qrc_files)} QRC files to compile:")

    for qrc_file in qrc_files:
        print(f"  - {qrc_file.name}")

        # Generate output filename (replace .qrc with _rc.py)
        output_file = qrc_file.parent / f"{qrc_file.stem}_rc.py"

        # Run pyside6-rcc
        try:
            result = subprocess.run([
                "poetry", "run", "pyside6-rcc",
                str(qrc_file),
                "-o", str(output_file)
            ], capture_output=True, text=True, cwd=script_dir)

            if result.returncode == 0:
                print(f"Compiled to {output_file.name}")
            else:
                print(f"Compilation failed:")
                print(f"{result.stderr}")
                success = False

        except FileNotFoundError:
            print(f"pyside6-rcc not found. Make sure PySide6 is installed.")
            success = False
        except Exception as e:
            print(f"Error compiling {qrc_file.name}: {e}")
            success = False

    return success


if __name__ == "__main__":
    print("Compiling QRC resource files...")
    success = compile_qrc_files()

    if success:
        print("All QRC files compiled successfully!")
        sys.exit(0)
    else:
        print("Some QRC files failed to compile!")
        sys.exit(1)
