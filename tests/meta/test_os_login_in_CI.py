import os


def test_os_login():
    assert os.getlogin()


def test_os_uname():
    assert os.uname()


def test_os_uname_nodename():
    assert os.uname().nodename
