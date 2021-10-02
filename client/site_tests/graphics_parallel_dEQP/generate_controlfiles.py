#!/usr/bin/env python2
"""
This script generates autotest control files for dEQP. It supports
1) Generate control files for tests with Passing expectations.
2) Generate control files to run tests that are not passing.
3) Decomposing a test into shards. Ideally shard_count is chosen such that
   each shard will run less than 1 minute. It mostly makes sense in
   combination with "hasty".
"""
import os
from collections import namedtuple
# Use 'sudo pip install enum34' to install.
from enum import Enum
# Use 'sudo pip install jinja2' to install.
from jinja2 import Template

Test = namedtuple(
        'Test',
        'filter, suite, shards, time, tag, api, caselist, perf_failure_description'
)

ATTRIBUTES_BVT_PB = ('suite:deqp, suite:graphics_per-day, suite:graphics_system')
ATTRIBUTES_DAILY = 'suite:deqp, suite:graphics_per-day, suite:graphics_system'


class Suite(Enum):
    none = 1
    daily = 2
    bvtcq = 3
    bvtpb = 4


deqp_dir = '/usr/local/deqp'
caselists = 'caselists'
GLES2_FILE = os.path.join(deqp_dir, caselists, 'gles2.txt')
GLES3_FILE = os.path.join(deqp_dir, caselists, 'gles3.txt')
GLES31_FILE = os.path.join(deqp_dir, caselists, 'gles31.txt')
VK_FILE = os.path.join(deqp_dir, caselists, 'vk.txt')

tests = [
        Test('dEQP-GLES2',
             Suite.bvtpb,
             shards=1,
             time='MEDIUM',
             tag='gles2',
             api='gles2',
             caselist=GLES2_FILE,
             perf_failure_description='Failures_GLES2'),
        Test('dEQP-GLES3',
             Suite.bvtpb,
             shards=1,
             time='LONG',
             tag='gles3',
             api='gles3',
             caselist=GLES3_FILE,
             perf_failure_description='Failures_GLES3'),
        Test('dEQP-GLES31',
             Suite.bvtpb,
             shards=1,
             time='LONG',
             tag='gles31',
             api='gles31',
             caselist=GLES31_FILE,
             perf_failure_description='Failures_GLES31'),
        Test('dEQP-VK',
             Suite.bvtpb,
             shards=4,
             time='LONG',
             tag='vk',
             api='vk',
             caselist=VK_FILE,
             perf_failure_description='Failures_VK'),
]

CONTROLFILE_TEMPLATE = Template("""\
# Copyright 2015-2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Please do not edit this file! It has been created by generate_controlfiles.py.

PY_VERSION = 3
NAME = '{{testname}}'
AUTHOR = 'chromeos-gfx'
PURPOSE = 'Run the drawElements Quality Program test suite with deqp-runner.'
CRITERIA = 'All of the individual tests must pass unless marked as known failures.'
ATTRIBUTES = '{{attributes}}'
TIME = '{{time}}'
TEST_CATEGORY = 'Functional'
TEST_CLASS = 'graphics'
TEST_TYPE = 'client'
MAX_RESULT_SIZE_KB = 131072
EXTENDED_TIMEOUT = 86400
DOC = \"\"\"
This test runs the drawElements Quality Program test suite.
\"\"\"
job.run_test('graphics_parallel_dEQP',{% if tag != None %}
             tag = '{{tag}}',{% endif %}
             opts = args + [
                 'api={{api}}',
                 'caselist={{caselist}}',
                 {% if perf_failure_description %}'perf_failure_description={{perf_failure_description}}',{% endif %}
                 'shard_number={{shard}}',
                 'shard_count={{shards}}'
             ])""")


def get_controlfilename(test, shard=0):
    return 'control.%s' % get_name(test, shard)


def get_attributes(test):
    if test.suite == Suite.bvtpb:
        return ATTRIBUTES_BVT_PB
    if test.suite == Suite.daily:
        return ATTRIBUTES_DAILY
    return ''


def get_time(test):
    return test.time


def get_name(test, shard):
    name = test.filter.replace('dEQP-', '', 1).lower()
    if test.shards > 1:
        name = '%s.%d' % (name, shard)
    return name


def get_testname(test, shard=0):
    return 'graphics_parallel_dEQP.%s' % get_name(test, shard)


def write_controlfile(filename, content):
    print(('Writing %s.' % filename))
    with open(filename, 'w+') as f:
        f.write(content)


def write_controlfiles(test):
    attributes = get_attributes(test)
    time = get_time(test)

    for shard in range(0, test.shards):
        testname = get_testname(test, shard)
        filename = get_controlfilename(test, shard)
        content = CONTROLFILE_TEMPLATE.render(
                testname=testname,
                attributes=attributes,
                time=time,
                subset='Pass',
                shard=shard,
                shards=test.shards,
                api=test.api,
                caselist=test.caselist,
                tag=test.tag,
                perf_failure_description=test.perf_failure_description)
        write_controlfile(filename, content)


def main():
    for test in tests:
        write_controlfiles(test)


if __name__ == "__main__":
    main()
