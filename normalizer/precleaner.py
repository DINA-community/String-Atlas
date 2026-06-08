import re


class PreCleaner:

    @staticmethod
    def pre_filter(text:str) -> str | None:
        # TODO thesis

        if isinstance(text, float):
            return None

        text = text.replace('(', '').replace(')', '')

        if (text.count(',') > 2
                or text.count(' or ') > 0 or text.count(' and ') > 0 or text.count(';') > 0):
            return None
        text = text.strip(',.:')


        if text == "":
            return None
        return text

    @staticmethod
    def pre_filter_csaf_vendors(vendor:str) -> str|None:
        # TODO thesis

        if isinstance(vendor, float):
            return None

        if (vendor.count(',') > 2
                or vendor.count(' or ') > 0 or vendor.count(' and ') > 0 or vendor.count(';') > 0 or vendor.count(' for ') > 0):
            return None
        vendor = vendor.strip(',.:')
        if vendor == "":
            return None
        return vendor

    # see 15 start
    @staticmethod
    def remove_csaf_product_version_tokens(product_name: str) -> str | None:
        if not isinstance(product_name, str):
            return None

        version_patterns = (
            r'(?i)\b(?:prior\s+to|up\s+to|through)\s+(?:version\s*)?v?\.?\s*\d+(?:\.\d+)*(?:\.?x)?\b',
            r'(?i)(?:<=|>=|<|>)\s*(?:version\s*)?v?\.?\s*\d+(?:\.\d+)*(?:\.?x)?\b',
            r'(?i)\bversion\s*[:=]?\s*v?\.?\s*\d+(?:\.\d+)*(?:\.?x)?\b',
            r'(?i)\brelease\s*[:=]?\s*v?\.?\s*\d+(?:\.\d+)*(?:\.?x)?\b',
            r'(?i)\b(?:service\s*pack|sp)\s*\d+\b',
            r'(?i)\b(?:update|patch(?:\s*level)?)\s*\d+(?:\.\d+)*\b',
            r'(?i)(?<![a-z0-9])v\.?\s*\d+(?:\.\d+)*(?:\.?x)?\b',
            r'(?i)(?<![a-z0-9])r\s*\d+(?:\.\d+){0,3}\b',
            r'(?i)(?<![a-z0-9])\d+(?:\.\d+)*\.x\b',
            r'(?i)(?<![a-z0-9])\d+(?:\.\d+)+(?![a-z0-9.])',
        )

        cleaned = product_name
        for pattern in version_patterns:
            cleaned = re.sub(pattern, ' ', cleaned)

        if cleaned != product_name:
            cleaned = re.sub(r'(?i)\b(?:and\s+prior|or\s+earlier)\b', ' ', cleaned)

        cleaned = re.sub(r'\(\s*\)|\[\s*\]|\{\s*\}', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip(' \t\r\n,.;:-_/')
        return cleaned or None
    # see 15 end