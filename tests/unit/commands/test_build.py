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

from __future__ import print_function

from mock import patch, MagicMock
from test_utils.io import catch_stdout

from mlt.commands.build import BuildCommand


@patch('mlt.commands.build.config_helpers.load_config')
@patch('mlt.commands.build.open')
@patch('mlt.commands.build.process_helpers.run_popen')
@patch('mlt.commands.build.progress_bar')
def test_simple_build(progress_bar, popen, open_mock,
                      verify_init):
    progress_bar.duration_progress.side_effect = \
        lambda x, y, z: print('Building')
    popen.return_value.poll.return_value = 0

    build = BuildCommand({'build': True, '--watch': False})
    build.config = MagicMock()

    with catch_stdout() as caught_output:
        build.action()
        output = caught_output.getvalue()

    # assert that we started build, then did build process, then built
    starting = output.find('Starting build')
    building = output.find('Building')
    built = output.find('Built')
    assert all(var >= 0 for var in (starting, building, built))
    assert starting < building < built


@patch('mlt.commands.build.config_helpers.load_config')
@patch('mlt.commands.build.time.sleep')
@patch('mlt.commands.build.Observer')
@patch('mlt.commands.build.open')
def test_watch_build(open_mock, observer, sleep_mock, verify_init):
    sleep_mock.side_effect = KeyboardInterrupt

    build = BuildCommand({'build': True, '--watch': True})
    build.config = MagicMock()

    with patch('mlt.commands.build.EventHandler') as event_handler_patch:
        build.action()
