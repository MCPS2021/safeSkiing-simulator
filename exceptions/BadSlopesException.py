class BadSlopesException(Exception):
    def __init__(self):
        super().__init__("Error in slopes configuration")