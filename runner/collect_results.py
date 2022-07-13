#!/usr/bin/env python3


import argparse
import functools
from itertools import product
import pandas as pd
import pathlib
import os
import json


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_path")
    parser.add_argument("out_file")
    parser.add_argument("--raw", dest="raw", action="store_true")
    args = parser.parse_args()

    # collect data from all runs
    src_path = (
        args.src_path if args.src_path != "latest"
        else latest_subdirectory(latest_subdirectory("./multirun"))
    )
    data_frames = []
    for path in pathlib.Path(src_path).rglob("results.csv"):
        data_frames.append(pd.read_csv(path.as_posix()))

    # determine min, max and median
    if not args.raw:
        reduced_data_frames = []
        for df in data_frames:
            reduced_df = df.drop(columns=["time_ms", "iteration"]).drop_duplicates()
            reduced_df["min_time_ms"] = df["time_ms"].min()
            reduced_df["max_time_ms"] = df["time_ms"].max()
            reduced_df["median_time_ms"] = df["time_ms"].median()
            reduced_df["mean_time_ms"] = df["time_ms"].mean()
            reduced_data_frames.append(reduced_df)
        data_frames = reduced_data_frames

    # concatenate the data
    concat = pd.concat(data_frames, ignore_index=True)

    # write the concatenated results
    if args.out_file.endswith(".json"):
        with open(args.out_file, "w") as f:
            json.dump((create_json(concat)), f, indent=4)
    else:
        concat.to_csv(args.out_file)

def create_json(all_data: pd.DataFrame) -> str:
    group_by = ["benchmark", "target", "threads", "scheduler"]
    name_computer = lambda group: group[0] + " (" + ", ".join(
        f"{group_by[i]}={p}"
        for i, p in enumerate(group_by[1:])
        if len(all_data[p].unique()) > 1
    ) + ")"
    is_correct_group = lambda group: functools.reduce(
        lambda a, b: a & b,
        [all_data[group_by[i]].values == v for i, v in enumerate(group)]
    )
    return [
        {
            "name": name_computer(group),
            "unit": "ms",
            "value": all_data[is_correct_group(group)].mean_time_ms.mean(),
            "extra": f"Target: {group[0]}"
                f"\nTotal Iterations: {all_data[is_correct_group(group)].total_iterations.iloc[0]}"
                f"\nThreads: {group[2]}"
                f"\nScheduler: {group[-1]}"
        }
        for group in product(*[all_data[p].unique() for p in group_by])
    ]

def latest_subdirectory(parent):
    if parent is None:
        raise Exception(f"{parent} does not exist.")
    subdirectories = os.listdir(parent)
    subdirectories.sort(key=functools.cmp_to_key(compare_dirnames))
    if not subdirectories:
        raise Exception(f"{parent} is empty.")
    return os.path.join(parent, subdirectories[-1])

def compare_dirnames(s0, s1):
    for number0, number1 in [(int(a), int(b)) for a, b in zip(s0.split("-"), s1.split("-"))]:
        if number0 != number1:
            return number0 - number1
    return 0

if __name__ == "__main__":
    main()
