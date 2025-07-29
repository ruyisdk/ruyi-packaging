from pathlib import Path

from .config import use_base_dir, use_ruyi_iscas_repo

basedir = Path(__file__).resolve().parent.parent.parent
"""
project directory
"""

datadir = basedir / 'cache' if use_base_dir else Path('~/.cache/riko/').expanduser()
"""
data or cache files
"""

nvchecker_datadir = datadir / 'nvchecker'
"""
nvchecker files
"""

ruyi_datadir = datadir / 'ruyi'
"""
ruyi files
"""

ruyi_config_dir = ruyi_datadir / 'config'
ruyi_data_dir = ruyi_datadir / 'local'
ruyi_cache_dir = ruyi_datadir / 'cache'
ruyi_state_dir = ruyi_datadir / 'state'


riko_datadir = datadir / 'riko'
"""
riko files
"""

ruyi_config = '''
[telemetry]
mode = "local"
'''
"""
ruyi config toml file
"""

ruyi_config_extra = '''
[repo]
remote = "https://mirror.iscas.ac.cn/git/ruyisdk/packages-index.git"
''' if use_ruyi_iscas_repo else ""
"""
ruyi extra config
"""
