'''Introduction missing'''

import ast
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from benchmark.benchmark_suite import BenchmarkGoetterdammerung, BenchmarkCase

def parse_queryset(arguments: list[str]) -> list[str]:
    if not arguments:
        raise ValueError("Bitte mindestens eine Query angeben.")

    value = " ".join(arguments)
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        parsed = value

    if isinstance(parsed, list):
        if all(isinstance(query, str) and query.strip() for query in parsed):
            return [query.strip() for query in parsed]
        raise ValueError("Eine Query-Liste darf nur Strings enthalten.")

    query_text = parsed if isinstance(parsed, str) else value
    queryset = [query.strip() for query in query_text.split(",")]
    if not all(queryset):
        raise ValueError("Durch Komma getrennte Queries dürfen nicht leer sein.")
    return queryset

def main():
    queryset = parse_queryset(sys.argv[1:])
    benchmark_case = BenchmarkCase(test_type="Product", group=None, test_name="dummy", ground_truth=["DUMMY"], category="Test – Different Spelling", sub_category="different spelling - acronym", queryset=queryset, vendor="Siemens")

    match_strategies = ["exact_match_strategy", "fuzzy_match_strategy", "vector_match_strategy" ]
    config = {"fuzzy_match_strategy_threshold": 0.8, "vector_match_strategy_threshold": 0.8}
    target_system_a = BenchmarkGoetterdammerung(api_key="1234567890abcdef", url=f"http://localhost:5002/api/match_all_with_strategies", match_strategies=match_strategies, config=config)
    results = target_system_a.run_single(case=benchmark_case)

    for result in results:
        print("--------")
        print(f"Query: {result.query}")
        print(result.suggest)

if __name__ == "__main__":
    main()
