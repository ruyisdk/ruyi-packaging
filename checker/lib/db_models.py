from dataclasses import dataclass
from enum import Enum
import json

class CheckType(Enum):
    UNKNOWN = 'unknown'
    UNKNOWN_AND_INACCESSIBLE = 'unknown_inaccessible'
    GITHUB = 'github'
    OPENWRT = 'openwrt'
    OPENEULER_LPI4A = 'openeuler_lpi4a'
    REVYOS = 'revyos'
 

@dataclass
class CheckInfoElement:
    name: str
    check_path: str
    check_type: CheckType

@dataclass
class CheckResultElement:
    name: str
    result: str
    failed: bool

# [{"name":"ruyi","check_path": "", "check_type": "github"}]
def parse_check_info(json_str: str):
    check_info = []
    for item in json.loads(json_str):
        check_info.append(CheckInfoElement(
            name=item['name'],
            check_path=item['check_path'],
            check_type=CheckType(item['check_type'])
        ))
    return check_info