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
    return patch('files.fetch_action_arg', MagicMock(return_value='output'))


@pytest.fixture(autouse=True)
def kube_helpers(patch):
    return patch('kubernetes_helpers')


@pytest.fixture(autouse=True)
def open_mock(patch):
    return patch('open')


@pytest.fixture(autouse=True)
def popen_mock(patch):
    popen_mock = MagicMock()
    popen_mock.return_value.poll.return_value = 0
    return patch('Popen', popen_mock)


@pytest.fixture(autouse=True)
def process_helpers(patch):
    return patch('process_helpers')


@pytest.fixture(autouse=True)
def progress_bar(patch):
    progress_mock = MagicMock()
    progress_mock.duration_progress.side_effect = lambda x, y, z: print(
        'Pushing ')
    return patch('progress_bar', progress_mock)


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
    return patch('os.walk', MagicMock(return_value=['foo', 'bar']))


def deploy(no_push, interactive, extra_config_args):
    deploy = DeployCommand(
        {'deploy': True, '--no-push': no_push, '--interactive': interactive})
    deploy.config = {'name': 'app', 'namespace': 'namespace'}
    deploy.config.update(extra_config_args)

    with catch_stdout() as caught_output:
        deploy.action()
        output = caught_output.getvalue()
    return output


def verify_successful_deploy(output, did_push=True):
    """assert pushing, deploying, then objs created, then pushed"""
    if did_push:
        pushing = output.find('Pushing ')
        pushed = output.find('Pushed to ')
    else:
        pushing = output.find('Skipping image push')
        # setting pushed to infinity to keep test format
        pushed = float('inf')
    deploying = output.find('Deploying ')
    inspecting = output.find('Inspect created objects by running:\n')

    assert all(var >= 0 for var in (deploying, inspecting, pushing, pushed))
    assert deploying < inspecting, pushing < pushed

    if not did_push:
        # we should not see pushing/pushed messages
        pushing = output.find('Pushing ')
        pushed = output.find('Pushed to ')
        assert all(var == -1 for var in (pushing, pushed))


def test_deploy_gce(walk_mock, progress_bar, popen_mock, open_mock,
                    template, kube_helpers, process_helpers, verify_build,
                    verify_init, fetch_action_arg):
    output = deploy(
        no_push=False, interactive=False,
        extra_config_args={'gceProject': 'gcr://projectfoo'})
    verify_successful_deploy(output)


def test_deploy_docker(walk_mock, progress_bar, popen_mock, open_mock,
                       template, kube_helpers, process_helpers, verify_build,
                       verify_init, fetch_action_arg):
    output = deploy(
        no_push=False, interactive=False,
        extra_config_args={'registry': 'dockerhub'})
    verify_successful_deploy(output)


def test_deploy_without_push(walk_mock, progress_bar, popen_mock, open_mock,
                             template, kube_helpers, process_helpers,
                             verify_build, verify_init, fetch_action_arg):
    output = deploy(
        no_push=True, interactive=False,
        extra_config_args={'gceProject': 'gcr://projectfoo'})
    verify_successful_deploy(output, did_push=False)
