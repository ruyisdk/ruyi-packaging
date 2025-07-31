#!/usr/bin/env python3

import argparse
import logging
import sys

from riko.cli.check import check
from riko.cli.list import list_result
from riko.cli.manifests import manifests
from riko.rikoriko import get_riko

logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':

    myriko = get_riko()

    # riko does not know what ruyi/nvchecker had done
    myriko.load_from_cache()

    parser = argparse.ArgumentParser(prog="riko", description="Riko: the Ruyi Packaging Bot")
    subparsers = parser.add_subparsers(dest="subcommand", help="sub-commands")

    subparser = subparsers.add_parser("check", help="Fetch data and refresh local cache")
    subparser.set_defaults(func=lambda args: check())

    subparser = subparsers.add_parser("list", help="List nvchecker result event or level")
    subparser.add_argument("event", help="event or level, default `updated`", default="updated", nargs="?",
                           choices=["any", "updated", "up-to-date", "no-result", "debug", "info", "error"])
    subparser.set_defaults(func=lambda args: list_result(args.event))

    subparser = subparsers.add_parser("manifests", help="Generate new packages-index manifests from old ones")
    subparser.add_argument("up_name", type=str, help="upstream name")
    subparser.add_argument("gen_vers", nargs="*", help="specify new versions, or use nvchecker result")
    subparser.set_defaults(func=lambda args: manifests(args.up_name, args.gen_vers))

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        myfunc = parser.parse_args()
        myfunc.func(myfunc)
