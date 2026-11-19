from enum import Enum
import pandas as pd
import requests
from abc import ABC, abstractmethod
from benchmark.subcategory_factory import BenchmarkSubcategoryFactoryStrategie
import time

class MatchReason(Enum):
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class BenchmarkTargetType(Enum):
    PRODUCT = "Product"
    VENDOR = "Vendor"


class BenchmarkCase:
    def __init__(self, test_type:BenchmarkTargetType, test_name: str, group: "BenchmarkGroup",
                 category:str,
                 sub_category: str,
                 ground_truth: list[str],
                 vendor: str, queryset: list[str]):
        self.test_type = test_type
        self.category = category
        self.ground_truth: list[str] = ground_truth
        self.test_name = test_name
        self.test_queryset: list[str] = queryset
        self.group: BenchmarkGroup = group
        self.sub_category: str = sub_category
        self.vendor: str = vendor

    def get_queryset(self) -> list[str]:
        return self.test_queryset

    def is_match(self, suggest: str):
        if suggest == 'SIMATIC S7-1500 CPU 1511F-1 PN ( 6ES7511-1FK02-0AB0':
            test = 2
        if suggest in self.ground_truth:
            return True
        contains_items = [x for x in self.ground_truth if "contains" in x]
        for check in contains_items:
            contains_in = check.split("\"")[1]
            if contains_in in suggest:
                return True
        return False


class BenchmarkSubGroup:
    cases: list[BenchmarkCase]
    category: str
    sub_category: str

    def __init__(self, category: str, sub_category: str):
        self.category = category
        self.sub_category = sub_category
        self.cases = []

    def add_case(self, case: BenchmarkCase):
        self.cases.append(case)

    def get_cases(self) -> list[BenchmarkCase]:
        return self.cases


class BenchmarkGroup:
    sub_groups: dict[str, BenchmarkSubGroup]
    category: str
    def __init__(self, category: str):
        self.category = category
        self.sub_groups = {}

    def add_sub_group(self, sub_group: BenchmarkSubGroup):
        self.sub_groups[sub_group.sub_category] = sub_group

    def get_sub_groups(self) -> dict[str, BenchmarkSubGroup]:
        return self.sub_groups

    def get_sub_category(self, sub_category):
        if sub_category in self.sub_groups:
            return self.sub_groups[sub_category]
        else:
            return None


class BenchmarkResult:
    def __init__(self, case: BenchmarkCase, is_match: bool, query: str, suggest: str|None, reason: MatchReason, csaf_ref: list[list[str, str]]=None):
        self.case: BenchmarkCase = case
        self.is_match: bool = is_match
        self.query: str = query
        self.suggest: str|None = suggest
        self.csaf_ref: list[list[str, str]]|None = csaf_ref
        self.reason:MatchReason = reason
        self.duration: float|None = None

    # TODO in diagramme
    def set_duration(self, duration:float):
        self.duration = duration

    def get_duration(self) -> float | None:
        return self.duration


class BenchmarkCaseManager:
    df: pd.DataFrame = None
    benchmark_groups:dict[str, BenchmarkGroup] = None
    benchmark_subcategory_factory:BenchmarkSubcategoryFactoryStrategie = None

    def __init__(self):
        self.results:dict[str,dict[str,str]]= None

    def attach_results(self, results: list[BenchmarkResult], count, count_all):
        i = - 1
        counter = 0
        product_subcategory_value = {}
        durations: dict[str,float] = {}
        for result in results:
            i = i + 1
            col_idx = self.df.columns.get_loc(result.case.test_name)

            col_name = "Result "+result.case.test_name
            if col_name not in self.df.columns:
                self.df.insert(col_idx + 1, col_name, "")


            indices = self.df.index[
                self.df.iloc[:, 1]
                .fillna("")
                .astype(str)
                .str.strip()
                ==
                str(result.case.sub_category).strip()
                ]

            try:
                row_pos = int(indices[0])
            except IndexError as err:
                print(f"IndexError: {err} for {result.case.test_name} in {result.case.sub_category}")
                print(result.case.test_name, result.case.sub_category, indices)
                continue

            key_col = col_name+str(row_pos)
            if key_col in product_subcategory_value:
                text_before = product_subcategory_value[key_col]
            else:
                text_before = ""

            if result.is_match and result.suggest is not None:
                text = "OK: "+result.suggest
            elif result.suggest is not None:
                text ="FAILED SUGGEST:"+result.suggest
            else:
                text = "FAILED"

            text = str(text_before+";"+text).lstrip(";")

            self.df.loc[row_pos, col_name] = text
            product_subcategory_value[key_col] = text

            if result.case.category not in durations:
                durations[result.case.category] = 0

            if durations[result.case.category] is not None:
                durations[result.case.category] += result.get_duration()


        self.results = {}
        for category in count.keys():
            self.results[category] = {"time at all": durations[category], "passed": count[category], "failed": count_all[category] - count[category], "all": count_all[category]}

    def save_results(self, filename:str):
        df = pd.DataFrame({
            "category": self.results.keys(),
            "count tests": [x["all"] for x in self.results.values()],
            "failed": [x["failed"] for x in self.results.values()],
            "passed": [x["passed"] for x in self.results.values()],
            "time at all (ms)": [x["time at all"] for x in self.results.values()],
            "time average (ms)": [float(x["time at all"] / x["all"]) for x in self.results.values()],
        })
        pd.DataFrame.to_csv(df, filename)


    def save_details(self, filename:str, with_results: bool = False):
        if with_results:
            df_ref = self.df.copy()
            for category, values in self.results.items():
                df_ref.loc[len(df_ref), self.df.columns[0]] = \
                    "{} - {} from {} cases succeeded".format(category, values["passed"], values["all"])
        else:
            df_ref = self.df
        pd.DataFrame.to_csv(df_ref, filename)


    def load(self, filename, benchmark_subcategory_factory: BenchmarkSubcategoryFactoryStrategie=None):
        df = pd.read_csv(filename)
        self.benchmark_subcategory_factory = benchmark_subcategory_factory
        self.df = df.fillna("").astype(str)
        self._init_benchmark_cases()

    def _init_benchmark_cases(self):
        self.benchmark_groups = {}
        benchmark_group = None
        # column C (Index 2) till the end
        for target_nr in range(2, len(self.df.columns)):

            product = None
            ground_truth = None
            vendor = None
            target_type = None
            for row_idx in range(len(self.df)):
                category = str(self.df.iloc[row_idx, 0]).strip()  # column A
                sub_category = str(self.df.iloc[row_idx, 1]).strip()  # column B

                value = str(self.df.iloc[row_idx, target_nr]).strip()
                if category == "Product":
                    if value == "":
                        break
                    product = value
                elif category == "Ground Truth":
                    ground_truth = value.split(";")
                elif category == "Vendor":
                    vendor = value
                elif category == "Type":
                    if value == "":
                        break
                    target_type = BenchmarkTargetType(value)
                elif category.startswith("Test"):

                    queryset = None
                    if value == "":
                        if self.benchmark_subcategory_factory:
                            subcategory_strategy = self.benchmark_subcategory_factory.create(sub_category)
                            if subcategory_strategy and target_type == BenchmarkTargetType.PRODUCT:
                                queryset = subcategory_strategy.process(vendor, product)
                                col_name = self.df.columns[target_nr]
                                # limited to 1
                                if len(queryset) > 0:
                                    query = queryset[0]
                                    queryset = [queryset[0]]
                                else:
                                    query = ""
                                self.df.loc[row_idx, col_name] = query
                    else:
                        queryset = self._clean_query_set(value.split(";"))

                    if queryset is None or len(queryset) == 0 or queryset[0] == "SKIP":
                        continue
                       # product, target_type, category, sub_category

                    if category not in self.benchmark_groups:
                        self.benchmark_groups[category] = BenchmarkGroup(
                            category=category
                        )
                    benchmark_group = self.benchmark_groups[category]

                    sub_group = benchmark_group.get_sub_category(sub_category=sub_category)
                    if not sub_group:
                        sub_group = BenchmarkSubGroup(category=category, sub_category=sub_category)
                        benchmark_group.add_sub_group(sub_group)

                    # queryset.insert(0, product)
                    if queryset is not None:
                        case = BenchmarkCase(
                            test_type=target_type,
                            group=benchmark_group,  # jetzt korrekt
                            test_name=product,
                            ground_truth=ground_truth,
                            category=category,
                            sub_category=sub_category,
                            queryset=queryset,
                            vendor=vendor
                        )
                        sub_group.add_case(case)



    def _clean_query_set(self, queryset: list[str]) -> list[str]:
        filtered = [x.strip() for x in queryset if x.strip() != "" and x != "SKIP"]
        return filtered

    def get_benchmark_groups(self) -> dict[str, BenchmarkGroup]:
        return self.benchmark_groups


class BenchmarkTargetSystem(ABC):

    def run(self, benchmark_groups: dict[str, BenchmarkGroup]) -> tuple[dict[str, int], dict[str, int],
    set[str], list[BenchmarkResult]]:
        results: list[BenchmarkResult] = []
        matches_category_count: dict[str, int] = {}
        matches_category_count_all: dict[str, int] = {}
        ground_truth_suggestions = set()
        counter = 0
        for group in benchmark_groups.values():
            for key_sub_group, sub_group in group.get_sub_groups().items():
                for case in sub_group.get_cases():

                    if "Lexical errors – wrong letter typing" in case.sub_category and case.test_name == "SIMATIC S7-1500":
                        counter = counter + 1

                    if case.test_type == BenchmarkTargetType.PRODUCT:
                        for query in case.test_queryset:

                            start = time.perf_counter()

                            response = self._run_product_benchmark(case, query)
                            is_match, evaluate = self.evaluate_response(case, response)

                            end = time.perf_counter()
                            duration_ms = (end - start) * 1000

                            if case.category not in matches_category_count_all:
                                matches_category_count_all[case.category] = 0
                                matches_category_count[case.category] = 0

                            matches_category_count_all[case.category] = matches_category_count_all[case.category] + 1

                            text = None
                            csaf_ref = None
                            reason = MatchReason.NO_MATCH
                            if is_match:
                                csaf_ref = evaluate["csaf_ref"]
                                matches_category_count[case.category] = matches_category_count[case.category] + 1
                                reason = MatchReason.FULL_MATCH
                                text = evaluate["text"]
                            elif evaluate is not None and evaluate["text"].strip() != "":
                                text = evaluate["text"]
                                ground_truth_suggestions.add(text)

                            result = BenchmarkResult(case, is_match, query, text, reason, csaf_ref=csaf_ref)
                            result.set_duration(duration_ms)
                            results.append(result)



        return matches_category_count, matches_category_count_all, ground_truth_suggestions, results

    def run_single(self, case: BenchmarkCase) -> list[BenchmarkResult]:
        results = []
        for query in case.test_queryset:
            response = self._run_product_benchmark(case, query)
            is_match, evaluate = self.evaluate_response(case, response)

            text = None
            csaf_ref = None
            reason = MatchReason.NO_MATCH
            if is_match:
                reason = MatchReason.FULL_MATCH
                text = evaluate["text"]
                csaf_ref = evaluate["csaf_ref"]
            elif evaluate is not None and evaluate["text"].strip() != "":
                text = evaluate["text"]

            result = BenchmarkResult(case, is_match, query, text, reason, csaf_ref=csaf_ref)
            results.append(result)
        return results

    def evaluate_response(self, case: BenchmarkCase, response) -> tuple[bool, dict]:

        # TODO reason full or partial match

        """
        {'matches': [
            {'id': 178, 'payload': {'category': 'brand_product', 'text': 'SIMATIC S7-1200', 'vendor': 'Siemens'},
             'score': 0.78096104, 'vector': None}]}
        """
        response = self.adapt_response(response)
        # TODO Adapter für REquest ->aber es ist System A2024 das untere gilt für System B 2026 Matcher
        if response:
            if case.is_match(response["text"]):
                return True, response
            else:
                return False, response
        return False, None

    @abstractmethod
    def _run_product_benchmark(self, case: BenchmarkCase, query: str):
        pass

    @abstractmethod
    def adapt_response(self, response):
        pass



class BenchmarkGoetterdammerung(BenchmarkTargetSystem):
    def __init__(self, api_key:str, url:str, match_strategies=None, config=None):
        if match_strategies is None:
            match_strategies = []
        if config is None:
            config = {}
        self.name = "Goetterdaemmerung"
        self.url = url
        self.api_key = api_key
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        self.match_strategies = match_strategies
        self.config = config

    def _run_product_benchmark(self, case: BenchmarkCase, query: str):
        payload = {
            "text": query,
            "match_strategies": self.match_strategies,
            "config": self.config
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=payload)
            # response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim API-Call: {e}")
            return None

    def adapt_response(self, response):
        """
                {'matches': {'SIMATIC IPC3000 SMART V3': {'annotations': [[], [], [], []],
                                                          'full_product_type': 'SIMATIC IPC3000 SMART V3',
                                                          'match_reason': 'brand', 'probability': 15,
                                                          'product_type': 'SIMATIC IPC3000 SMART V3',
                                                          'product_type_series': 'SIMATIC IPC3000',
                                                          'product_type_series_suggest': 'SIMATIC IPC3000',
                                                          'request_column': None, 'tokens':
                """
        if isinstance(response, list):
            item = response[0]
            text = next(iter(item))
            reason = item["matches"][text]["probability"]
            return {"text": text, "reason": reason, "csaf_ref": None}
        elif isinstance(response, dict) and "matches" in response and isinstance(response["matches"], list) and len(response["matches"]) > 0:
            if isinstance(response["matches"], list):
                text = response["matches"][0]["normalized"]
                if isinstance(text, list):
                    text = " ".join(text)
                reason = response["matches"][0]["reason"]
                csaf_ref = response["matches"][0]["csaf_ref"]
            else:
                # matcher2024
                print("2024")
                text = next(iter(response["matches"]))
                reason = response["matches"][text]["probability"]
                csaf_ref = None
            return {"text": text, "reason": reason, "csaf_ref": csaf_ref}
        return None
