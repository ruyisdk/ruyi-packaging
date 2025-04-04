import os
import subprocess
import shutil
from checkers.db_models import *
from checkers.checker_base import *
import json

TEST = True

def main():
    clone_db()
    update_db()
    pass

def clone_db():
    if os.path.exists('db'):
        shutil.rmtree('db')
    token = os.getenv('GITHUB_TOKEN')
    result = subprocess.run(['git', 'clone', '--branch', 'db', f'https://oauth2:{token}@github.com/{'Cyl18' if TEST else 'ruyisdk'}/ruyi-packaging.git', 'db'])
    result.check_returncode()

def update_db():
    check_info = parse_check_info('db/check_info.json')
    check_results = CheckerBase.check_all(check_info)
    with open('db/check_results.json', 'w') as f:
        json.dump([result.__dict__ for result in check_results], f, indent=4)

def push_db():
    pass


if __name__ == "__main__":
    main()
