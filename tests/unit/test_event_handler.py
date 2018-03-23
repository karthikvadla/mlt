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

from mock import MagicMock, patch

from mlt.event_handler import EventHandler
from test_utils.io import catch_stdout


@patch('mlt.event_handler.call')
def test_dispatch_git(call):
    """if event relates to git we return immediately"""
    event_handler = EventHandler(lambda: 'foo')
    event_handler.dispatch(MagicMock(src_path='./.git'))
    call.assert_not_called()


@patch('mlt.event_handler.call')
def test_dispatch_directory(call):
    """if event is the main dir we do nothing"""
    event_handler = EventHandler(lambda: 'foo')
    event_handler.dispatch(MagicMock(src_path='./'))
    call.assert_not_called()


@patch('mlt.event_handler.open')
@patch('mlt.event_handler.call')
def test_dispatch_is_ignored(call, open_mock):
    """if git check-ignore passes, we do nothing"""
    call.return_value = 0
    event_handler = EventHandler(lambda: 'foo')
    event_handler.dispatch(MagicMock())
    assert event_handler.timer is None


@patch('mlt.event_handler.open')
@patch('mlt.event_handler.call')
def test_dispatch(call, open_mock):
    """normal file event handling"""
    event_handler = EventHandler(lambda: 'foo')
    event_handler.timer = None
    with catch_stdout() as caught_output:
        event_handler.dispatch(MagicMock(src_path='/foo'))
        output = caught_output.getvalue()
    assert output == 'event.src_path /foo\n'
