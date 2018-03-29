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

from subprocess import check_output
from test_utils import project


def test_templates():
    output = check_output(['mlt', 'templates', 'list',
                           '--template-repo={}'.format(project.basedir())]
                          ).decode("utf-8")
    desired_template_output = """Template        Description
--------------  --------------------------------------------------------------------------------------------------
hello-world     A TensorFlow python HelloWorld example run through Kubernetes Jobs.
pytorch         Sample distributed application taken from http://pytorch.org/tutorials/intermediate/dist_tuto.html
tf-dist-mnist   A distributed TensorFlow MNIST model which designates worker 0 as the chief.
tf-distributed  A distributed TensorFlow matrix multiplication run through the TensorFlow Kubernetes Operator.
"""
    assert output == desired_template_output
