#!/usr/bin/env python3
"""Generate the ETL-lab raw facilities CSV for a profile — and verify it conforms.

The raw CSV is DERIVED from a profile's facility seed (via the shared messiness recipe in
profiles/common.py), so it can never drift from the dataset the generator builds. Run this
whenever a profile's facilities change; commit the resulting CSV.

Usage:
    python etl_lab/build_raw_csv.py --profile pediatric        # writes facilities_raw.pediatric.csv
    python etl_lab/build_raw_csv.py --all                      # rebuild every profile's CSV
    python etl_lab/build_raw_csv.py --all --check              # verify only (no write) — for CI

Each CSV, after the Lakeflow Designer lab's transforms, must conform to exactly the profile's
clean facility dimension. `--check`/the post-write assert prove that.
"""
import argparse
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from profiles import PROFILES, get_profile
from profiles.common import build_messy_facility_csv, conform, facilities_with_ids

HERE = os.path.dirname(os.path.abspath(__file__))


def expected_dim(seed):
    """The clean facility dimension the raw CSV must conform to (proper-cased type)."""
    return sorted((fid, name, ftype, city, state, region)
                  for (fid, name, ftype, city, state, region) in facilities_with_ids(seed))


def verify(profile):
    seed = profile["facility_seed"]
    raw = build_messy_facility_csv(seed)
    rows = list(csv.DictReader(io.StringIO(raw)))
    got = conform(rows)
    want = expected_dim(seed)
    problems = []
    if len(got) != len(seed):
        problems.append(f"expected {len(seed)} clean rows, got {len(got)}")
    nulls = [r[0] for r in got if not r[5]]
    if nulls:
        problems.append(f"null region after derive: {nulls}")
    if got != want:
        problems.append("conformed rows do not match the clean facility dimension")
    return raw, got, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", help="profile name (e.g. adult, pediatric)")
    ap.add_argument("--all", action="store_true", help="process every registered profile")
    ap.add_argument("--check", action="store_true", help="verify only; do not write files")
    args = ap.parse_args()

    names = list(PROFILES) if args.all else ([args.profile] if args.profile else [])
    if not names:
        ap.error("pass --profile <name> or --all")

    failed = False
    for name in names:
        profile = get_profile(name)
        raw, got, problems = verify(profile)
        status = "OK" if not problems else "FAIL: " + "; ".join(problems)
        print(f"[{name}] {len(got)} clean rows — {status}")
        if problems:
            failed = True
            continue
        if not args.check:
            path = os.path.join(HERE, f"facilities_raw.{name}.csv")
            with open(path, "w", newline="") as f:
                f.write(raw)
            print(f"    wrote {os.path.relpath(path)}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
