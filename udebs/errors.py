class UdebsError(Exception):
    """Base class for all Udebs errors."""
    pass

class UdebsSyntaxError(UdebsError):
    """Is raised when an effect or require is malformed and fails to parse."""
    def __init__(self, string):
        self.message = string
    def __str__(self):
        return repr(self.message)

class UdebsExecutionError(UdebsError):
    """Is raised when an error occurs during execution of a udebs action."""
    def __init__(self, script):
        self.script = script
    def __str__(self):
        return "invalid '{}'".format(self.script.raw)

class UndefinedSelectorError(UdebsError):
    """Is raised when udebs encounters an invalid reference to a udebs object."""
    def __init__(self, target, _type):
        self.selector = target
        self.type = _type
    def __str__(self):
        return "{} is not a valid {} selector.".format(repr(self.selector), self.type)