
from riko.rikoriko import get_riko
from riko.cli.check import check

def _riko_check():
    """
    All file are generate on local filesystem and all data are loaded (though program will end soon)
    :return:
    """
    check(get_riko())

if __name__ == '__main__':
    _riko_check()

    myriko = get_riko()
