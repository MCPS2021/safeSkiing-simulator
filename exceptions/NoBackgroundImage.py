class BadSlopesException(Exception):
    def __init__(self):
        super().__init__("No background image specified in the config file")