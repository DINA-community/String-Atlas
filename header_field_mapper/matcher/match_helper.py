class MatchHelper:

    @staticmethod
    def normalize_hits_scores(hits:{}):
        min_value = min(hits.values())
        max_value = max(hits.values())

        calculated_value = {}
        if min_value == max_value:
            for column, value in hits.items():
                calculated_value[column] = 0
            return calculated_value

        for column, value in hits.items():
            calculated_value[column] = (value - min_value) / (max_value - min_value)
        return calculated_value
