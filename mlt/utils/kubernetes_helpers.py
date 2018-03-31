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
import sys

from subprocess import call

from mlt.utils import process_helpers
from kubernetes import client, config


def ensure_namespace_exists(ns):
    exit_code = call(["kubectl", "get", "namespace", ns], stdout=open(
        os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
    if exit_code is not 0:
        process_helpers.run(["kubectl", "create", "namespace", ns])


def check_crds(skip_crd_check, commad_type, app_name=None):
    if not skip_crd_check:
        if app_name is None:
            crd_file = 'crd-requirements.txt'
        else:
            crd_file = os.path.join(app_name, 'crd-requirements.txt')
        if os.path.exists(crd_file):
            with open(crd_file) as f:
                crd_list = f.readlines()

            missing, missing_crds = _checking_crds_on_k8(crd_list)

            if missing:
                print(
                    "Warning: Template will "
                    "not work on your current cluster \n"
                    "Please contact your administrator "
                    "to install the following operator(s): \n")
                for crd in missing_crds:
                    print(crd)

                if commad_type is 'deploy':
                    sys.exit(1)
        else:
            print('file does not exits: {}'.format(crd_file))


def _checking_crds_on_k8(crd_list):
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
