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

import shutil
import tempfile
from contextlib import contextmanager

from mlt.utils import process_helpers


@contextmanager
def clone_repo(repo):
    destination = tempfile.mkdtemp()
    process_helpers.run_popen(
        "git clone {} {}".format(repo, destination),
        shell=True, stdout=False, stderr=False).wait()
    try:
        yield destination
    finally:
        shutil.rmtree(destination)
