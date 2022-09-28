# -*- coding: utf-8 -*-
#
# Copyright (c) 2022~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import os

from gcidsum import _enumerate_paths

def test_enumerate_paths():
    def ep(p: str):
        return [p.name for p in _enumerate_paths(p)]

    all_py_files = ['gcidsum.py']

    assert all_py_files == ep('*.py')
    assert all_py_files == ep('./*.py')
    assert all_py_files == ep('.\\*.py')

    assert all_py_files == ep(os.path.join(os.getcwd(), '*.py'))
