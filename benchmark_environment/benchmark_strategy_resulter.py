#!/usr/bin/env python3
"""Evaluate benchmark strategy result CSV files.

The input files are expected to have names such as:

    system_2024_2026_vector_fuzzy_exact_0.8.csv

The strategy order is read from the strategy tokens in the filename
(`exact`, `fuzzy`, `vector`) and the trailing number is used as threshold.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from html import escape
from pathlib import Path


STRATEGY_NAMES = {"exact", "fuzzy", "vector"}
DEFAULT_RESULTS_DIR = Path("results")
DEFAULT_CHART_PATH = Path("benchmark_strategy_results.svg")
CHART_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
    "#003f5c",
    "#bc5090",
    "#ffa600",
    "#58508d",
    "#00876c",
]


@dataclass(frozen=True)
class ResultRow:
    file: Path
    strategies: tuple[str, ...]
    threshold: float
    category: str
    count_tests: int
    failed: int
    passed: int
    time_all_ms: float
    time_average_ms: float


@dataclass(frozen=True)
class TotalResult:
    file: Path
    strategies: tuple[str, ...]
    threshold: float
    count_tests: int
    failed: int
    passed: int
    time_all_ms: float
    time_average_ms: float


def parse_result_filename(path: Path) -> tuple[tuple[str, ...], float]:
    parts = path.stem.split("_")
    if not parts:
        raise ValueError("filename has no parseable parts")

    try:
        threshold = float(parts[-1])
    except ValueError as exc:
        raise ValueError("filename does not end with a float threshold") from exc

    strategies = tuple(part for part in parts[:-1] if part in STRATEGY_NAMES)
    if not strategies:
        raise ValueError("filename does not contain any known strategy")

    return strategies, threshold


def parse_int(value: str) -> int:
    return int(float(value))


def read_result_file(path: Path) -> list[ResultRow]:
    strategies, threshold = parse_result_filename(path)
    rows: list[ResultRow] = []

    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {
            "category",
            "count tests",
            "failed",
            "passed",
            "time at all (ms)",
            "time average (ms)",
        }
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"missing required columns: {missing}")

        for row in reader:
            rows.append(
                ResultRow(
                    file=path,
                    strategies=strategies,
                    threshold=threshold,
                    category=row["category"],
                    count_tests=parse_int(row["count tests"]),
                    failed=parse_int(row["failed"]),
                    passed=parse_int(row["passed"]),
                    time_all_ms=float(row["time at all (ms)"]),
                    time_average_ms=float(row["time average (ms)"]),
                )
            )

    return rows


def collect_rows(results_dir: Path) -> list[ResultRow]:
    if not results_dir.exists():
        raise FileNotFoundError(f"results directory not found: {results_dir}")

    rows: list[ResultRow] = []
    skipped_files: list[tuple[Path, str]] = []

    for path in sorted(results_dir.glob("*.csv")):
        try:
            rows.extend(read_result_file(path))
        except ValueError as exc:
            skipped_files.append((path, str(exc)))

    if skipped_files:
        print("Skipped files:")
        for path, reason in skipped_files:
            print(f"  - {path}: {reason}")
        print()

    return rows


def best_by_category(rows: list[ResultRow]) -> dict[str, list[ResultRow]]:
    grouped: dict[str, list[ResultRow]] = {}
    for row in rows:
        grouped.setdefault(row.category, []).append(row)

    best: dict[str, list[ResultRow]] = {}
    for category, category_rows in grouped.items():
        max_passed = max(row.passed for row in category_rows)
        best[category] = [
            row for row in category_rows if row.passed == max_passed
        ]

    return dict(sorted(best.items()))


def totals_by_file(rows: list[ResultRow]) -> list[TotalResult]:
    grouped: dict[Path, list[ResultRow]] = {}
    for row in rows:
        grouped.setdefault(row.file, []).append(row)

    totals: list[TotalResult] = []
    for file, file_rows in grouped.items():
        count_tests = sum(row.count_tests for row in file_rows)
        failed = sum(row.failed for row in file_rows)
        passed = sum(row.passed for row in file_rows)
        time_all_ms = sum(row.time_all_ms for row in file_rows)
        time_average_ms = time_all_ms / count_tests if count_tests else 0.0
        first_row = file_rows[0]
        totals.append(
            TotalResult(
                file=file,
                strategies=first_row.strategies,
                threshold=first_row.threshold,
                count_tests=count_tests,
                failed=failed,
                passed=passed,
                time_all_ms=time_all_ms,
                time_average_ms=time_average_ms,
            )
        )

    return totals


def best_totals(rows: list[ResultRow]) -> list[TotalResult]:
    totals = totals_by_file(rows)
    if not totals:
        return []

    max_passed = max(total.passed for total in totals)
    return [total for total in totals if total.passed == max_passed]


def strategy_text(strategies: tuple[str, ...]) -> str:
    return " -> ".join(strategies)


def strategy_key(strategies: tuple[str, ...]) -> str:
    return "_".join(strategies)


def print_category_results(best: dict[str, list[ResultRow]]) -> None:
    print("Beste Ergebnisse pro Kategorie")
    print(
        "category | passed | failed | count tests | threshold | strategies | "
        "time all ms | time avg ms | file"
    )
    print("-" * 120)

    for category, rows in best.items():
        for row in sorted(rows, key=lambda item: (item.threshold, item.strategies)):
            print(
                f"{category} | {row.passed} | {row.failed} | {row.count_tests} | "
                f"{row.threshold:.1f} | {strategy_text(row.strategies)} | "
                f"{row.time_all_ms:.3f} | {row.time_average_ms:.3f} | {row.file}"
            )


def print_total_results(totals: list[TotalResult]) -> None:
    print()
    print("Beste Ergebnisse gesamt")
    print(
        "passed | failed | count tests | threshold | strategies | "
        "time all ms | time avg ms | file"
    )
    print("-" * 100)

    for total in sorted(totals, key=lambda item: (item.threshold, item.strategies)):
        print(
            f"{total.passed} | {total.failed} | {total.count_tests} | "
            f"{total.threshold:.1f} | {strategy_text(total.strategies)} | "
            f"{total.time_all_ms:.3f} | {total.time_average_ms:.3f} | {total.file}"
        )


def build_chart_panels(rows: list[ResultRow]) -> dict[str, dict[tuple[str, ...], list[tuple[float, int]]]]:
    panels: dict[str, dict[tuple[str, ...], list[tuple[float, int]]]] = {}

    for row in rows:
        panels.setdefault(row.category, {}).setdefault(row.strategies, []).append(
            (row.threshold, row.passed)
        )

    for total in totals_by_file(rows):
        panels.setdefault("All categories", {}).setdefault(total.strategies, []).append(
            (total.threshold, total.passed)
        )

    for series in panels.values():
        for points in series.values():
            points.sort()

    return dict(sorted(panels.items()))


def text_element(x: float, y: float, text: str, size: int = 12, weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#222">{escape(text)}</text>'
    )


def line_element(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 1.0) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width:.1f}" />'
    )


def polyline_element(points: list[tuple[float, float]], color: str) -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'<polyline points="{point_text}" fill="none" stroke="{color}" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />'
    )


def circle_element(x: float, y: float, color: str) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}" />'


def nice_ticks(max_value: int, steps: int = 4) -> list[int]:
    if max_value <= 0:
        return [0]

    raw_step = max(1, max_value / steps)
    magnitude = 10 ** (len(str(int(raw_step))) - 1)
    candidates = [1, 2, 5, 10]
    step = min(
        candidate * magnitude
        for candidate in candidates
        if candidate * magnitude >= raw_step
    )
    top = int(((max_value + step - 1) // step) * step)
    return list(range(0, top + 1, int(step)))


def write_svg_chart(rows: list[ResultRow], output_path: Path) -> None:
    panels = build_chart_panels(rows)
    all_strategies = sorted({row.strategies for row in rows}, key=strategy_key)
    color_by_strategy = {
        strategy: CHART_COLORS[index % len(CHART_COLORS)]
        for index, strategy in enumerate(all_strategies)
    }

    width = 1600
    title_height = 54
    legend_width = 330
    chart_gap = 34
    left_margin = 72
    right_margin = 24
    top_margin = 42
    bottom_margin = 56
    panel_width = (width - legend_width - left_margin - right_margin - chart_gap) / 2
    panel_height = 390
    plot_left_padding = 56
    plot_top_padding = 44
    plot_right_padding = 20
    plot_bottom_padding = 46
    panel_rows = (len(panels) + 1) // 2
    height = title_height + top_margin + panel_rows * panel_height + bottom_margin

    svg: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="#ffffff" />',
        text_element(32, 34, "Benchmark strategy results", 22, "700"),
        text_element(32, 54, "Passed tests by threshold and strategy order", 13),
    ]

    thresholds = sorted({row.threshold for row in rows})
    min_threshold = min(thresholds)
    max_threshold = max(thresholds)

    for index, (title, series) in enumerate(panels.items()):
        col = index % 2
        row = index // 2
        panel_x = left_margin + col * (panel_width + chart_gap)
        panel_y = title_height + top_margin + row * panel_height
        plot_x = panel_x + plot_left_padding
        plot_y = panel_y + plot_top_padding
        plot_width = panel_width - plot_left_padding - plot_right_padding
        plot_height = panel_height - plot_top_padding - plot_bottom_padding
        max_passed = max(point[1] for points in series.values() for point in points)
        y_ticks = nice_ticks(max_passed)
        y_max = max(y_ticks)

        svg.append(
            f'<rect x="{panel_x:.1f}" y="{panel_y:.1f}" width="{panel_width:.1f}" '
            f'height="{panel_height - 16:.1f}" fill="#fafafa" stroke="#dddddd" />'
        )
        svg.append(text_element(panel_x, panel_y - 10, title, 15, "700"))

        for tick in y_ticks:
            y = plot_y + plot_height - (tick / y_max * plot_height if y_max else 0)
            svg.append(line_element(plot_x, y, plot_x + plot_width, y, "#e6e6e6"))
            svg.append(text_element(plot_x - 46, y + 4, str(tick), 11))

        for threshold in thresholds:
            x = plot_x + (
                (threshold - min_threshold) / (max_threshold - min_threshold) * plot_width
                if max_threshold != min_threshold
                else 0
            )
            svg.append(line_element(x, plot_y, x, plot_y + plot_height, "#eeeeee"))
            svg.append(text_element(x - 9, plot_y + plot_height + 22, f"{threshold:.1f}", 11))

        svg.append(line_element(plot_x, plot_y, plot_x, plot_y + plot_height, "#222222", 1.2))
        svg.append(
            line_element(
                plot_x,
                plot_y + plot_height,
                plot_x + plot_width,
                plot_y + plot_height,
                "#222222",
                1.2,
            )
        )
        svg.append(text_element(plot_x + plot_width / 2 - 28, panel_y + panel_height - 34, "threshold", 12))
        svg.append(text_element(panel_x + 2, plot_y - 12, "passed", 12))

        for strategy, points in sorted(series.items(), key=lambda item: strategy_key(item[0])):
            color = color_by_strategy[strategy]
            scaled_points = [
                (
                    plot_x
                    + (
                        (threshold - min_threshold)
                        / (max_threshold - min_threshold)
                        * plot_width
                        if max_threshold != min_threshold
                        else 0
                    ),
                    plot_y + plot_height - (passed / y_max * plot_height if y_max else 0),
                )
                for threshold, passed in points
            ]
            svg.append(polyline_element(scaled_points, color))
            for x, y in scaled_points:
                svg.append(circle_element(x, y, color))

    legend_x = width - legend_width + 26
    legend_y = title_height + top_margin
    svg.append(text_element(legend_x, legend_y - 12, "Strategies", 15, "700"))
    for index, strategy in enumerate(all_strategies):
        y = legend_y + index * 28
        color = color_by_strategy[strategy]
        svg.append(line_element(legend_x, y, legend_x + 28, y, color, 3.0))
        svg.append(circle_element(legend_x + 14, y, color))
        svg.append(text_element(legend_x + 38, y + 4, strategy_text(strategy), 12))

    svg.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Find the strategy/threshold combinations with the most passed tests "
            "per category and overall."
        )
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="directory containing result CSV files (default: results)",
    )
    parser.add_argument(
        "--chart",
        type=Path,
        default=DEFAULT_CHART_PATH,
        help=(
            "path for the generated SVG chart "
            f"(default: {DEFAULT_CHART_PATH})"
        ),
    )
    parser.add_argument(
        "--no-chart",
        action="store_true",
        help="only print the text evaluation and do not write a chart",
    )
    args = parser.parse_args()

    rows = collect_rows(args.results_dir)
    if not rows:
        print(f"No result rows found in {args.results_dir}")
        return 1

    print_category_results(best_by_category(rows))
    print_total_results(best_totals(rows))
    if not args.no_chart:
        write_svg_chart(rows, args.chart)
        print()
        print(f"Diagramm geschrieben: {args.chart}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
