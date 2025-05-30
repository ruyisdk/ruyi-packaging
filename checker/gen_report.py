import json
import os
from typing import List
from checker import main as checker_main
from gen_check_info import parse_single_file, get_files
from lib.db_models import CheckInfoElement, CheckResultElement, CheckType

checker_main()

# parse db.check_result.json to list[CheckResultElement]
def parse_check_results(file_path: str) -> List[CheckResultElement]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return [CheckResultElement(**item) for item in data]

def parse_check_info(file_path: str) -> List[CheckInfoElement]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return [CheckInfoElement(**item) for item in data]

def main():
    results = parse_check_results('db/check_results.json')    
    infos = parse_check_info('db/check_info.json')
    files = get_files()
    dist_infos = [parse_single_file(file) for file in files]
    
    if os.path.exists('report.md'):
        os.remove('report.md')
    with open('report.md', 'w', encoding="utf-8") as report:
        report.write("| 状态 | 最新文件 | 当前版本 | 源文件 | 名称 |\n")
        report.write("| ---- | -------- | ------ | -------- |\n")
        for info in infos:
            result = next((r for r in results if r.name == info.name), None)
            if info.check_type == CheckType.UNKNOWN.value or info.check_type == CheckType.UNKNOWN_AND_INACCESSIBLE.value:
                continue
            if info.name == "ruyi":
                continue

            if result:
                status = ""
                if result.failed:
                    status = "❌"
                elif result.current_version == result.result:
                    status = "✅"
                else:
                    status = "⚠️"
                latest_file = result.current_version
                current_version = result.result
                source_file = ""
                for dist_info in dist_infos:
                    for file in dist_info:
                        if file.name == info.name:
                            source_file = file.path
                            break
                file_path = info.name
                report.write(f"| {status} | {latest_file} | {current_version} | {source_file} | {file_path} |\n")
            else:
                report.write(f"| ❓ | - | - | {info.name} |\n")

if __name__ == "__main__":
    main()
    print("Report generated: report.md")