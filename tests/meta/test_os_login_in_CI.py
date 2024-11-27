import os
import warnings


def test_os_login():
    try:
        assert os.getlogin()
    except OSError:
        warnings.warn("os.getlogin() failed")


def test_os_uname():
    assert os.uname()


def test_os_uname_nodename():
    assert os.uname().nodename
