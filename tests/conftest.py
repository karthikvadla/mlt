#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: EPL-2.0
#

from mock import MagicMock
import inspect
import pytest
import os
import sys


# enable test_utils to be used in tests via `from test_utils... import ...
sys.path.append(os.path.join(os.path.dirname(__file__), 'test_utils'))


MODULES = ('mlt.tests',)
MODULES_REPLACE = ('tests.unit', 'mlt')


def patch_setattr(module_names, module_replace, monkeypatch, path, m):
    """ Credit for this goes mostly to @megawidget
    do not call this directly -- assumes the fixture's caller is two stacks up
    and will correspondingly guess the module path to patch
    `path` can be:
        1. an object, if it's defined in the module you're testing
        2. a name, if it's imported in the module you're testing
        3. a full path a la traditional monkeypatch
    """
    if hasattr(path, '__module__'):
        monkeypatch.setattr('.'.join((path.__module__, path.__name__)), m)
        return
    elif any(path.startswith(i+'.') for i in module_names):
        # full path.  OK.
        monkeypatch.setattr(path, m)
        # try:
        #     monkeypatch.setattr(path, m)
        # except AttributeError:
        #     # this will fix builtins like mocking `open`
        #     print(monkeypatch)
        #     print(path, m)
        #     print('*' * 80)
        #     A
    else:
        # assume we're patching stuff in the file the test file is supposed to
        # be testing
        fn = inspect.getouterframes(inspect.currentframe())[2][1]
        fn = os.path.splitext(os.path.relpath(fn))[0]
        module = fn.replace(os.path.sep, '.').replace('test_', '').replace(
            *module_replace)
        pytest.set_trace()
        try:
            monkeypatch.setattr('.'.join((module, path)), m)
        except AttributeError:
            # handle mocking builtins like `open`


@pytest.fixture
def patch(monkeypatch):
    """allows us to add easy autouse fixtures by patching anything we want"""
    def wrapper(path, mock=None):
        m = mock if mock is not None else MagicMock()
        patch_setattr(MODULES, MODULES_REPLACE, monkeypatch, path, m)
        return m

    return wrapper
