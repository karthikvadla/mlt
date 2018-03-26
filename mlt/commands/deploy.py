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
from conditional import conditional
from contextlib import contextmanager
import json
import os
import sys
import time
import uuid
import yaml
from string import Template
from subprocess import Popen, PIPE
from termcolor import colored

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
            push_error = self.push_process.communicate()
            print(colored(push_error[0], 'red'))
            print(colored(push_error[1], 'red'))
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
        """Substitutes image, app, run data into k8s-template selected.
           Can also launch user into interactive shell with --interactive flag
        """
        app_name = self.config['name']
        self.namespace = self.config['namespace']
        remote_container_name = files.fetch_action_arg(
            'push', 'last_remote_container')

        print("Deploying {}".format(remote_container_name))
        kubernetes_helpers.ensure_namespace_exists(self.namespace)

        for path, dirs, filenames in os.walk("k8s-templates"):
            self.file_count = len(filenames)
            for filename in filenames:
                with open(os.path.join(path, filename)) as f:
                    template = Template(f.read())
                out = template.substitute(
                    image=remote_container_name,
                    app=app_name, run=str(uuid.uuid4()))

                # sometimes we want to deploy interactively, but we always
                # want to do the below stuff for a regular deploy regardless
                with conditional(self.args["--interactive"],
                                 self._deploy_interactively(out, filename)) \
                        as out_modified:
                    # conditional will make out_modified None if
                    # not running interactive mode
                    out = out_modified or out
                    with open(os.path.join('k8s', filename), 'w') as f:
                        f.write(out)
                    process_helpers.run(
                        ["kubectl", "--namespace", self.namespace,
                         "apply", "-R", "-f", "k8s"])

            print("\nInspect created objects by running:\n"
                  "$ kubectl get --namespace={} all\n".format(self.namespace))

        # we can't yield many times inside of contextmanagers so for now this
        # lives here. After everything is deployed we'll make a kubectl exec
        # call into our debug container
        if self.args["--interactive"]:
            self._exec_into_pod(self.interactive_deploy_podname)

    @contextmanager
    def _deploy_interactively(self, data, filename):
        """Makes template command become `sleep infinity`
           and keep track of the pod we want to exec into when all things
           have deployed.
           Right now we support just one interactive deploy
           default to only file in template dir if possible
           keep track of which pod we want to connect to
        """
        interactive_deploy = False
        if self.file_count == 1 or \
                self.args["<kube_spec>"] == filename:
            data = self._patch_template_spec(data)
            interactive_deploy = True

        # do regular deploy things here
        yield data

        # don't know of a better way to do this; grab the pod created
        # by the job we just deployed
        # this gets the most recent pod by name, so we can exec into it
        # once everything is done deploying
        if interactive_deploy:
            pod = process_helpers.run_popen(
                "kubectl get pods --namespace {} ".format(self.namespace) +
                "--sort-by=.status.startTime", shell=True
            ).stdout.read().decode('utf-8').strip().splitlines()
            if pod:
                # we want last pod listed, podname is always listed first
                self.interactive_deploy_podname = pod[-1].split()[0]
            else:
                raise ValueError("No pods found in namespace: {}".format(
                    self.namespace))

    def _patch_template_spec(self, data):
        """Makes `command` of template yaml `sleep infinity`.
           We will also add a `debug=true` label onto this pod for easy
           discovery later.
           # NOTE: for now we only support basic functionality. Only 1
           container in a deployment for now.
        """
        data = yaml.load(data)
        """
        TODO: this should be smarter
        3 options:
        1. search yaml for `containers` anywhere
        2. Have function to update `containers` location depending on spec
        3. Have templates for each kind of spec
        I like option 1. More flexible!
        """
        data['spec']['template']['metadata'] = {'labels': {'debug': 'true'}}
        data['spec']['template']['spec']['containers'][0].update(
            {'command':
             ["/bin/bash", "-c",
              "trap : TERM INT; sleep infinity & wait"]})
        return json.dumps(data)

    def _exec_into_pod(self, podname):
        """wait til pod comes up and then exec into it"""
        print("Connecting to pod...")
        # we will try 5 times, 1 sec between tries
        tries = 0
        while True:
            pod = process_helpers.run_popen(
                "kubectl get pods --namespace {} {} -o json".format(
                    self.namespace, podname),
                shell=True).stdout.read().decode('utf-8')
            if not pod:
                continue

            # check if pod is in running state
            # gcr stores an auth token which could be returned as part
            # of the pod json data
            pod = json.loads(pod)
            if pod.get('items') or pod.get('status'):
                if pod.get('items'):
                    pod = pod['items'][0]
                if pod['status']['phase'] == 'Running':
                    break

            if tries == 5:
                raise ValueError("Pod {} not Running".format(podname))
            tries += 1
            time.sleep(1)

        process_helpers.run_popen(
            ["kubectl", "exec", "-it", podname,
             "/bin/bash"], stdout=None, stderr=None).wait()
