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

from mock import patch

from mlt.commands.undeploy import UndeployCommand


@patch('mlt.commands.undeploy.config_helpers.load_config')
@patch('mlt.commands.undeploy.process_helpers')
def test_undeploy(proc_helpers, load_config):
    undeploy = UndeployCommand({'undeploy': True})
    undeploy.config = {'namespace': 'foo'}
    undeploy.action()
    proc_helpers.run.assert_called_once()
