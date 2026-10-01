# compare_outputs.py
#
# A checking tool for Phase 2 (not part of the project itself).
#
# phase1_output.txt is the "answer key": the exact output of the Tinker case
# study from Phase 1. This script runs the case study as it is right now and
# checks that every line matches the answer key.
#
# Use it after switching tinker_case_study.py over to your classes:
#     python3 compare_outputs.py
#
# It runs the case study for you, so you don't have to save any output
# yourself. You don't need to understand how this file works -- it's a
# checking tool, not part of the project. (The imports below, `os`,
# `subprocess`, and `sys`, are what let it find the project folder, run
# another Python file, and read what that file prints.)
#
# It works no matter which folder your terminal is in, because it always
# looks for its files in the same folder as this script.

import os
import subprocess
import sys

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))


def read_answer_key():
    """Return the lines of phase1_output.txt as a list."""
    file = open(os.path.join(PROJECT_FOLDER, "phase1_output.txt"), encoding="utf-8")
    lines = file.read().splitlines()
    file.close()
    return lines


def run_case_study():
    """Run tinker_case_study.py and return what it printed, as a list of lines."""
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_FOLDER, "tinker_case_study.py")],
        capture_output=True,
        text=True,
        cwd=PROJECT_FOLDER,
    )
    if result.returncode != 0:
        print("The case study crashed before finishing. Here's the error:\n")
        print(result.stderr)
        return None
    return result.stdout.splitlines()


def compare():
    expected = read_answer_key()
    actual = run_case_study()
    if actual is None:
        return

    for i in range(len(expected)):
        if i >= len(actual):
            print(f"Your output stopped early, at line {i + 1}.")
            print(f"  Expected: {expected[i]}")
            return
        if expected[i] != actual[i]:
            print(f"First difference is on line {i + 1}:")
            print(f"  Expected: {expected[i]}")
            print(f"  Got:      {actual[i]}")
            return

    if len(actual) > len(expected):
        print(f"Your output has extra lines, starting at line {len(expected) + 1}:")
        print(f"  {actual[len(expected)]}")
        return

    print(f"MATCH: all {len(expected)} lines are identical to Phase 1. The refactor is correct.")


if __name__ == "__main__":
    compare()