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

"""mlt.
Usage:
  mlt (-h | --help)
  mlt --version
  mlt init [--template=<template> --template-repo=<repo>]
      [--registry=<registry> --namespace=<namespace>] <name>
  mlt build [--watch]
  mlt deploy [--no-push] [-i | --interactive]
      [--connection-attempts=<connection-attempts>] [<kube_spec>]
  mlt undeploy
  mlt (template | templates) list [--template-repo=<repo>]

Options:
  --template=<template>                         Template name for app
                                                initialization [default: hello-world].
  --template-repo=<repo>                        Git URL of template repository.
                                                [default: git@github.com:IntelAI/mlt.git]
  --registry=<registry>                         Container registry to use.
                                                If none is set, will attempt to use gcloud.
  --namespace=<namespace>                       Kubernetes Namespace to use.
                                                If none is set, will attempt to create or
                                                use a namespace identical to username.
  --connection-attempts=<connection-attempts>   Number of retries to connect to a pod interactively.
                                                Waits 1 second between retrying.
                                                [default: 5]
  --interactive                                 Rewrites container command to infinite sleep,
                                                and then drops user into `kubectl exec` shell.
                                                Adds a `debug=true` label for easy discovery
                                                later. If you have more than 1 template yaml,
                                                specify which file you'd like to deploy
                                                interactively as the `kube_spec`. `kube_spec` is
                                                only used with this flag.
  --watch                                       Watch project directory and build on file changes
  --no-push                                     Deploy your project to kubernetes using the same
                                                image from your last run.
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
    # -i is an alias, so ensure that we only have to do logic on --interactive
    if args["-i"]:
        args["--interactive"] = True
    # docopt doesn't support type assignment:
    # https://github.com/docopt/docopt/issues/8
    args['--connection-attempts'] = int(args['--connection-attempts'])
    run_command(args)
