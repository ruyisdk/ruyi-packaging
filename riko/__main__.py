#!/usr/bin/env python3

import argparse
import sys

from riko.rikoriko import get_riko
from riko.cli.action import ActionRiko

if __name__ == '__main__':

    myriko = get_riko()

    # riko does not know what ruyi/nvchecker had done
    myriko.load_from_cache()

    parser = argparse.ArgumentParser(prog="riko", description="Riko: the Ruyi Packaging Bot")
    parser.add_argument("action", type=str, choices=["check"], action=ActionRiko, help="riko action")

    if "-h" in sys.argv or "--help" in sys.argv or len(sys.argv) > 2:
        parser.print_help()
    else:
        parser.parse_args()
