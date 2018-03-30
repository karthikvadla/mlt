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
      [--registry=<registry> --namespace=<namespace]
      [--skip-crd-check] <name>
  mlt build [--watch]
  mlt deploy [--no-push]
  mlt undeploy
  mlt (template | templates) list [--template-repo=<repo>]

Options:
  --template=<template>   Template name for app
                          initialization [default: hello-world].
  --template-repo=<repo>  Git URL of template repository.
                          [default: git@github.com:IntelAI/mlt.git]
  --registry=<registry>   Container registry to use.
                          If none is set, will attempt to use gcloud.
  --namespace=<namespace> Kubernetes Namespace to use.
                          If none is set, will attempt to create or
                          use a namespace identical to username.
  --skip-crd-check        To avoid crd check during mlt init [default: False].
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
