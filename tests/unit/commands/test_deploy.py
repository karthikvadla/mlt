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


@pytest.fixture
def sleep(patch):
    return patch('time.sleep')


@pytest.fixture
def fetch_action_arg(patch):
    return patch('files.fetch_action_arg', MagicMock(return_value='output'))


@pytest.fixture
def kube_helpers(patch):
    return patch('kubernetes_helpers')


@pytest.fixture
def json(patch):
    return patch('json')


@pytest.fixture
def open_mock(patch):
    return patch('open')


@pytest.fixture
def popen_mock(patch):
    popen_mock = MagicMock()
    popen_mock.return_value.poll.return_value = 0
    return patch('Popen', popen_mock)


@pytest.fixture
def process_helpers(patch):
    return patch('process_helpers')


@pytest.fixture
def progress_bar(patch):
    progress_mock = MagicMock()
    progress_mock.duration_progress.side_effect = lambda x, y, z: print(
        'Pushing ')
    return patch('progress_bar', progress_mock)


@pytest.fixture
def template(patch):
    return patch('Template')


@pytest.fixture
def verify_build(patch):
    return patch('build_helpers.verify_build')


@pytest.fixture
def verify_init(patch):
    return patch('config_helpers.load_config')


@pytest.fixture
def walk_mock(patch):
    return patch('os.walk', MagicMock(return_value=['foo', 'bar']))


@pytest.fixture
def yaml(patch):
    return patch('yaml.load')


def deploy(no_push, interactive, extra_config_args):
    deploy = DeployCommand(
        {'deploy': True, '--no-push': no_push, '--interactive': interactive})
    deploy.config = {'name': 'app', 'namespace': 'namespace'}
    deploy.config.update(extra_config_args)

    with catch_stdout() as caught_output:
        deploy.action()
        output = caught_output.getvalue()
    return output


def verify_successful_deploy(output, did_push=True, interactive=False):
    """assert pushing, deploying, then objs created, then pushed"""
    pushing = output.find('Pushing ')
    push_skip = output.find('Skipping image push')
    deploying = output.find('Deploying ')
    inspecting = output.find('Inspect created objects by running:\n')
    pushed = output.find('Pushed to ')
    pod_connect = output.find('Connecting to pod...')

    if did_push:
        assert all(var >= 0 for var in (
            deploying, inspecting, pushing, pushed))
        assert deploying < inspecting, pushing < pushed
    else:
        assert all(var == -1 for var in (pushing, pushed))
        assert all(var >= 0 for var in (deploying, inspecting, push_skip))
        assert push_skip < deploying, deploying < inspecting

    if interactive:
        assert pod_connect > inspecting


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


def test_deploy_interactive_one_file(walk_mock, progress_bar, popen_mock,
                                     open_mock, template, kube_helpers,
                                     process_helpers, verify_build,
                                     verify_init, fetch_action_arg, sleep,
                                     yaml, json):
    walk_mock.return_value = ['foo']
    json.loads.return_value = {'status': {'phase': 'Running'}}
    output = deploy(
        no_push=False, interactive=True,
        extra_config_args={'registry': 'dockerhub'})
    verify_successful_deploy(output, interactive=True)


def test_deploy_interactive_two_files(walk_mock, progress_bar, popen_mock,
                                      open_mock, template, kube_helpers,
                                      process_helpers, verify_build,
                                      verify_init, fetch_action_arg, sleep,
                                      yaml, json):
    json.loads.return_value = {'status': {'phase': 'Running'}}
    output = deploy(
        no_push=False, interactive=True,
        extra_config_args={'registry': 'dockerhub', '<kube_spec>': 'r'})
    verify_successful_deploy(output, interactive=True)


def test_deploy_interactive_pod_not_run(walk_mock, progress_bar, popen_mock,
                                        open_mock, template, kube_helpers,
                                        process_helpers, verify_build,
                                        verify_init, fetch_action_arg, sleep,
                                        yaml, json):
    json.loads.return_value = {'status': {'phase': 'Error'}}
    with pytest.raises(ValueError):
        output = deploy(
            no_push=False, interactive=True,
            extra_config_args={'registry': 'dockerhub', '<kube_spec>': 'r'})
