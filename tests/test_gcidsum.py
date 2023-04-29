# -*- coding: utf-8 -*-
#
# Copyright (c) 2022~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import os
import re
import subprocess
import tempfile
import pathlib

import pytest

from gcidsum import _enumerate_paths, OpenFileError

_sha1sum_output_re = re.compile(r'^[0-9a-f]{40}  (?P<fn>.+)$')

def _get_sha1sum_found_files(pattern: str):
    proc = subprocess.run(['sha1sum', pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    proc.check_returncode()
    outputs = proc.stdout.decode('utf-8')
    for line in outputs.splitlines():
        match = _sha1sum_output_re.match(line)
        assert match, line
        yield match.group('fn')

def _get_enumerate_paths_found_files(pattern: str):
    for path in _enumerate_paths(pattern):
        yield str(path)

@pytest.mark.parametrize('pattern', [
    os.path.join(os.getcwd(), '*.py'),
    'gcidsum.py',
    '*.py',
    './*.py',
    '.\\*.py',
])
def test_enumerate_paths(pattern: str):
    from_enumerate_paths = list(_get_enumerate_paths_found_files(pattern))
    from_sha1sum = list(_get_sha1sum_found_files(pattern))

    # the separator of from_enumerate_paths is based on OS;
    # the separator of from_sha1sum is based on inputs
    # I want to format them with unix path separator
    from_enumerate_paths = [x.replace('\\', '/') for x in from_enumerate_paths]
    from_sha1sum = [x.replace('\\', '/') for x in from_sha1sum]

    assert from_enumerate_paths == from_sha1sum

@pytest.mark.parametrize('pattern_suffix', [
    'test_gcid_data.py',
    '*.py',
])
def test_enumerate_paths_from_abs(pattern_suffix: str):
    with tempfile.TemporaryDirectory(prefix=__name__ + '-') as tmpdir:
        (pathlib.Path(tmpdir) / 'test_gcid_data.py').write_text('sometext')

        pattern = os.path.join(tmpdir, pattern_suffix)

        from_enumerate_paths = list(_get_enumerate_paths_found_files(pattern))
        from_sha1sum = list(_get_sha1sum_found_files(pattern))
        assert from_enumerate_paths == from_sha1sum

@pytest.mark.parametrize('pattern', [
    '**/*.py',
])
def test_enumerate_paths_with_recursive(pattern: str):
    e1: OpenFileError = None
    e2: subprocess.CalledProcessError = None
    try:
        list(_get_enumerate_paths_found_files(pattern))
        assert False
    except OpenFileError as ee:
        e1 = ee
    try:
        list(_get_sha1sum_found_files(pattern))
        assert False
    except subprocess.CalledProcessError as ee:
        e2 = ee

    assert e1 is not None and e2 is not None

    e2_stderr: bytes = e2.stderr
    assert e1.message == e2_stderr.decode('utf-8').removeprefix('sha1sum:').strip()
