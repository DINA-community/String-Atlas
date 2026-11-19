import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from benchmark.subcategory_factory import BenchmarkSubcategoryFactory
from benchmark.benchmark_suite import BenchmarkCaseManager, BenchmarkGoetterdammerung


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark cases from a CSV file.")
    parser.add_argument(
        "csv_file",
        type=str,
        help="Relative or absolute path to the benchmark CSV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    test_suite_manager = BenchmarkCaseManager()
    test_suite_manager.load(args.csv_file, BenchmarkSubcategoryFactory())

    benchmark_groups = test_suite_manager.get_benchmark_groups()
    # benchmark_groups = {"Test – Lexical errors": benchmark_groups["Test – Lexical errors"]}

    total = sum(
        len(case.get_queryset())
        for group in benchmark_groups.values()
        for sub_group in group.get_sub_groups().values()
        for case in sub_group.get_cases()
    )
    print("Total number of test cases: {}".format(total))

    match_strategies = ["exact_match_strategy", "fuzzy_match_strategy", "vector_match_strategy"]
    config = {"fuzzy_match_strategy_threshold": 0.8, "vector_match_strategy_threshold": 0.8}
    target_system_b = BenchmarkGoetterdammerung(api_key="1234567890abcdef", url="http://localhost:5002/api/match_all_with_strategies", match_strategies=match_strategies, config=config)
    count, count_all, ground_truth_suggestions, results = target_system_b.run(benchmark_groups)

    for category in count.keys():
        print("{} - {} from {} cases succeeded".format(category, count[category], count_all[category]))

    print("following suggestions are not matched:")
    print(ground_truth_suggestions)

    test_suite_manager.attach_results(results, count, count_all)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    test_suite_manager.save_details(f"details_{timestamp}.csv", with_results=False)
    test_suite_manager.save_results(f"results_{timestamp}.csv")

if __name__ == "__main__":
    main()
