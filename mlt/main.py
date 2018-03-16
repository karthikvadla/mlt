#!/usr/bin/env python
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

# TODO: dynamically specify which debug tools user wants installed
# when they do a `mlt deploy --debug`

"""mlt.
Usage:
  mlt (-h | --help)
  mlt --version
  mlt init [--template=<template> --template-repo=<repo>]
      [--registry=<registry> --namespace=<namespace] <name>
  mlt build [--watch]
  mlt deploy [--no-push --debug --interactive]
  mlt undeploy
  mlt (template | templates) list [--template-repo=<repo>]

Options:
  --template=<template>   Template name for app
                          initialization [default: hello-world].
  --template-repo=<repo>  Git URL of template repository.
                          [default: git@github.com:NervanaSystems/mlt.git]
  --registry=<registry>   Container registry to use.
                          If none is set, will attempt to use gcloud.
  --namespace=<namespace> Kubernetes Namespace to use.
                          If none is set, will attempt to create or
                          use a namespace identical to username.
  --watch                 Watch project directory and build on file changes.
  --no-push               Deploy your project to kubernetes using the same
                          image from your last run.
  --debug                 Monkeypatches your deployed job into debug mode.
                          Deployment command becomes effectively
                          `sleep infinity & wait`. Your public key and
                          known_hosts are copied into the container. SSH is
                          installed, `whoami` user is created (helps with
                          syncing code), rsync and vim are installed, and your
                          deployment environment is copied into the root user's
                          environment so sshing in becomes the same env as a
                          `kubectl exec`.
  --interactive           Launches you into an ssh connection with your job.
                          Requires `--debug` to have happened, so will trigger
                          a `--debug` call if none has happened yet.
"""
from docopt import docopt

from mlt.commands import (BuildCommand, DeployCommand, InitCommand,
                          TemplatesCommand, UndeployCommand)

# every available command and its corresponding action will go here
COMMAND_MAP = (
    ('build', BuildCommand),
    ('deploy', DeployCommand),
    ('init', InitCommand),
    ('template', TemplatesCommand),
    ('templates', TemplatesCommand),
    ('undeploy', UndeployCommand),
)


def run_command(args):
    """maps params from docopt into mlt commands"""
    for command, CommandClass in COMMAND_MAP:
        if args[command]:
            CommandClass(args).action()
            return


def main():
    args = docopt(__doc__, version="ML Container Templates v0.0.1")
    # docker requires repo name to be in lowercase
    if args["<name>"]:
        args["<name>"] = args["<name>"].lower()
    run_command(args)
