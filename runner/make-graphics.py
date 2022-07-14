#!/usr/bin/env python3

from typing import List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import argparse

FONT = {"family": "serif", "size": 18}
LARGE_FONT = 28

STYLES = [
    ("*", "magenta", "magenta"),
    ("x", "cyan", "green"),
    ("o", "yellow", "orange"),
    ("v", "blue", "purple"),
    ("+", "pink", "red"),
    ("*", "brown", "brown"),
    (".", "orange", "orange"),
    ("x", "teal", "teal"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_paths", nargs="+")
    parser.add_argument("out_path")
    parser.add_argument("--uri", dest="uri", action="store_true")
    args = parser.parse_args()
    df = load_df(args.src_paths)
    render(df, args.out_path)


def load_df(src_paths: List[str]) -> pd.DataFrame:
    dataframes = []
    for src_path in src_paths:
        dataframes.append(pd.read_csv(src_path))
        dataframes[-1]["src_path"] = [src_path] * len(dataframes[-1].index)
    df = pd.concat(dataframes)
    target = df.target.iloc[0].replace("lf-", "").upper()
    df["runtime_version"] = (
        [f"{target} {v} {src_path.split('.')[0].split('-')[-1]}" for v in df.scheduler]
        if "scheduler" in df.columns
        else [target] * len(df.index)
    )
    return df


def compute_legend(runtime_versions: str) -> List[Tuple[str, str, str, str]]:
    assert len(STYLES) >= len(runtime_versions)
    return [(a, *b) for a, b in zip(sorted(runtime_versions), STYLES)]


def render(df: pd.DataFrame, out_path: str):
    matplotlib.rc("font", **FONT)
    fig, axes = plt.subplots(6, 4)
    fig.set_size_inches(30, 45)
    axes = axes.ravel()
    x = sorted(list(df.threads.unique()))
    df_numbers = df[np.isfinite(df.mean_time_ms)]
    for ax, benchmark in zip(axes, sorted(list(df.benchmark.unique()))):
        df_benchmark = df_numbers[df_numbers.benchmark == benchmark]
        top = 1.3 * df_benchmark.mean_time_ms.max()
        for version, marker, linecolor, markercolor in compute_legend(
            df.runtime_version.unique()
        ):
            df_benchmark_scheduler = df_benchmark[
                df_benchmark.runtime_version == version
            ]
            ax.set_title(benchmark)
            ax.set_xticks(x)
            ax.set_ylim(bottom=0, top=top)
            (line,) = ax.plot(
                x,
                [
                    df_benchmark_scheduler[
                        df_benchmark_scheduler.threads == threads
                    ].mean_time_ms.mean()
                    for threads in x
                ],
                marker=marker,
                ms=12,
                linewidth=2,
                c=linecolor,
                markeredgecolor=markercolor,
            )
            line.set_label(version)
        ax.legend()
    ax = fig.add_subplot(111, frameon=False)
    ax.xaxis.label.set_fontsize(LARGE_FONT)
    ax.yaxis.label.set_fontsize(LARGE_FONT)
    ax.title.set_fontsize(LARGE_FONT)
    ax.set_facecolor("white")
    plt.rc("font", size=LARGE_FONT)
    plt.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False)
    plt.title("Comparison of Scheduler Versions\n")
    plt.xlabel("Number of Threads")
    plt.ylabel("Mean Time (milliseconds)\n")
    fig.patch.set_facecolor("white")
    fig.savefig(out_path, transparent=False)


if __name__ == "__main__":
    main()
