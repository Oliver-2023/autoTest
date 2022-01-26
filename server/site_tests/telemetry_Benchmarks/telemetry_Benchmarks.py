# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import sys

# TODO (b/206008069), remove this when migrated to new env
sys.path.insert(0,
                '/usr/local/lib/python2.7/dist-packages/six-1.16.0-py2.7.egg')
try:
    import six
    logging.debug("six version is {}".format(six.__version__))
except ImportError as e:
    logging.warning("Could not import six due to %s", e)

from autotest_lib.server import test
from autotest_lib.server.cros import telemetry_runner
from autotest_lib.server.cros.crosperf import device_setup_utils


class telemetry_Benchmarks(test.test):
    """Run a telemetry benchmark."""
    version = 1


    def run_once(self, host=None, benchmark=None, args={}):
        """Run a telemetry benchmark.

        @param host: hostname(ip address) to run the telemetry benchmark on.
        @param benchmark: telemetry benchmark test to run.
        """
        local = args.get("local") == "True"
        optional = {}
        telemetry_on_dut = args.get("telemetry_on_dut")
        if telemetry_on_dut:
            optional["telemetry_on_dut"] = telemetry_on_dut == "True"

        dut_config_str = args.get("dut_config", "{}")
        dut_config = json.loads(dut_config_str)
        if dut_config:
            device_setup_utils.setup_device(host, dut_config)

        with telemetry_runner.TelemetryRunnerFactory().get_runner(
                host, local, **optional) as telemetry:
            perf_value_writer = self
            extra_args = args.get("extra_args", [])
            repeat = args.get("pageset_repeat")
            if repeat is not None:
                extra_args.append('--pageset-repeat=%s' % repeat)

            telemetry.run_telemetry_benchmark(benchmark, perf_value_writer,
                                              *extra_args)
