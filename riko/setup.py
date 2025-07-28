import os
import subprocess

from .const import basedir, nvchecker_datadir, riko_datadir, ruyi_datadir, ruyi_cache_dir, ruyi_state_dir, \
    ruyi_data_dir, ruyi_config_dir, ruyi_config, ruyi_config_extra


def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def _ensure_riko_path() -> None:
    _ensure_dir(riko_datadir)


def _ensure_nvchecker_path() -> None:
    _ensure_dir(nvchecker_datadir)


def _ensure_ruyi_path() -> None:
    _ensure_dir(ruyi_datadir)
    _ensure_dir(ruyi_config_dir)
    _ensure_dir(ruyi_config_dir / 'ruyi')
    _ensure_dir(ruyi_data_dir)
    _ensure_dir(ruyi_cache_dir)
    _ensure_dir(ruyi_state_dir)


def _ensure_paths() -> None:
    """
    Ensures that the data directories exist.
    :return:
    """
    _ensure_riko_path()
    _ensure_nvchecker_path()
    _ensure_ruyi_path()


def _ensure_nvchecker_env() -> None:
    path = os.environ['PATH']
    os.environ['PATH'] = str(basedir / (':' + path))


def _ensure_ruyi_env() -> None:
    os.environ['XDG_CONFIG_HOME'] = str(ruyi_config_dir)
    os.environ['XDG_DATA_HOME'] = str(ruyi_data_dir)
    os.environ['XDG_CACHE_HOME'] = str(ruyi_cache_dir)
    os.environ['XDG_STATE_HOME'] = str(ruyi_state_dir)


def _ensure_envs() -> None:
    """
    Setup environment variables
    :return:
    """
    _ensure_nvchecker_env()
    _ensure_ruyi_env()


def setup() -> None:
    """
    Sets up all
    :return:
    """
    _ensure_paths()
    _ensure_envs()

    with open(ruyi_config_dir / 'ruyi/config.toml', "w") as cfg:
        cfg.write(ruyi_config + "\n" + ruyi_config_extra)

    # ruyi update
    cmd: list[str] = ["ruyi", "update"]
    env = os.environ.copy()
    rfd, wfd = os.pipe()

    process = subprocess.Popen(cmd, stdout=wfd, stderr=wfd, env=env)
    os.close(wfd)

    out = os.fdopen(rfd)
    output = out.read()
    out.close()

    ret = process.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, cmd, output)
