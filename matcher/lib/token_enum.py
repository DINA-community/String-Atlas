from enum import Enum

class TokenSemanticEnum(Enum):
    VENDOR = "vendor"
    VENDOR_ID = "vendor_id"
    BRAND = "brand"
    BRAND_ID = "brand_id"
    SERIES = "series"
    SUBSERIES = "subseries"
    NORMALIZED = "normalized"
    UNIQUE = "unique"
    CSAF_REF = "csaf_ref"
    MULTIPLE = "multiple"

    TEXTMINER_VENDOR_NORMALIZED = "vendor_csaf_normalized"
