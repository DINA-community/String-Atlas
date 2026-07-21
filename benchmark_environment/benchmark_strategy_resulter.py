#!/usr/bin/env python3
"""Evaluate benchmark strategy result CSV files.

The input files are expected to have names such as:

    system_2024_2026_vector_fuzzy_exact_0.8.csv

The strategy order is read from the strategy tokens in the filename
(`exact`, `fuzzy`, `vector`) and the trailing number is used as threshold.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import re
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def get_data() -> pd.DataFrame:
    """Load csv files and get ride of first empty column."""
    dfs = []
    files = Path("results").glob("*.csv")
    if not any(files):
        print('No csv files under results/ found')
        return pd.DataFrame(dfs)
    for file in Path("results").glob("*.csv"):
        method, threshold = re.search(
            r".*\d{4}_\d{4}_(.*?)_([0-9.]+)\.csv$",
            str(file),
        ).groups()

        df_tmp = pd.read_csv(
            file,
            dtype={
                "count tests": int,
                "failed": int,
                "passed": float,
                "time at all (ms)": float,
                "time average (ms)": float,
            },
            index_col=False,
        )
        df_tmp = df_tmp.iloc[:, 1:]  # drop first column
        df_tmp["method"] = method
        df_tmp["threshold"] = float(threshold)
        dfs.append(df_tmp)

    return pd.concat(dfs, ignore_index=True)


def plot_curves(ax, plot_df, value):
    curve_groups = {}

    for method, group in plot_df.groupby("method"):
        group = group.sort_values("threshold")
        key = (
            tuple(group["threshold"]),
            tuple(group[value]),
        )
        curve_groups.setdefault(key, []).append(method)

    for (x, y), methods in curve_groups.items():
        ax.plot(x, y, marker="o", label=", ".join(sorted(methods)))


def format_axis(ax, title, ylabel):
    ax.set_title(title)
    ax.set_xlabel("Threshold")
    ax.set_ylabel(ylabel+" (normalized)")
    ax.set_yticks(np.arange(0, 1.01, 0.25))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.grid(alpha=0.3)


def get_normalizer(df, category, case, plot):

    if case == "passed":
        if plot == "single":
            return df.loc[df["category"] == category, "count tests"].max()
        else:
            return round(df["count tests"].mean() * len(df["category"].unique()))
    elif case == "time average (ms)":
        if plot == "single":
            return df.loc[df["category"] == category, "time average (ms)"].max()
        else:
            max_total = 0
            for dummy, group in df.groupby("category"):
                max_total += group["time average (ms)"].max()
            return max_total
    return 0


def plot_group(ax, data, title, case, normalizer):
    plot_df = data.groupby(["threshold", "method"], as_index=False)[case].sum()
    plot_df[case] /= normalizer
    plot_curves(ax, plot_df, case)
    format_axis(ax, title, case)


def plot2x2_data(df: pd.DataFrame, case: str = "passed"):
    """Plots the benchmark data in 4 diagrams
    3 Testcases and one total plot
    The y-axis is normalized to 100%
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=False)
    axes = axes.ravel()

    categories = sorted(df["category"].unique())

    for ax, category in zip(axes[:3], categories):
        subset = df[df["category"] == category]
        normalizer = get_normalizer(subset, category, case, "single")
        plot_group(ax, subset, category, case, normalizer)

    normalizer = get_normalizer(df, "", case, "sum")
    plot_group(axes[3], df, "Total", case, normalizer)

    handles, labels = axes[3].get_legend_handles_labels()
    # fit labels 
    labels = [label.replace(",", "\n") for label in labels]

    fig.legend(
        handles,
        labels,
        title="Method",
        loc="center right",
        bbox_to_anchor=(0.95, 0.5),
        ncol=1,
        fontsize="large",
        frameon=True,
    )

    plt.tight_layout(rect=[0, 0, 0.75, 0.95])
    plt.savefig(f"plot_{case}.png")
    return fig


def ranking(df):
    """Get information about threshold and method choice."""

    #####################################
    # Get the favorite threshold values #
    #####################################
    thresholds = set()

    for category in df["category"].unique():
        values = (
            df.loc[df["category"] == category]
            .sort_values("passed", ascending=False)
            .head(20)
            .sort_values("time average (ms)")["threshold"]
        )
        thresholds.update(values)

    thresholds = sorted(thresholds)

    best_methods = []
    promissing_methods = set()

    #######################
    # Evaluation baseline #
    #######################

    for category in df.category.unique():
        entries = (
            df.loc[df.threshold.isin(thresholds) & (df.category == category)]
            .sort_values(by=["passed"], ascending=False)
            .head()
            .sort_values(by=["time average (ms)"])["method"]
            .head()
        )
        promissing_methods.update(entries)
        best_methods.append(entries.iloc[0])

    # Final view
    for category in df["category"].unique():
        print(category)
        print(
            df.loc[
                (df.method.isin(best_methods))
                & (df.threshold.isin(thresholds))
                & (df["category"] == category)
            ]
            .sort_values(by=["passed"], ascending=False)
            .head(2)
            .sort_values("time average (ms)")[["threshold", "method"]]
        )


if __name__ == "__main__":
    df_raw = get_data()
    if df_raw.empty:
        print("Skip program because no data to process.")
    else:
        plot2x2_data(df_raw, "passed")
        plot2x2_data(df_raw, "time average (ms)")
        ranking(df_raw)
        plt.show()
