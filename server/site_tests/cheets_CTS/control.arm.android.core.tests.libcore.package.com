# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# This file has been automatically generated. Do not edit!

AUTHOR = 'ARC Team'
NAME = 'cheets_CTS.arm.android.core.tests.libcore.package.com'
ATTRIBUTES = 'suite:cts'
DEPENDENCIES = 'arc'
JOB_RETRIES = 2
TEST_TYPE = 'server'
TIME = 'LENGTHY'

DOC = ('Run package android.core.tests.libcore.package.com of the '
       'Android 6.0_r9 Compatibility Test Suite (CTS), build 3102289,'
       'using arm ABI in the ARC container.')

def run_CTS(machine):
    host = hosts.create_host(machine)
    job.run_test(
        'cheets_CTS',
        host=host,
        iterations=1,
        tag='android.core.tests.libcore.package.com',
        target_package='android.core.tests.libcore.package.com',
        bundle='arm',
        timeout=3600)

parallel_simple(run_CTS, machines)