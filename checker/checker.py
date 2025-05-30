
import json
import os
import subprocess
import shutil

from lib.db_models import CheckInfoElement, CheckType, parse_check_info
from lib.checker_base import CheckerBase
from lib.checker import check_all

TEST = True

def main():
    clone_db()
    update_db()
    push_db()
    pass

def clone_db():
    if os.path.exists('db'):
        shutil.rmtree('db')
    token = os.getenv('GITHUB_TOKEN')
    result = subprocess.run(['git', 'clone', '--branch', 'db', f'https://oauth2:{token}@github.com/{"Cyl18" if TEST else "ruyisdk"}/ruyi-packaging.git', 'db'])
    result.check_returncode()

def update_db():
    path = 'db/check_info.json'
    check_info = parse_check_info(open(path).read())
    check_results = check_all(check_info)
    if os.path.exists('db/check_results.json'):
        os.remove('db/check_results.json')
    with open('db/check_results.json', 'w') as f:
        json.dump([result.__dict__ for result in check_results], f, indent=4)

def push_db():
    # switch to db directory
    if TEST:
        return
    os.chdir('db')
    subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions[bot]'])
    subprocess.run(['git', 'config', '--global', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'])

    subprocess.run(['git', 'add', '-A'])
    result = subprocess.run(['git', 'commit', '-m', 'update check results'])
    if result.returncode != 0:
        print("No changes to commit")
        return
    subprocess.run(['git', 'push', 'origin', 'db'])
    pass


if __name__ == "__main__":
    main()
