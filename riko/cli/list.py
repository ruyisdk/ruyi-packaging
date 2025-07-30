"""
List nvchecker results
"""

import json
import sys

from ..rikoriko import get_riko

def list_result(event: str) -> None:
    """
    List nvchecker result event or level, "no-result" and "error" usually associate with check failure
    :param event: nvchecker result json item "event" {updated,up-to-date,no-result},
    or "level" {debug, info, error}, or {any}
    :return:
    """
    res: list[dict] = get_riko().get_nvchecker_results(event)

    json.dump(res, sys.stdout, indent=2, sort_keys=False)
