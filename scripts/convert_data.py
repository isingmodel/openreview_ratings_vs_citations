"""One-time script to convert existing .pkl and .hdf5 data to JSON/Parquet."""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import h5py
import numpy as np
import pandas as pd


def convert_hdf5_to_json(hdf5_path: Path, output_path: Path) -> int:
    """Convert OpenReview HDF5 file to JSON format. Returns record count."""
    records = []
    with h5py.File(hdf5_path, "r") as f:
        for key in f.keys():
            record = {
                "id": key,
                "rating": f[key]["rating"][()].tolist()
                if isinstance(f[key]["rating"][()], np.ndarray)
                else [f[key]["rating"][()]],
                "decision": f[key]["decision"][()].decode("utf-8"),
                "title": f[key]["title"][()].decode("utf-8"),
            }
            records.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    return len(records)


def convert_pkl_openreview_to_json(pkl_path: Path, output_path: Path) -> int:
    """Convert OpenReview pickle file to JSON format. Returns record count."""
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    # Handle different pickle structures
    if isinstance(data, list):
        # List of forum data - extract key info
        records = []
        for forum in data:
            if isinstance(forum, list):
                # Each forum is a list of notes
                forum_record = {"notes": []}
                for note in forum:
                    note_dict = {
                        "id": getattr(note, "id", None),
                        "forum": getattr(note, "forum", None),
                        "content": getattr(note, "content", {}),
                    }
                    forum_record["notes"].append(note_dict)
                records.append(forum_record)
            else:
                records.append(str(forum))
    else:
        records = data

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False, default=str)

    return len(records) if isinstance(records, list) else 1


def convert_pkl_table_to_parquet(pkl_path: Path, output_path: Path) -> int:
    """Convert preprocessed table pickle to Parquet. Returns row count."""
    df = pd.read_pickle(pkl_path)

    # Convert rating lists to strings for Parquet compatibility
    if "rating" in df.columns:
        df["rating"] = df["rating"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else str(x)
        )

    df.to_parquet(output_path, index=False)
    return len(df)


def convert_year_data(year_dir: Path, verify: bool = False) -> dict:
    """Convert all data files in a year directory. Returns conversion stats."""
    stats = {"year": year_dir.name, "conversions": []}

    for file in year_dir.iterdir():
        if file.suffix == ".hdf5":
            output = year_dir / "openreview_raw.json"
            count = convert_hdf5_to_json(file, output)
            stats["conversions"].append(
                {"source": file.name, "target": output.name, "records": count}
            )
            print(f"  [OK] {file.name} -> {output.name} ({count} records)")

        elif file.suffix == ".pkl" and "openreview" in file.name.lower():
            output = year_dir / "openreview_raw.json"
            if not output.exists():  # Don't overwrite if hdf5 was converted
                count = convert_pkl_openreview_to_json(file, output)
                stats["conversions"].append(
                    {"source": file.name, "target": output.name, "records": count}
                )
                print(f"  [OK] {file.name} -> {output.name} ({count} records)")

        elif file.suffix == ".pkl" and "preprocessed" in file.name.lower():
            output = year_dir / "preprocessed.parquet"
            count = convert_pkl_table_to_parquet(file, output)
            stats["conversions"].append(
                {"source": file.name, "target": output.name, "records": count}
            )
            print(f"  [OK] {file.name} -> {output.name} ({count} rows)")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Convert .pkl and .hdf5 files to JSON/Parquet"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Path to the data directory",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify conversion by comparing record counts",
    )
    args = parser.parse_args()

    print(f"Converting data in: {args.data_dir}\n")

    all_stats = []
    for year_dir in sorted(args.data_dir.iterdir()):
        if year_dir.is_dir() and year_dir.name.startswith("ICLR"):
            print(f"[{year_dir.name}]")
            stats = convert_year_data(year_dir, args.verify)
            all_stats.append(stats)
            print()

    print("Conversion complete!")
    if args.verify:
        print("\nVerification summary:")
        for stats in all_stats:
            print(f"  {stats['year']}: {len(stats['conversions'])} files converted")


if __name__ == "__main__":
    main()
