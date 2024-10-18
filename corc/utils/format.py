import sys


def error_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
