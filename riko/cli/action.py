import argparse

from .check import check

class ActionRiko(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(ActionRiko, self).__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values == "check":
            check()
