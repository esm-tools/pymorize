#!/usr/bin/env python3
"""
Cleans up from example runs
"""
import shutil
from pathlib import Path


def cleanup():
    current_dir = Path.cwd()

    for item in current_dir.rglob("*"):
        if (
            item.is_file()
            and item.name.startswith("slurm")
            and item.name.endswith("out")
        ):
            try:
                item.unlink()
                print(f"Removed file: {item}")
            except Exception as e:
                print(f"Error removing file {item}: {e}")

        elif item.is_dir() and item.name == "logs":
            try:
                shutil.rmtree(item)
                print(f"Removed directory: {item}")
            except Exception as e:
                print(f"Error removing directory {item}: {e}")
    print("Cleanup completed.")


if __name__ == "__main__":
    cleanup()
