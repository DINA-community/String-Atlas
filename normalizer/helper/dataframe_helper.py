import pandas as pd
from collections import Counter


class DataFrameHelper:
    DEFAULT_STORE_KEY = 'DEFAULT'

    COLUMN_ANNOTATION_PRODUCT_NAME = 'annotation_product_name'
    COLUMN_VALUE_PRODUCT_NAME = 'product_name'
    COLUMN_PROCESSED_PRODUCT = 'processed_product_name'
    COLUMN_REGEX_PRODUCT_NAME = 'regex_product_name'

    df_store = {'DEFAULT': None}
    store_key_index = []
    word_index = {}

    def __init__(self, df):
        self.df_store[self.DEFAULT_STORE_KEY] = df

    def raw_load(self, store_key_src: str) -> pd.DataFrame:
        return self.df_store[store_key_src]

    def raw_save(self, store_key_tgt, df):
        self.df_store[store_key_tgt] = df

    def filter_corpus_column(self, store_key_src:str, store_key_tgt:str, columns: list, search_terms:list, blacklist: list = None,
                             regex_pattern:str=None) -> pd.DataFrame:
        if regex_pattern is None:
            regex_pattern = []
        corpus = self.df_store[store_key_src]
        column = columns[0]
        # TODO mehrere columns bzw. komplexere suche

        blacklist = [x.lower() for x in blacklist]

        if search_terms is None:
            if isinstance(search_terms, list) and len(regex_pattern) > 0:
                corpus.loc[:,column] = corpus.loc[
                    corpus[column].apply(
                        lambda x: not any(term.lower() in x for term in blacklist)
                                  and bool(pd.Series(x).str.contains(regex_pattern[0], case=False, regex=True).any())
                    )
                ]
            else:
                # TODO blacklist anwenden
                corpus = corpus[
                    corpus[column].fillna("").apply(lambda x: not any(term in x for term in blacklist))
                ]
        else:
            if isinstance(search_terms, list) and len(regex_pattern) > 0:
                corpus.loc[:,column] = corpus.loc[
                    corpus[column].apply(
                        lambda x: all(term in x for term in search_terms)
                                  and not any(term in x for term in blacklist)
                                  and bool(pd.Series(x).str.contains(regex_pattern[0], case=False, regex=True).any())
                    )
                ]
            elif isinstance(search_terms, list):
                corpus.loc[:,column] = corpus.loc[
                    corpus[column].apply(
                        lambda x: all(term in x for term in search_terms)
                                  and not any(term in x for term in blacklist)
                    )
                ]
            else:
                # TODO blacklist anwenden
                corpus.loc[:,column] = corpus.loc[
                    corpus[column].str.contains(search_terms, case=False)
                ]
        self.df_store[store_key_tgt] = corpus
        return corpus


    # kostenintensiv -> hier nach n wörtern abbrechen
    # TODO case insenstive noch reinbringen, aber semantic darf nicht verloren gehen bei "proCPU" oder "CPUpro"
    def create_word_statistics(self, store_key_src:str, column:str):
        # TODO nach Text Mining auslagern, erstmal string_miner ignorieren. kann auch für eingabe eher hilfreich sein
        total_counts = sum(self.df_store[store_key_src][column].apply(self._count_token), Counter())
        word_stats = [total_counts.most_common()]

        run = True
        n = 2
        # TODO n < 8 rausmachen
        # TODO korrigierte Version
        # self.df_store[store_key_src][column + '_' + str(n) + '_gram_counts'] = self.df_store[store_key_src][column].apply(
        #     lambda x: self._count_ngrams(x, n))
        while run is True and n < 8:
            # TODO hier ist fehler
            self.df_store[store_key_src].loc[:, column + '_' + str(n) + '_gram_counts'] = self.df_store[store_key_src].loc[:, column].apply(lambda x: self._count_ngrams(x, n))

            total_bigram_counts = sum(self.df_store[store_key_src][column + '_' + str(n) + '_gram_counts'], Counter())

            ngrams_list = total_bigram_counts.most_common()
            if len(ngrams_list) > 0:
                word_stats.append(ngrams_list)
            else:
                run = False
            n = n + 1
        return word_stats

    # TODO falsche komponente -> corpus manager
    def _count_ngrams(self, text, n):
        tokens = text.split()  # Tokenisierung der Wörter (Trennung durch Leerzeichen)
        if len(tokens) < n:
            return Counter()

        grams = zip(*(tokens[i:] for i in range(n)))
        return Counter(grams)  # Zählen der Bigrams

    # TODO falsche komponente -> corpus manager
    def _count_token(self, text):
        return Counter(text.split())

    def init_vendor(self, store_key_src:str, vendor:str):
        df = self.raw_load(store_key_src)
        vendor_filtered_df = df.loc[df['vendor'] == vendor].copy()
        self.raw_save(vendor, vendor_filtered_df)
        return vendor_filtered_df
