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

from setuptools import setup, find_packages

setup(name='mlt',
      description='Machine Learning Container Tool',
      long_description=open('README.md').read(),
      author='Intel Nervana',
      author_email='intelnervana@intel.com',
      url='http://www.intelnervana.com',
      packages=find_packages(exclude=["tests"]),
      entry_points={
          'console_scripts': ['mlt=mlt.main:main']
      },
      package_data={
          'mlt': ['mlt-templates', 'mlt/scripts/kube_debug.sh']
      },
      include_package_data=True,
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Science/Research',
                   'Operating System :: POSIX',
                   'Operating System :: MacOS :: MacOS X',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering :: ' +
                   'Artificial Intelligence',
                   'Topic :: Scientific/Engineering :: Information Analysis',
                   'Topic :: System :: Distributed Computing'])
