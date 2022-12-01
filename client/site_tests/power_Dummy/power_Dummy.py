# Lint as: python2, python3
# Copyright 2018 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time

from autotest_lib.client.cros.power import power_test

class power_Dummy(power_test.power_Test):
    """class for testing power wrapper tests.

    Run for a short time and collect logger data.
    """
    version = 1
    loop = 3
    loop_time = 3.0
    dummy_result = 0

    def initialize(self, pdash_note='', force_discharge=False):
        """Measure power with a short interval."""
        super(power_Dummy, self).initialize(seconds_period=1.,
                                            pdash_note=pdash_note,
                                            force_discharge=force_discharge)

    def warmup(self):
        """Warm up for a short time."""
        super(power_Dummy, self).warmup(warmup_time=1.)

    def run_once(self):
        """Measure power with multiple loggers."""
        start_ts = time.time()
        self.start_measurements()
        for i in range(self.loop):
            tstart = time.time()
            time.sleep(self.loop_time)
            self.checkpoint_measurements('section%s' % i, tstart)

        self._keyvallogger.add_item('system', self.dummy_result, 'point',
                                    'perf')
