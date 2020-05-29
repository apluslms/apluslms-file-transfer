class Colors:
    """Define a set of color patterns for printing"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class fg:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class bg:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'


class PrintColor:
    """Print messages with colors"""
    @staticmethod
    def header(msg):
        print(Colors.fg.purple + Colors.bold + msg + Colors.ENDC)

    @staticmethod
    def info(msg):
        print(Colors.fg.orange + msg + Colors.ENDC)

    @staticmethod
    def success(msg):
        print(Colors.fg.yellow + Colors.bold + msg + Colors.ENDC)

    @staticmethod
    def warn(msg):
        print(Colors.WARNING + msg + Colors.ENDC)

    @staticmethod
    def err(msg):
        print(Colors.FAIL + Colors.bold + msg + Colors.ENDC)
