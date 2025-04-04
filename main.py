import os
import subprocess
import shutil
from checkers.db_models import *

import json

def main():
    pass

def clone_db():
    if os.path.exists('db'):
        shutil.rmtree('db')
    token = os.getenv('GITHUB_TOKEN')
    result = subprocess.run(['git', 'clone', '--branch', 'db', f'https://oauth2:{token}@github.com/ruyisdk/ruyi-packaging.git', 'db'])
    result.check_returncode()

def update_db():
    check_info = parse_check_info('db/check_info.json')
    for item in check_info:
        if item.check_type == CheckType.GITHUB:
            pass
        elif item.check_type == CheckType.TUNA:
            pass  # Handle TUNA case


if __name__ == "__main__":
    main()
