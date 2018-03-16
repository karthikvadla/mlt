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

import os
import json
import time
import uuid
import sys
from string import Template
from subprocess import Popen, PIPE
from termcolor import colored

from mlt import KUBE_DEBUG
from mlt.commands import Command
from mlt.utils import (build_helpers, config_helpers, files,
                       kubernetes_helpers, progress_bar, process_helpers)


class DeployCommand(Command):
    def __init__(self, args):
        super(DeployCommand, self).__init__(args)
        self.config = config_helpers.load_config()
        build_helpers.verify_build(self.args)

    def action(self):
        if self.args['--no-push']:
            print("Skipping image push")
        else:
            self._push()
        self._deploy_new_container()
        if self.args['--debug']:
            process_helpers.run_popen(KUBE_DEBUG, shell=True)
        if self.args['--interactive']:
            # check if --debug has been ran before
            process_helpers.run_popen("ssh -A root@127.0.0.1", shell=True)

    def _push(self):
        last_push_duration = files.fetch_action_arg(
            'push', 'last_push_duration')
        self.container_name = files.fetch_action_arg(
            'build', 'last_container')

        self.started_push_time = time.time()
        # TODO: unify these commands by factoring out docker command
        # based on config
        if 'gceProject' in self.config:
            self._push_gke()
        else:
            self._push_docker()

        progress_bar.duration_progress(
            'Pushing ', last_push_duration,
            lambda: self.push_process.poll() is not None)
        if self.push_process.poll() != 0:
            print(colored(self.push_process.communicate()[0], 'red'))
            sys.exit(1)

        with open('.push.json', 'w') as f:
            f.write(json.dumps({
                "last_remote_container": self.remote_container_name,
                "last_push_duration": time.time() - self.started_push_time
            }))

        print("Pushed to {}".format(self.remote_container_name))

    def _push_gke(self):
        self.remote_container_name = "gcr.io/{}/{}".format(
            self.config['gceProject'], self.container_name)
        self._tag()
        self.push_process = Popen(["gcloud", "docker", "--", "push",
                                   self.remote_container_name],
                                  stdout=PIPE, stderr=PIPE)

    def _push_docker(self):
        self.remote_container_name = "{}/{}".format(
            self.config['registry'], self.container_name)
        self._tag()
        self.push_process = Popen(
            ["docker", "push", self.remote_container_name],
            stdout=PIPE, stderr=PIPE)

    def _tag(self):
        process_helpers.run(
            ["docker", "tag", self.container_name, self.remote_container_name])

    def _deploy_new_container(self):
        app_name = self.config['name']
        namespace = self.config['namespace']
        remote_container_name = files.fetch_action_arg(
            'push', 'last_remote_container')

        print("Deploying {}".format(remote_container_name))

        for filename in os.listdir("k8s-templates"):
            with open(os.path.join('k8s-templates', filename)) as f:
                template = Template(f.read())
                out = template.substitute(image=remote_container_name,
                                          app=app_name, run=str(uuid.uuid4()))

                with open(os.path.join('k8s', filename), 'w') as f:
                    f.write(out)

            kubernetes_helpers.ensure_namespace_exists(namespace)
            process_helpers.run(
                ["kubectl", "--namespace", namespace, "apply", "-R",
                 "-f", "k8s"])

            print("\nInspect created objects by running:\n"
                  "$ kubectl get --namespace={} all\n".format(namespace))
