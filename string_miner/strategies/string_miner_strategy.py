class StringMinerStrategy:
    name = None
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def annotate_token(self, token, token_before=None, token_after=None, next_meta_info=None, level=0) -> ():
        """
        first tuple element is match score
        second tuple element is type of token
        third tuple element is annotation
        """
        pass
