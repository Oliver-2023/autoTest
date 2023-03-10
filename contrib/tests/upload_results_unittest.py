#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os

import common
import unittest

from autotest_lib.contrib.upload_results import *

RESULTS_DIR=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'results-1-stub_PassServer')

class UploadResultsTestCase(unittest.TestCase):

    def test_afe_uniqueness(self):
        rp = ResultsParser
        job1 = rp.parse(RESULTS_DIR, False)
        job2 = rp.parse(RESULTS_DIR, False)

        self.assertNotEqual(job1.afe_job_id, job2.afe_job_id)

    # test mandatory fields are filled on load
    def test_generate_job_serialize(self):
        rp = ResultsParser
        job = rp.parse(RESULTS_DIR, False)

        # test mandatory fields are populated
        self.assertEqual(job.machine_group, 'madoo') # device model
        self.assertEqual(job.board, 'dedede')
        self.assertEqual(job.suite, 'default_suite')
        self.assertEqual(job.label, 'chroot/stub_PassServer')
        self.assertEqual(job.hwid, 'MADOO-RLGE C5B-D4D-G4E-C27-C2N-A2F')
        # dlm_sku_id is populated externally by PVS tool

    # test mandatory fields are filled after save and reload
    def test_persist_and_reload_job(self):
        rp = ResultsParser
        job1 = rp.parse(RESULTS_DIR, False)
        job2 = rp.parse(RESULTS_DIR, True)

        self.assertEqual(job1.machine_group, job2.machine_group)
        self.assertEqual(job1.board, job2.board)
        self.assertEqual(job1.suite, job2.suite)
        self.assertEqual(job1.label, job2.label)

        # even with a reload, we should *still* have a unique job
        self.assertNotEqual(job1.afe_job_id, job2.afe_job_id)

if __name__ == '__main__':
    unittest.main()