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

import pytest
from mock import patch
from subprocess import CalledProcessError

from mlt.utils.process_helpers import run, run_popen
from test_utils.io import catch_stdout


@patch('mlt.utils.process_helpers.check_output')
def test_run_no_cwd(check_output):
    """Assert a command was called with no current working dir
       This command should return the value of `bar`
    """
    check_output.return_value.decode.return_value = 'bar'
    output = run('ls')
    assert output == 'bar'


@patch('mlt.utils.process_helpers.check_output')
def test_run_cwd(check_output):
    """Assert a command was called with /tmp as working dir
       This command should return the value of `foo`
    """
    check_output.return_value.decode.return_value = 'foo'
    output = run('ls', '/tmp')
    assert output == 'foo'


@patch('mlt.utils.process_helpers.check_output')
def test_run_error(check_output):
    """There was a bad command made, therefore no output"""
    check_output.side_effect = CalledProcessError(
        returncode=2, cmd='Bad Command!')
    with catch_stdout() as caught_output:
        with pytest.raises(SystemExit):
            run('ls')
        output = caught_output.getvalue().strip()
    # since we're mocking CalledProcessError call, not sure we can simulate
    # exception raised by actual check_output call, so e.output is None
    assert output == 'None'


@patch('mlt.utils.process_helpers.Popen')
def test_run_popen(popen):
    """Popen call should succeed"""
    popen.return_value = 0
    result = run_popen(['ls', '/tmp'])
    assert result == 0


@patch('mlt.utils.process_helpers.Popen')
def test_run_popen_shell(popen):
    """Popen call should succeed"""
    popen.return_value = 0
    result = run_popen('ls /tmp', shell=True)
    assert result == 0
