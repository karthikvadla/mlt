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

from mock import patch, MagicMock

from mlt.utils.progress_bar import duration_progress


@patch('mlt.utils.progress_bar.progressbar')
def test_duration_progress_not_done(progressbar):
    """We have a duration of 1 and then we aren't done once
       and then we finish, which means bar.next() is called twice inside
       of the for loop and and update happens once as we're done early
    """
    duration_progress('activity', 1, MagicMock(
        side_effect=[False, True, True]))

    progressbar_obj = progressbar.ProgressBar.return_value.return_value
    assert progressbar_obj.next.call_count == 2
    assert progressbar_obj.update.call_count == 1


@patch('mlt.utils.progress_bar.progressbar')
def test_duration_progress_duration_done(progressbar):
    """We have a duration of 1 but then terminate immediately
       So we have a bar.next() call, then we update as we're done early
       and then `if not is_done()` is not called so func terminates
    """
    duration_progress('activity', 1, lambda: True)

    progressbar_obj = progressbar.ProgressBar.return_value.return_value
    assert progressbar_obj.next.call_count == 1
    assert progressbar_obj.update.call_count == 1


@patch('mlt.utils.progress_bar.progressbar')
def test_duration_progress_no_duration_not_done(progressbar):
    """We have no duration, then we aren't done yet, then we enter the while
       loop for one iteration to update the bar and then terminate
    """
    duration_progress('activity', None, MagicMock(
        side_effect=[False, False, False, True]))

    progressbar_obj = progressbar.ProgressBar.return_value.return_value
    progressbar_obj.next.assert_not_called()
    progressbar_obj.update.call_count == 3


@patch('mlt.utils.progress_bar.progressbar')
def test_duration_progress_no_duration_done(progressbar):
    """Duration is None and we are done so nothing is called in the func"""
    duration_progress('activity', None, lambda: True)

    progressbar_obj = progressbar.ProgressBar.return_value.return_value
    progressbar_obj.next.assert_not_called()
    progressbar_obj.update.assert_not_called()
