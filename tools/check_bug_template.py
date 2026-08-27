"""Assert that every defect entry carries the six fields the assignment requires.

Each ``### BUG-NN`` section in the defect report must contain all six labels
verbatim. Presence of the underlying information is not enough: the label must
be there, so the report can be scored against the brief's rubric by scanning
rather than by reading. Exits non-zero if any field is missing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parent.parent / "docs" / "test-execution-and-bugs.md"

REQUIRED = [
    ("Severity", r"\*\*Severity:\*\*"),
    ("Reproduction", r"\*\*Reproduction(?: Steps)?[.:]\*\*"),
    ("Expected", r"\*\*Expected[.:]\*\*"),
    ("Actual", r"\*\*Actual[.:]\*\*"),
    ("Business impact", r"\*\*(?:Business [Ii]mpact|Impact)[.:]\*\*"),
    ("Evidence", r"\*\*Evidence[.:]\*\*"),
]


def main() -> int:
    sections = re.split(
        r"^### (BUG-\d+)[^\n]*$", REPORT.read_text(), flags=re.MULTILINE
    )
    if len(sections) < 3:
        print("no BUG sections found")
        return 1

    widths = [max(len(name), 8) for name, _ in REQUIRED]
    header = "bug      " + " ".join(f"{n:<{w}}" for (n, _), w in zip(REQUIRED, widths))
    print(header)
    print("-" * len(header))

    missing: list[str] = []
    for i in range(1, len(sections), 2):
        bug, body = sections[i], sections[i + 1]
        cells = []
        for (name, pattern), width in zip(REQUIRED, widths):
            found = re.search(pattern, body) is not None
            cells.append(f"{'yes' if found else 'NO':<{width}}")
            if not found:
                missing.append(f"{bug}:{name}")
        print(f"{bug:8} " + " ".join(cells))

    total = len(sections) // 2
    print()
    if missing:
        print(f"FAIL — {len(missing)} field(s) missing: {', '.join(missing)}")
        return 1
    print(f"PASS — {total}/{total} sections carry all {len(REQUIRED)} required labels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
