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
import pytest
from mock import MagicMock

from mlt.commands.deploy import DeployCommand
from test_utils.io import catch_stdout


@pytest.fixture(autouse=True)
def fetch_action_arg(patch):
    return patch('files.fetch_action_arg')


@pytest.fixture(autouse=True)
def kube_helpers(patch):
    return patch('kubernetes_helpers')


@pytest.fixture(autouse=True)
def open_mock(patch):
    return patch('open')


@pytest.fixture(autouse=True)
def popen_mock(patch):
    return patch('Popen')


@pytest.fixture(autouse=True)
def process_helpers(patch):
    return patch('process_helpers')


@pytest.fixture(autouse=True)
def progress_bar(patch):
    return patch('progress_bar')


@pytest.fixture(autouse=True)
def template(patch):
    return patch('Template')


@pytest.fixture(autouse=True)
def verify_build(patch):
    return patch('build_helpers.verify_build')


@pytest.fixture(autouse=True)
def verify_init(patch):
    return patch('config_helpers.load_config')


@pytest.fixture(autouse=True)
def walk_mock(patch):
    return patch('os.walk')


def test_deploy_gce(walk_mock, progress_bar, popen_mock, open_mock,
                    template, kube_helpers, process_helpers, verify_build,
                    verify_init, fetch_action_arg):
    walk_mock.return_value = ['foo', 'bar']
    progress_bar.duration_progress.side_effect = \
        lambda x, y, z: print('Pushing ')
    popen_mock.return_value.poll.return_value = 0

    deploy = DeployCommand(
        {'deploy': True, '--no-push': False, '--interactive': False})
    deploy.config = {
        'gceProject': 'gcr://tacoprojectbestproject',
        'name': 'besttacoapp',
        'namespace': 'besttaconamespace'
    }
    fetch_action_arg.return_value = 'output'

    with catch_stdout() as caught_output:
        deploy.action()
        output = caught_output.getvalue()

    # assert pushing, deploying, then objs created, then pushed
    pushing = output.find('Pushing ')
    deploying = output.find('Deploying ')
    inspecting = output.find('Inspect created objects by running:\n')
    pushed = output.find('Pushed to ')
    assert all(var >= 0 for var in (deploying, inspecting, pushing, pushed))
    assert deploying < inspecting, pushing < pushed


def test_deploy_docker(walk_mock, progress_bar, popen_mock, open_mock,
                       template, kube_helpers, process_helpers, verify_build,
                       verify_init, fetch_action_arg):
    walk_mock.return_value = ['foo', 'bar']
    progress_bar.duration_progress.side_effect = \
        lambda x, y, z: print('Pushing ')
    popen_mock.return_value.poll.return_value = 0

    deploy = DeployCommand(
        {'deploy': True, '--no-push': False, '--interactive': False})
    deploy.config = {
        'registry': 'dockerhub',
        'name': 'besttacoapp',
        'namespace': 'besttaconamespace'
    }
    fetch_action_arg.return_value = 'output'

    with catch_stdout() as caught_output:
        deploy.action()
        output = caught_output.getvalue()

    # assert pushing, deploying, then objs created, then pushed
    pushing = output.find('Pushing ')
    deploying = output.find('Deploying ')
    inspecting = output.find('Inspect created objects by running:\n')
    pushed = output.find('Pushed to ')
    assert all(var >= 0 for var in (deploying, inspecting, pushing, pushed))
    assert deploying < inspecting, pushing < pushed


def test_deploy_without_push(walk_mock, progress_bar, popen_mock, open_mock,
                             template, kube_helpers, process_helpers,
                             verify_build, verify_init, fetch_action_arg):
    walk_mock.return_value = ['foo', 'bar']
    progress_bar.duration_progress.side_effect = \
        lambda x, y, z: print('Pushing ')
    popen_mock.return_value.poll.return_value = 0

    deploy = DeployCommand(
        {'deploy': True, '--no-push': True, '--interactive': False})
    deploy.config = {
        'gceProject': 'gcr://projectfoo',
        'name': 'foo',
        'namespace': 'foo'
    }
    fetch_action_arg.return_value = 'output'

    with catch_stdout() as caught_output:
        deploy.action()
        output = caught_output.getvalue()

    # assert pushing, deploying, then objs created, then pushed
    skipping_push = output.find('Skipping image push')
    deploying = output.find('Deploying ')
    inspecting = output.find('Inspect created objects by running:\n')
    assert all(var >= 0 for var in (deploying, inspecting, skipping_push))
    assert skipping_push < deploying < inspecting

    # we should not see pushing/pushed messages
    pushing = output.find('Pushing ')
    pushed = output.find('Pushed to ')
    assert all(var == -1 for var in (pushing, pushed))
