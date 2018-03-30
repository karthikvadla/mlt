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

from subprocess import call

from mlt.utils import process_helpers
from kubernetes import client, config


def ensure_namespace_exists(ns):
    exit_code = call(["kubectl", "get", "namespace", ns], stdout=open(
        os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
    if exit_code is not 0:
        process_helpers.run(["kubectl", "create", "namespace", ns])


def check_crds(crd_list):
    """
    Check if given crd list installed on K8 or not.
    """
    config.load_kube_config()
    api_client = client.ApiextensionsV1beta1Api()
    current_crds = [x['spec']['names']['kind'].lower()
                    for x in
                    api_client
                    .list_custom_resource_definition()
                    .to_dict()['items']]
    missing = False
    missing_crds = set(crd_list)-set(current_crds)
    if missing_crds:
        missing = True

    return missing, missing_crds
