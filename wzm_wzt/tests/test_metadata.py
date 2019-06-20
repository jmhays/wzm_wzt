"""Unit and regression test for the metadata classes and functions."""

import pytest
import os
from wzm_wzt.metadata import MetaData, backup_file

def test_backups(tmpdir):
    fnm = "{}/backup_file_test.txt".format(tmpdir)
    with open(fnm, "w") as tmpfile:
        tmpfile.write("touch")
    
    backup_file(fnm, vtype='copy')
    backup_file(fnm, vtype='rename')

    assert 'backup_file_test.txt.1' in os.listdir(tmpdir)
    assert 'backup_file_test.txt.0' in os.listdir(tmpdir)