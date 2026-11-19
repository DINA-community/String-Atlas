from normalizer.database.csaf_database_helper import CSAFDataBaseHelper


class Visitor:
    database_helper = None
    vendor = None
    brand = None

    def __init__(self, database_helper:CSAFDataBaseHelper, vendor, brand):
        self.database_helper = database_helper
        self.vendor = vendor
        self.brand = brand

    def visit(self, node):
        pass
