# Copyright 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import re
import shutil
from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import cros_logging, service_stopper
from autotest_lib.client.cros.graphics import graphics_utils


class graphics_parallel_dEQP(graphics_utils.GraphicsTest):
    """Run the drawElements Quality Program test suite."""
    version = 1
    _services = None
    _shard_number = 0
    _shard_count = 1
    _board = None
    _cpu_type = None
    _gpu_type = None
    _surface = None
    _filter = None
    _width = 256  # Use smallest width for which all tests run/pass.
    _height = 256  # Use smallest height for which all tests7 run/pass.
    _caselist = None
    _log_path = None  # Location for detailed test output logs
    _debug = False  # Analyze kernel messages.
    _log_reader = None  # Reader to analyze (kernel) messages log.
    _log_filter = re.compile('.* .* kernel:')  # kernel messages filter.
    _env = None  # environment for test processes
    _skips = []
    _fails = []
    _flakes = []
    # We do not consider these results as failures.
    TEST_RESULT_FILTER = [
            'pass', 'notsupported', 'internalerror', 'qualitywarning',
            'compatibilitywarning', 'skipped'
    ]

    def initialize(self):
        super(graphics_parallel_dEQP, self).initialize()
        self._api_helper = graphics_utils.GraphicsApiHelper()
        self._board = utils.get_board()
        self._cpu_type = utils.get_cpu_soc_family()
        self._gpu_type = utils.get_gpu_family()

        # deqp may depend on libraries that are present only on test images.
        # Those libraries are installed in /usr/local.
        self._env = os.environ.copy()
        old_ld_path = self._env.get('LD_LIBRARY_PATH', '')
        if old_ld_path:
            self._env[
                    'LD_LIBRARY_PATH'] = '/usr/local/lib:/usr/local/lib64:' + old_ld_path
        else:
            self._env['LD_LIBRARY_PATH'] = '/usr/local/lib:/usr/local/lib64'

        self._services = service_stopper.ServiceStopper(['ui', 'powerd'])
        # Valid choices are fbo and pbuffer. The latter avoids dEQP assumptions.
        self._surface = 'pbuffer'
        self._services.stop_services()

    def cleanup(self):
        if self._services:
            self._services.restore_services()
        super(graphics_parallel_dEQP, self).cleanup()

    def _get_executable(self, api):
        """Return the executable path of the api."""
        return self._api_helper.get_deqp_executable(api)

    def _can_run(self, api):
        """Check if specific api is supported in this board."""
        return api in self._api_helper.get_supported_apis()

    def read_file(self, filename):
        expects_path = os.path.join(self.autodir, 'tests',
                                    'graphics_parallel_dEQP', 'boards',
                                    filename)
        try:
            with open(expects_path) as f:
                logging.debug(
                        "Reading board test list from {}".format(expects_path))
                return f.readlines()
        except IOError as e:
            logging.debug("No file found at {}".format(expects_path))
            return []

    def setup_case_list_filters(self):
        """Set up the skip/flake/fails filter lists.

        The expected fails list will be entries like
        'dEQP-SUITE.test.name,Crash', such as you find in a failures.csv,
        results.csv, or the "Some failures found:" stdout output of a previous
        run.  Enter a test here when it has an expected state other than Pass or
        Skip.

        The skips list is a list of regexs to match test names to not run at
        all. This is good for tests that are too slow or uninteresting to ever
        see status for.

        The flakes list is a list of regexes to match test names that may have
        unreliable status.  Any unexpected result of that test will be marked
        with the Flake status and not cause the test run to fail.  The runner
        does automatic flake detection on its own to try to mitigate
        intermittent failures, but even with that we can see too many spurious
        failures in CI when run across many boards and many builds, so this lets
        you run those tests while avoiding having them fail out CI runs until
        the source of the flakiness can be resolved.

        The primary source of board skip/flake/fails will be files in this test
        directory under boards/, but we also list some common entries directly
        in the code here to save repetition of the explanations.  The files may
        contain empty lines or comments starting with '#'.

        We could avoid adding filters for other apis than the one being tested,
        but it's harmless to have unused tests in the lists and makes
        copy-and-paste mistakes less likely.

        We don't care to run the performance or stress tests from dEQP-GLES on
        any boards -- they're very slow but don't generally fail."""

        self._skips.append('dEQP-GLES.*.performance.*')
        self._skips.append('dEQP-GLES.*.stress.*')

        # This set of tests may emit warnings, but is not required for
        # conformance and I've never seen anyone pay attention to it.
        self._skips.append('dEQP-GLES.*.accuracy.*')

        # The flush_finish tests throw warnings when behavior doesn't match
        # their expectations, except that tiling GPUs don't behave the way they
        # expect in their timing setup so the tests take exceptionally long
        # while just wasting developer time.  Not required to be warnings-free
        # for conformance.
        if self._gpu_type in ['qualcomm', 'rogue'
                              ] or self._gpu_type.startswith('Mali'):
            self._skips.append('dEQP-GLES.*.functional.flush_finish.*')

        # This test flakes across all Mesa drivers (Intel KBL+GLK, AMD, and Qualcomm, at least).
        # https://gitlab.freedesktop.org/mesa/mesa/-/issues/4575
        self._flakes.append(
                'dEQP-VK.wsi.display.get_display_plane_capabilities')

        # Add any board-specific expectations
        self._skips += self.read_file(self._board + '-' + 'skips.txt')
        self._skips += self.read_file(self._gpu_type + '-' + 'skips.txt')
        self._fails += self.read_file(self._board + '-' + 'fails.txt')
        self._fails += self.read_file(self._gpu_type + '-' + 'fails.txt')
        self._flakes += self.read_file(self._board + '-' + 'flakes.txt')
        self._flakes += self.read_file(self._gpu_type + '-' + 'flakes.txt')
        # TODO: Add more fails lists for various boards
        # TODO: Fix the Missing results from the runner on trogdor
        # TODO: Add the other VK shards on trogdor

    def add_filter_arg(self, command, list, arg, filename):
        if not list:
            return

        path = os.path.join(self._log_path, filename)
        with open(path, "w") as f:
            for test in list:
                f.write(test + '\n')
        command.append(arg + '=' + path)

    def run_once(self, opts=None):
        options = dict(
                api=None,
                caselist=None,
                filter='',
                subset_to_run='Pass',  # Pass, Fail, Timeout, NotPass...
                shard_number='0',
                shard_count='1',
                debug='False',
                perf_failure_description=None)
        if opts is None:
            opts = []
        options.update(utils.args_to_dict(opts))
        logging.info('Test Options: %s', options)

        self._caselist = options['caselist']
        self._shard_number = int(options['shard_number'])
        self._shard_count = int(options['shard_count'])
        self._debug = (options['debug'] == 'True')

        api = options['api']

        if not self._can_run(api):
            logging.info('Skipping on %s due to lack of %s API support',
                         self._gpu_type, api)
            return

        if options['perf_failure_description']:
            self._test_failure_description = options[
                    'perf_failure_description']
        else:
            # Do not report failure if failure description is not specified.
            self._test_failure_report_enable = False

        # Some information to help post-process logs.
        logging.info('ChromeOS BOARD = %s', self._board)
        logging.info('ChromeOS CPU family = %s', self._cpu_type)
        logging.info('ChromeOS GPU family = %s', self._gpu_type)

        self.setup_case_list_filters()

        # Create a place to put detailed test output logs.
        filter_name = self._filter or os.path.basename(self._caselist)
        logging.info('dEQP test filter = %s', filter_name)
        self._log_path = os.path.join(os.getcwd(), 'deqp-runner')
        shutil.rmtree(self._log_path, ignore_errors=True)
        os.mkdir(self._log_path)

        if self._debug:
            # LogReader works on /var/log/messages by default.
            self._log_reader = cros_logging.LogReader()
            self._log_reader.set_start_by_current()

        executable = self._get_executable(api)
        # Must be in the executable directory when running for it to find it's
        # test data files!
        os.chdir(os.path.dirname(executable))

        command = ['deqp-runner', 'run']
        command.append('--output=%s' % self._log_path)
        command.append('--deqp=%s' % executable)
        command.append('--caselist=%s' % self._caselist)
        if self._shard_number != 0:
            command.append('--fraction-start=%d' % (self._shard_number + 1))
        if self._shard_count != 1:
            command.append('--fraction=%d' % self._shard_count)

        self.add_filter_arg(command, self._flakes, '--flakes',
                            'known_flakes.txt')
        self.add_filter_arg(command, self._skips, '--skips', 'skips.txt')
        self.add_filter_arg(command, self._fails, '--baseline',
                            'expected-fails.txt')

        command.append('--')
        command.append('--deqp-surface-type=%s' % self._surface)
        command.append('--deqp-surface-width=%s' % self._width)
        command.append('--deqp-surface-height=%s' % self._height)
        command.append('--deqp-gl-config-name=rgba8888d24s8ms0')

        # TODO: Get the deqp ebuild to include testlog-to-xml and the
        # stylesheets, and have the runner invoke it for failures.

        # Must initialize because some errors don't repopulate
        # run_result, leaving old results.
        run_result = {}
        try:
            run_result = utils.run(command,
                                   env=self._env,
                                   ignore_status=True,
                                   stdout_tee=utils.TEE_TO_LOGS,
                                   stdout_level=logging.INFO,
                                   stderr_tee=utils.TEE_TO_LOGS)
        except error.CmdError:
            raise error.TestFail("Failed starting '%s'" % command)

        # Update failing tests to the chrome perf dashboard records.
        try:
            with open(os.path.join(self._log_path,
                                   'failures.csv')) as fails_file:
                for line in fails_file.readlines():
                    self.add_failures(line)
        except IOError:
            # failures.csv not created if there were were no failures
            pass

        # TODO: We should have a chrome perf dashboard where we report the
        # Flakes out of results.csv so we can preemptively manage the flakes
        # list per board, to avoid causing run failures for known flakes when
        # the automatic flake detection doesn't catch it.

        if run_result.exit_status != 0:
            raise error.TestFail('dEQP run failed with status code %d' %
                                 run_result.exit_status)

        # self.write_perf_keyval(test_results) # XXX