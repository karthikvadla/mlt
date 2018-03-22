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
"""
This file will contain a command class for easy testing of different
e2e scenarios by other test files. Goal is to make it easy to add further
e2e scenarios in the future with the least amount of code duplication.
"""
import getpass
import json
import os
import shutil
from subprocess import Popen
import uuid

from mlt.utils.process_helpers import run, run_popen

from project import basedir


class CommandTester(object):
    def __init__(self, workdir):
        # just in case tests fail, want a clean namespace always
        self.workdir = workdir
        self.app_name = str(uuid.uuid4())[:10]
        self.namespace = getpass.getuser() + '-' + self.app_name

        self.project_dir = os.path.join(self.workdir, self.app_name)
        self.mlt_json = os.path.join(self.project_dir, 'mlt.json')
        self.build_json = os.path.join(self.project_dir, '.build.json')
        self.deploy_json = os.path.join(self.project_dir, '.push.json')

    def init(self):
        p = Popen(
            ['mlt', 'init', '--registry=localhost:5000',
             '--template-repo={}'.format(basedir()),
             '--namespace={}'.format(self.namespace), self.app_name],
            cwd=self.workdir)
        assert p.wait() == 0
        assert os.path.isfile(self.mlt_json)
        with open(self.mlt_json) as f:
            assert json.loads(f.read()) == {
                'namespace': self.namespace,
                'name': self.app_name,
                'registry': 'localhost:5000'
            }
        # verify we created a git repo with our project init
        assert "On branch master" in run(
            "git --git-dir={}/.git --work-tree={} status".format(
                self.project_dir, self.project_dir).split())

    def build(self):
        p = Popen(['mlt', 'build'], cwd=self.project_dir)
        assert p.wait() == 0
        assert os.path.isfile(self.build_json)
        with open(self.build_json) as f:
            build_data = json.loads(f.read())
            assert 'last_container' in build_data and \
                'last_build_duration' in build_data
            # verify that we created a docker image
            assert run_popen(
                "docker image inspect {}".format(build_data['last_container']),
                shell=True
            ).wait() == 0

    def deploy(self):
        p = Popen(['mlt', 'deploy'], cwd=self.project_dir)
        out, err = p.communicate()
        assert p.wait() == 0
        assert os.path.isfile(self.deploy_json)
        with open(self.deploy_json) as f:
            deploy_data = json.loads(f.read())
            assert 'last_push_duration' in deploy_data and \
                'last_remote_container' in deploy_data
        # verify that the docker image has been pushed to our local registry
        # need to decode because in python3 this output is in bytes
        assert 'true' in run_popen(
            "curl --noproxy \"*\"  registry:5000/v2/_catalog | "
            "jq .repositories | jq 'contains([\"{}\"])'".format(self.app_name),
            shell=True
        ).stdout.read().decode("utf-8")
        # verify that our job did indeed get deployed to k8s
        assert run_popen(
            "kubectl get jobs --namespace={}".format(self.namespace),
            shell=True).wait() == 0

    def undeploy(self):
        p = Popen(['mlt', 'undeploy'], cwd=self.project_dir)
        assert p.wait() == 0
        # verify no more deployment job
        assert run_popen(
            "kubectl get jobs --namespace={}".format(
                self.namespace), shell=True).wait() == 0
