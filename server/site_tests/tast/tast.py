# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
import shutil
import tempfile

import dateutil.parser
import six

from autotest_lib.client.common_lib import base_job
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import dev_server
from autotest_lib.client.common_lib.cros import tpm_utils
from autotest_lib.server import test
from autotest_lib.server import utils
from autotest_lib.server.cros.network import wifi_test_context_manager
from autotest_lib.server.hosts import cros_host
from autotest_lib.server.hosts import servo_host
from autotest_lib.server.hosts import servo_constants
from autotest_lib.utils import labellib
from autotest_lib.site_utils.rpm_control_system import utils as rpm_utils
from six.moves import urllib
import yaml

# A datetime.DateTime representing the Unix epoch in UTC.
_UNIX_EPOCH = dateutil.parser.parse('1970-01-01T00:00:00Z')

# Keywords that are used in result json file.
_KEY_NAME = 'name'
_KEY_START = 'start'
_KEY_END = 'end'
_KEY_ERRORS = 'errors'
_KEY_SKIP_REASON = 'skipReason'
_KEY_REASON = 'reason'
_KEY_TIME = 'time'


def split_arguments(args):
    """Splits arguments into the autotest and tast variable assignments.
    Use the results as command_args and varslist respectively.

    @param args: List of strings passed to test_that --args

    @returns Array of Tauto args, Array of TAST variable assignments.
    """

    auto_args = []
    tast_vars = []
    for a in args:
        if a.startswith("tast."):
            tast_vars.append(a[5:])
        else:
            auto_args.append(a)
    return auto_args, tast_vars


def _encode_text(text):
    """Takes an unicode string into native string
    (bytes for python 2 and text for python 3).
    """
    if six.PY2:
        return text.encode('utf-8')
    return text


def _encode_json(j):
    """Takes JSON object parsed by json.load() family, and encode each unicode
    strings into str.
    """
    if isinstance(j, six.text_type):
        return _encode_text(j)
    if isinstance(j, list):
        return [_encode_json(x) for x in j]
    if isinstance(j, dict):
        return dict((_encode_json(k), _encode_json(v))
                    for k, v in six.iteritems(j))
    return j

class tast(test.test):
    """Autotest server test that runs a Tast test suite.

    Tast is an integration-testing framework analagous to the test-running
    portion of Autotest. See
    https://chromium.googlesource.com/chromiumos/platform/tast/ for more
    information.

    This class runs the "tast" command locally to execute a Tast test suite on a
    remote DUT.
    """
    version = 1

    # Maximum time to wait for various tast commands to complete, in seconds.
    _VERSION_TIMEOUT_SEC = 10
    _DOWNLOAD_TIMEOUT_SEC = 120
    _LIST_TIMEOUT_SEC = 30

    # Additional time to add to the run timeout (e.g. for collecting crashes and
    # logs).
    _RUN_OVERHEAD_SEC = 20
    # Additional time given to the run command to exit before it's killed.
    _RUN_EXIT_SEC = 5

    # Number of times to retry SSH connection attempts to the DUT.
    _SSH_CONNECT_RETRIES = 2

    # File written by the tast command containing test results, as
    # newline-terminated JSON TestResult objects.
    _STREAMED_RESULTS_FILENAME = 'streamed_results.jsonl'

    # Text file written by the tast command if a global error caused the test
    # run to fail (e.g. SSH connection to DUT was lost).
    _RUN_ERROR_FILENAME = 'run_error.txt'

    # Maximum number of failing and missing tests to include in error messages.
    _MAX_TEST_NAMES_IN_ERROR = 3

    # Default paths where Tast files are installed by Portage packages.
    _PORTAGE_TAST_PATH = '/usr/bin/tast'

    # Alternate locations for Tast files when using Server-Side Packaging.
    # These files are installed from autotest_server_package.tar.bz2.
    _SSP_ROOT = '/usr/local/tast'
    _SSP_TAST_PATH = os.path.join(_SSP_ROOT, 'tast')
    _SSP_REMOTE_BUNDLE_DIR = os.path.join(_SSP_ROOT, 'bundles/remote')
    _SSP_REMOTE_DATA_DIR = os.path.join(_SSP_ROOT, 'data')
    _SSP_REMOTE_TEST_RUNNER_PATH = os.path.join(_SSP_ROOT, 'remote_test_runner')
    _SSP_DEFAULT_VARS_DIR_PATH = os.path.join(_SSP_ROOT, 'vars')

    # Prefix added to Tast test names when writing their results to TKO
    # status.log files.
    _TEST_NAME_PREFIX = 'tast.'

    # Prefixes of keyval keys recorded for missing tests.
    _MISSING_TEST_KEYVAL_PREFIX = 'tast_missing_test.'

    # Job start/end TKO event status codes from base_client_job._rungroup in
    # client/bin/job.py.
    _JOB_STATUS_START = 'START'
    _JOB_STATUS_END_GOOD = 'END GOOD'
    _JOB_STATUS_END_FAIL = 'END FAIL'
    _JOB_STATUS_END_ABORT = 'END ABORT'

    # In-job TKO event status codes from base_client_job._run_test_base in
    # client/bin/job.py and client/common_lib/error.py.
    _JOB_STATUS_GOOD = 'GOOD'
    _JOB_STATUS_FAIL = 'FAIL'

    # Status reason used when an individual Tast test doesn't finish running.
    _TEST_DID_NOT_FINISH_MSG = 'Test did not finish'

    def initialize(self,
                   host,
                   test_exprs,
                   ignore_test_failures=False,
                   max_run_sec=3600,
                   command_args=[],
                   install_root='/',
                   ssp=None,
                   build=None,
                   build_bundle='cros',
                   run_private_tests=True,
                   varsfiles=[],
                   download_data_lazily=True,
                   clear_tpm=False,
                   totalshards=1,
                   shardindex=0,
                   companion_duts={},
                   varslist=[],
                   maybemissingvars='',
                   vars_gs_path=''):
        """
        @param host: remote.RemoteHost instance representing DUT.
        @param test_exprs: Array of strings describing tests to run.
        @param ignore_test_failures: If False, this test will fail if individual
            Tast tests report failure. If True, this test will only fail in
            response to the tast command failing to run successfully. This
            should generally be False when the test is running inline and True
            when it's running asynchronously.
        @param max_run_sec: Integer maximum running time for the "tast run"
            command in seconds.
        @param command_args: List of arguments passed on the command line via
            test_that's --args flag, i.e. |args| in control file.
        @param install_root: Root directory under which Tast binaries are
            installed. Alternate values may be passed by unit tests.
        @param ssp: Whether to use SSP files. Default is to auto-detect.
        @param build: Whether to build test runners and test bundles.
            Default is to build if and only if SSP is unavailable
            (i.e. build = not ssp).
        @param build_bundle: Test bundle name to build. Effective only when
            build=True.
        @param run_private_tests: Download and run private tests. Effective
            only when build=False. When build=True, build_bundle can be
            specified to build and run a private bundle.
        @param varsfiles: list of names of yaml files containing variables set
            in |-varsfile| arguments.
        @param download_data_lazily: If True, external data files are downloaded
            lazily between tests. If false, external data files are downloaded
            in a batch before running tests.
        @param clear_tpm: clear the TPM first before running the tast tests.
        @param totalshards: Total number of shards.
        @param shardindex: The shard index to be run.
        @param companion_duts: A map of role to DUT name to tast run command as
            |-companiondut| arguments. Each entry in the map will be formatted
            as "role:dut" for each -companiondut argument.
        @param varslist: list of strings to pass to tast run command as |-vars|
            arguments. Each string should be formatted as "name=value".
        @param maybemissingvars: a regex to pass to tast run command as
            |-maybemissingvars| arguments.
        @param vars_gs_path: gs path to load vars from. The vars are loaded
            from gs in json format (key = value), then stored in a local
            yaml file. The local file name is then appended to |-varsfiles|.

        @raises error.TestFail if the Tast installation couldn't be found.
        """
        if ssp is None:
            ssp = os.path.exists(self._SSP_TAST_PATH)
        if build is None:
            build = not ssp

        self._host = host
        self._test_exprs = test_exprs
        self._ignore_test_failures = ignore_test_failures
        self._max_run_sec = max_run_sec
        self._command_args = command_args
        self._install_root = install_root
        self._ssp = ssp
        self._build = build
        self._build_bundle = build_bundle
        self._run_private_tests = run_private_tests
        self._fake_now = None
        self._varsfiles = varsfiles
        self._varslist = varslist
        self._download_data_lazily = download_data_lazily
        self._clear_tpm = clear_tpm
        self._totalshards = totalshards
        self._shardindex = shardindex
        self._companion_duts = companion_duts
        self._maybemissingvars = maybemissingvars
        self._pull_varsfiles_from_gs(vars_gs_path)

        # List of JSON objects describing tests that will be run. See Test in
        # src/platform/tast/src/chromiumos/tast/testing/test.go for details.
        self._tests_to_run = []

        # List of JSON objects corresponding to tests from
        # _STREAMED_RESULTS_FILENAME. See TestResult in
        # src/platform/tast/src/chromiumos/cmd/tast/run/results.go for details.
        self._test_results = []

        # Error message read from _RUN_ERROR_FILENAME, if any.
        self._run_error = None

        self._tast_path = self._get_path(
            self._SSP_TAST_PATH if ssp else self._PORTAGE_TAST_PATH)

        # Register a hook to write the results of individual Tast tests as
        # top-level entries in the TKO status.log file.
        self.job.add_post_run_hook(self._log_all_tests)

    def run_once(self):
        """Runs a single iteration of the test."""

        if self._clear_tpm:
            tpm_utils.ClearTPMOwnerRequest(self._host, wait_for_ready=True)

        self._log_version()
        self._find_devservers()

        self._ensure_bundles()

        # Shortcut if no test belongs to the specified test_exprs.
        if not self._get_tests_to_run():
            return

        run_failed = False
        try:
            self._run_tests()
        except:
            run_failed = True
            raise
        finally:
            self._read_run_error()
            # Parse partial results even if the tast command didn't finish.
            self._parse_results(run_failed)

    def set_fake_now_for_testing(self, now):
        """Sets a fake timestamp to use in place of time.time() for unit tests.

        @param now Numeric timestamp as would be returned by time.time().
        """
        self._fake_now = now

    def _pull_varsfiles_from_gs(self, vars_gs_path):
        """Pulls varsfiles from GS, stores it as a local file and appends the
        file name to varsfiles.

        @param varsgspath Path to varsfiles in GS e.g.
            'config/perf_cuj/perf_cuj.config'.
        """
        if not vars_gs_path:
            return

        devservers = dev_server.ImageServer.get_available_devservers()
        devserver_url = devservers[0][0]
        if not devserver_url:
            logging.warning("No devserver_url")
            return

        logging.info('Using devserver: %s', devserver_url)
        labels = self._host.host_info_store.get().labels
        build = labellib.LabelsMapping(labels).get(labellib.Key.CROS_VERSION)
        if not build:
            logging.warning(
                    "Not able to detect build, means not running on Moblab.")
            return

        ds = dev_server.ImageServer(devserver_url)
        gs_bucket = dev_server._get_image_storage_server()
        if not gs_bucket:
            logging.warning("No gs_bucket")
            return

        config_path, config_file = os.path.split(vars_gs_path)
        archive_url = os.path.join(gs_bucket, config_path.strip('/'))
        logging.info('Staging configuration from %s.', gs_bucket)
        try:
            ds.stage_artifacts(build,
                               archive_url=archive_url,
                               files=[config_file])
        except Exception as e:
            logging.error('Staging artifacts failed: %s', str(e))
            return

        logging.info('Parsing configuration from %s.', archive_url)
        config_url = os.path.join(devserver_url, 'static',
                                  vars_gs_path.strip('/'))
        response = urllib.request.urlopen(config_url)
        vars = json.loads(response.read())
        test_args = dict()
        for key in vars:
            test_args[key] = vars[key]
        logging.info('Read %d values from remote configuration.', len(vars))

        with tempfile.NamedTemporaryFile(suffix='.yaml',
                                         delete=False) as temp_file:
            yaml.dump(test_args, stream=temp_file, default_flow_style=False)
            self._varsfiles.append(temp_file.name)

    def _get_path(self, path):
        """Returns the path to an installed Tast-related file or directory.

        @param path: Absolute paths in root filesystem, e.g. "/usr/bin/tast".

        @returns Absolute path within install root, e.g.
            "/usr/local/tast/usr/bin/tast".
        """
        return os.path.join(self._install_root, os.path.relpath(path, '/'))

    def _get_servo_args(self):
        """Gets servo-related arguments to pass to "tast run".

        @returns List of command-line flag strings that should be inserted in
            the command line after "tast run".
        """
        # Start with information provided by the Autotest database.
        merged_args = {}
        host_args = servo_host.get_servo_args_for_host(self._host)
        if host_args:
            merged_args.update(host_args)

        # Incorporate information that was passed manually.
        args_dict = utils.args_to_dict(self._command_args)
        merged_args.update(cros_host.CrosHost.get_servo_arguments(args_dict))

        logging.info('Autotest servo-related args: %s', merged_args)
        host_arg = merged_args.get(servo_constants.SERVO_HOST_ATTR)
        port_arg = merged_args.get(servo_constants.SERVO_PORT_ATTR)
        if not host_arg or not port_arg:
            return []
        return ['-var=servo=%s:%s' % (host_arg, port_arg)]

    def _get_firmware_args(self):
        """Gets firmware-related arguments to pass to "tast run".

        @returns List of command-line flag strings that should be inserted in
            the command line after "tast run".
        """
        # Incorporate information that was passed manually.
        args_dict = utils.args_to_dict(self._command_args)

        args = []
        no_ec_sync = args_dict.get("no_ec_sync")
        if no_ec_sync:
            args += ['-var=firmware.no_ec_sync=' + no_ec_sync]
        logging.info('Firmware args: %s', args)
        return args

    def _get_rpm_args(self):
        """Gets rpm-related arguments to pass to "tast run".

        @returns List of command-line flag strings that should be inserted in
            the command line after "tast run".
        """
        info = self._host.host_info_store.get()
        args = []
        forward_args = [
                (rpm_utils.POWERUNIT_HOSTNAME_KEY, 'powerunitHostname=%s'),
                (rpm_utils.POWERUNIT_OUTLET_KEY, 'powerunitOutlet=%s'),
                (rpm_utils.HYDRA_HOSTNAME_KEY, 'hydraHostname=%s'),
        ]
        for key, var_arg in forward_args:
            if key in info.attributes:
                args += ['-var=' + var_arg % info.attributes[key]]
        logging.info('RPM args: %s', args)
        return args

    def _get_wificell_args(self):
        """Gets wificell-related (router, pcap) arguments to pass to "tast run".

        @returns List of command-line flag strings that should be inserted in
            the command line after "tast run".
        """
        # Incorporate information that was passed manually.
        args_dict = utils.args_to_dict(self._command_args)
        args = []
        # Alias of WiFiTestContextManager.
        WiFiManager = wifi_test_context_manager.WiFiTestContextManager
        # TODO(crbug.com/1065601): plumb other WiFi test specific arguments,
        #     e.g. pcap address. See: WiFiTestContextManager's constants.
        forward_args = [
            (WiFiManager.CMDLINE_ROUTER_ADDR, 'router=%s'),
            (WiFiManager.CMDLINE_PCAP_ADDR, 'pcap=%s'),
        ]
        for key, var_arg in forward_args:
            if key in args_dict:
                args += ['-var=' + var_arg % args_dict[key]]
        # Append "routers" var for supporting multi-router tests with current
        # two-AP fixture setup (with specified router_addr and pcap_addr args).
        # TODO(b/171949862): remove this when a new multi-router fixture is
        # defined and rolled out to the lab.
        if (WiFiManager.CMDLINE_ROUTER_ADDR in args_dict
                    and WiFiManager.CMDLINE_PCAP_ADDR in args_dict):
            args += [
                    '-var=routers=%s,%s' %
                    (args_dict[WiFiManager.CMDLINE_ROUTER_ADDR],
                     args_dict[WiFiManager.CMDLINE_PCAP_ADDR])
            ]
        logging.info('Autotest wificell-related args: %s', args)
        return args

    def _get_cloud_storage_info(self):
        """Gets the cloud storage bucket URL to pass to tast.

        @returns Cloud storage bucket URL that should be inserted in
            the command line after "tast run".
        """
        gs_bucket = dev_server._get_image_storage_server()
        args_dict = utils.args_to_dict(self._command_args)
        build = args_dict.get('build')
        if not build:
            labels = self._host.host_info_store.get().labels
            build = labellib.LabelsMapping(labels).get(
                labellib.Key.CROS_VERSION)

        if not gs_bucket or not build:
            return []
        gs_path = gs_bucket + build
        if not gs_path.endswith('/'):
            gs_path += '/'
        logging.info('Cloud storage bucket: %s', gs_path)
        return ['-buildartifactsurl=%s' % gs_path]

    def _find_devservers(self):
        """Finds available devservers.

        The result is saved as self._devserver_args.
        """
        devservers, _ = dev_server.ImageServer.get_available_devservers(
            self._host.hostname, prefer_local_devserver=True)
        logging.info('Using devservers: %s', ', '.join(devservers))
        self._devserver_args = ['-devservers=%s' % ','.join(devservers)]

    def _log_version(self):
        """Runs the tast command locally to log its version."""
        try:
            utils.run([self._tast_path, '-version'],
                      timeout=self._VERSION_TIMEOUT_SEC,
                      stdout_tee=utils.TEE_TO_LOGS,
                      stderr_tee=utils.TEE_TO_LOGS,
                      stderr_is_expected=True,
                      stdout_level=logging.INFO,
                      stderr_level=logging.ERROR)
        except error.CmdError as e:
            logging.error('Failed to log tast version: %s', str(e))

    def _run_tast(self,
                  subcommand,
                  extra_subcommand_args,
                  test_exprs,
                  timeout_sec,
                  log_stdout=False,
                  ignore_status=False):
        """Runs the tast command locally to e.g. list available tests or perform
        testing against the DUT.

        @param subcommand: Subcommand to pass to the tast executable, e.g. 'run'
            or 'list'.
        @param extra_subcommand_args: List of additional subcommand arguments.
        @param test_exprs: Array of strings describing tests to run.
        @param timeout_sec: Integer timeout for the command in seconds.
        @param log_stdout: If true, write stdout to log.
        @param ignore_status: If true, command execution errors are ignored.

        @returns client.common_lib.utils.CmdResult object describing the result.

        @raises error.TestFail if the tast command fails or times out.
        """
        cmd = [
            self._tast_path,
            '-verbose=true',
            '-logtime=false',
            subcommand,
            '-sshretries=%d' % self._SSH_CONNECT_RETRIES,
            '-downloaddata=%s' % (
                'lazy' if self._download_data_lazily else 'batch'),
            '-totalshards=%s' % self._totalshards,
            '-shardindex=%s' % self._shardindex,
        ]
        if self._build:
            cmd.extend([
                '-build=true',
                '-buildbundle=%s' % self._build_bundle,
                '-checkbuilddeps=false',
            ])
        else:
            cmd.append('-build=false')
            if self._ssp:
                remote_test_runner_path = self._get_path(
                    self._SSP_REMOTE_TEST_RUNNER_PATH)
                if not os.path.exists(remote_test_runner_path):
                    raise error.TestFail(
                        '%s does not exist (broken SSP?)' %
                        remote_test_runner_path)
                cmd.extend([
                    '-remotebundledir=%s' % self._get_path(
                        self._SSP_REMOTE_BUNDLE_DIR),
                    '-remotedatadir=%s' % self._get_path(
                        self._SSP_REMOTE_DATA_DIR),
                    '-remoterunner=%s' % remote_test_runner_path,
                ])
                if subcommand == 'run':
                    cmd.append('-defaultvarsdir=%s' %
                               self._get_path(self._SSP_DEFAULT_VARS_DIR_PATH))
            if self._run_private_tests:
                cmd.append('-downloadprivatebundles=true')
        cmd.extend(self._devserver_args)
        cmd.extend(extra_subcommand_args)
        cmd.append('%s:%d' % (self._host.hostname, self._host.port))
        cmd.extend(test_exprs)

        logging.info('Running %s',
                     ' '.join([utils.sh_quote_word(a) for a in cmd]))
        try:
            return utils.run(
                    cmd,
                    ignore_status=ignore_status,
                    timeout=timeout_sec,
                    stdout_tee=(utils.TEE_TO_LOGS if log_stdout else None),
                    stderr_tee=utils.TEE_TO_LOGS,
                    stderr_is_expected=True,
                    stdout_level=logging.INFO,
                    stderr_level=logging.ERROR)
        except error.CmdError as e:
            # Run several commands to debug possible network issues.
            # TODO(b/189332919): Remove this logic once we finish debugging.
            logging.info('Tast exited abnormally. Running several commands to '
                         'diagnose possible network issues...')
            utils.run('time getent ahosts %s' % self._host.hostname,
                      timeout=60,
                      ignore_status=True,
                      stdout_tee=utils.TEE_TO_LOGS,
                      stderr_tee=utils.TEE_TO_LOGS,
                      stderr_is_expected=True,
                      stdout_level=logging.INFO,
                      stderr_level=logging.ERROR)
            utils.run(
                    'ssh '
                    # Enable maximum debug logging.
                    '-vvv '
                    # Disable connection sharing to debug connection issues.
                    '-o ControlPath=none '
                    # Following arguments were copied from Autotest logs.
                    '-a -x '
                    '-o StrictHostKeyChecking=no '
                    '-o UserKnownHostsFile=/dev/null '
                    '-o BatchMode=yes '
                    '-o ConnectTimeout=10 '
                    '-o ConnectionAttempts=3 '
                    '-l root -p %d %s true' %
                    (self._host.port, self._host.hostname),
                    timeout=60,
                    ignore_status=True,
                    stdout_tee=utils.TEE_TO_LOGS,
                    stderr_tee=utils.TEE_TO_LOGS,
                    stderr_is_expected=True,
                    stdout_level=logging.INFO,
                    stderr_level=logging.ERROR)
            # The tast command's output generally ends with a line describing
            # the error that was encountered; include it in the first line of
            # the TestFail exception. Fall back to stderr if stdout is empty (as
            # is the case with the "list" subcommand, which uses stdout to print
            # test data).
            get_last_line = lambda s: s.strip().split('\n')[-1].strip()
            last_line = (get_last_line(e.result_obj.stdout) or
                         get_last_line(e.result_obj.stderr))
            msg = (' (last line: %s)' % last_line) if last_line else ''
            raise error.TestFail('Failed to run tast%s: %s' % (msg, str(e)))
        except error.CmdTimeoutError as e:
            raise error.TestFail('Got timeout while running tast: %s' % str(e))

    def _ensure_bundles(self):
        """Runs the tast command to ensure all test bundles are available.

        If private test bundles are available, they are downloaded from cloud
        storage and installed to the DUT. Otherwise it is no-nop.

        Note that "tast list" also downloads private test bundles if they are
        missing. Nevertheless we attempt to download them in advance because
        "tast list" cannot emit detailed logs due to technical limitations and
        often make it difficult to debug issues related to private test bundle
        installation.
        """
        logging.info('Downloading private test bundles (if any)')
        temp_dir = tempfile.mkdtemp()
        try:
            args = ['-resultsdir=' + temp_dir] + self._get_cloud_storage_info()
            for role, dut in sorted(self._companion_duts.items()):
                args.append('-companiondut=%s:%s' % (role, dut))

            # Start "tast run" with an attribute expression matching no test
            # to trigger a private test bundle download.
            # Note that Tast CLI will exit abnormally when no test matches,
            # so we set ignore_status=True to avoid throwing TestFail.
            self._run_tast('run',
                           args, ['("group:none")'],
                           tast._DOWNLOAD_TIMEOUT_SEC,
                           log_stdout=True,
                           ignore_status=True)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _get_tests_to_run(self):
        """Runs the tast command to update the list of tests that will be run.

        @returns False if no tests matched by test_exprs; True otherwise

        @raises error.TestFail if the tast command fails or times out.
        """
        logging.info('Getting list of tests that will be run')
        args = ['-json=true'] + self._get_cloud_storage_info()
        result = self._run_tast('list', args, self._test_exprs,
                                self._LIST_TIMEOUT_SEC)
        try:
            self._tests_to_run = _encode_json(json.loads(
                    result.stdout.strip()))
        except ValueError as e:
            raise error.TestFail('Failed to parse tests: %s' % str(e))
        if len(self._tests_to_run) == 0:
            expr = ' '.join([utils.sh_quote_word(a) for a in self._test_exprs])
            logging.warning('No tests matched by %s', expr)
            return False

        logging.info('Expect to run %d test(s)', len(self._tests_to_run))
        return True

    def _run_tests(self):
        """Runs the tast command to perform testing.

        @raises error.TestFail if the tast command fails or times out (but not
            if individual tests fail).
        """
        args = [
                '-resultsdir=' + self.resultsdir,
                '-waituntilready=true',
                '-timeout=' + str(self._max_run_sec),
                '-continueafterfailure=true',
        ]
        args.extend(self._get_servo_args())
        args.extend(self._get_rpm_args())
        args.extend(self._get_wificell_args())
        args.extend(self._get_cloud_storage_info())
        args.extend(self._get_firmware_args())

        for varsfile in self._varsfiles:
            args.append('-varsfile=%s' % varsfile)

        for var in self._varslist:
            args.append('-var=%s' % var)

        if self._maybemissingvars:
            args.append('-maybemissingvars=%s' % self._maybemissingvars)

        for role, dut in sorted(self._companion_duts.items()):
            args.append('-companiondut=%s:%s:%d' % (role, dut.hostname, dut.port))

        logging.info('Running tests with timeout of %d sec', self._max_run_sec)
        self._run_tast('run',
                       args,
                       self._test_exprs,
                       self._max_run_sec + tast._RUN_EXIT_SEC,
                       log_stdout=True)

    def _read_run_error(self):
        """Reads a global run error message written by the tast command."""
        # The file is only written if a run error occurred.
        path = os.path.join(self.resultsdir, self._RUN_ERROR_FILENAME)
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._run_error = f.read().strip()

    def _parse_results(self, ignore_missing_file):
        """Parses results written by the tast command.

        @param ignore_missing_file: If True, return without raising an exception
            if the Tast results file is missing. This is used to avoid raising a
            new error if there was already an earlier error while running the
            tast process.

        @raises error.TestFail if results file is missing and
            ignore_missing_file is False, or one or more tests failed and
            _ignore_test_failures is false.
        """
        # The file may not exist if "tast run" failed to run. Tests that were
        # seen from the earlier "tast list" command will be reported as having
        # missing results.
        path = os.path.join(self.resultsdir, self._STREAMED_RESULTS_FILENAME)
        if not os.path.exists(path):
            if ignore_missing_file:
                return
            raise error.TestFail('Results file %s not found' % path)

        failed = []
        seen_test_names = set()
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    test = _encode_json(json.loads(line))
                except ValueError as e:
                    raise error.TestFail('Failed to parse %s: %s' % (path, e))
                self._test_results.append(test)

                name = test[_KEY_NAME]
                seen_test_names.add(name)

                if test.get(_KEY_ERRORS):
                    for err in test[_KEY_ERRORS]:
                        logging.warning('%s: %s', name, err[_KEY_REASON])
                    failed.append(name)
                else:
                    # The test will have a zero (i.e. 0001-01-01 00:00:00 UTC)
                    # end time (preceding the Unix epoch) if it didn't report
                    # completion.
                    if _rfc3339_time_to_timestamp(test[_KEY_END]) <= 0:
                        failed.append(name)

        missing = [
                t[_KEY_NAME] for t in self._tests_to_run
                if t[_KEY_NAME] not in seen_test_names
        ]

        if missing:
            self._record_missing_tests(missing)

        failure_msg = self._get_failure_message(failed, missing)
        if failure_msg:
            raise error.TestFail(failure_msg)

    def _get_failure_message(self, failed, missing):
        """Returns an error message describing failed and/or missing tests.

        @param failed: List of string names of Tast tests that failed.
        @param missing: List of string names of Tast tests with missing results.

        @returns String to be used as error.TestFail message.
        """
        def list_tests(names):
            """Returns a string listing tests.

            @param names: List of string test names.

            @returns String listing tests.
            """
            s = ' '.join(sorted(names)[:self._MAX_TEST_NAMES_IN_ERROR])
            if len(names) > self._MAX_TEST_NAMES_IN_ERROR:
                s += ' ...'
            return s

        msg = ''
        if failed and not self._ignore_test_failures:
            msg = '%d failed: %s' % (len(failed), list_tests(failed))
        if missing:
            if msg:
                msg += '; '
            msg += '%d missing: %s' % (len(missing), list_tests(missing))
        return msg

    def _log_all_tests(self):
        """Writes entries to the TKO status.log file describing the results of
        all tests.
        """
        seen_test_names = set()
        for test in self._test_results:
            self._log_test(test)
            seen_test_names.add(test[_KEY_NAME])

    def _log_test(self, test):
        """Writes events to the TKO status.log file describing the results from
        a Tast test.

        @param test: A JSON object corresponding to a single test from a Tast
            results.json file. See TestResult in
            src/platform/tast/src/chromiumos/cmd/tast/run/results.go for
            details.
        """
        name = test[_KEY_NAME]
        start_time = _rfc3339_time_to_timestamp(test[_KEY_START])
        end_time = _rfc3339_time_to_timestamp(test[_KEY_END])

        test_reported_errors = bool(test.get(_KEY_ERRORS))
        test_skipped = bool(test.get(_KEY_SKIP_REASON))
        # The test will have a zero (i.e. 0001-01-01 00:00:00 UTC) end time
        # (preceding the Unix epoch) if it didn't report completion.
        test_finished = end_time > 0

        # Avoid reporting tests that were skipped.
        if test_skipped and not test_reported_errors:
            return

        self._log_test_event(self._JOB_STATUS_START, name, start_time)

        if test_finished and not test_reported_errors:
            self._log_test_event(self._JOB_STATUS_GOOD, name, end_time)
            end_status = self._JOB_STATUS_END_GOOD
        else:
            # The previous START event automatically increases the log
            # indentation level until the following END event.
            if test_reported_errors:
                for err in test[_KEY_ERRORS]:
                    error_time = _rfc3339_time_to_timestamp(err[_KEY_TIME])
                    self._log_test_event(self._JOB_STATUS_FAIL, name,
                                         error_time, err[_KEY_REASON])
            if not test_finished:
                # If a run-level error was encountered (e.g. the SSH connection
                # to the DUT was lost), report it here to make it easier to see
                # the reason why the test didn't finish.
                if self._run_error:
                    self._log_test_event(self._JOB_STATUS_FAIL, name,
                                         start_time, self._run_error)
                self._log_test_event(self._JOB_STATUS_FAIL, name, start_time,
                                     self._TEST_DID_NOT_FINISH_MSG)
                end_time = start_time

            end_status = self._JOB_STATUS_END_FAIL

        self._log_test_event(end_status, name, end_time)

    def _log_test_event(self, status_code, test_name, timestamp, message=''):
        """Logs a single event to the TKO status.log file.

        @param status_code: Event status code, e.g. 'END GOOD'. See
            client/common_lib/log.py for accepted values.
        @param test_name: Tast test name, e.g. 'ui.ChromeLogin'.
        @param timestamp: Event timestamp (as seconds since Unix epoch).
        @param message: Optional human-readable message.
        """
        full_name = self._TEST_NAME_PREFIX + test_name
        # The TKO parser code chokes on floating-point timestamps.
        entry = base_job.status_log_entry(status_code,
                                          None,
                                          full_name,
                                          message,
                                          None,
                                          timestamp=int(timestamp))
        self.job.record_entry(entry, False)

    def _record_missing_tests(self, missing):
        """Records tests with missing results in job keyval file.

        @param missing: List of string names of Tast tests with missing results.
        """
        keyvals = {}
        for i, name in enumerate(sorted(missing)):
            keyvals['%s%d' % (self._MISSING_TEST_KEYVAL_PREFIX, i)] = name
        utils.write_keyval(self.job.resultdir, keyvals)


class _LessBrokenParserInfo(dateutil.parser.parserinfo):
    """dateutil.parser.parserinfo that interprets years before 100 correctly.

    Our version of dateutil.parser.parse misinteprets an unambiguous string like
    '0001-01-01T00:00:00Z' as having a two-digit year, which it then converts to
    2001. This appears to have been fixed by
    https://github.com/dateutil/dateutil/commit/fc696254. This parserinfo
    implementation always honors the provided year to prevent this from
    happening.
    """
    def convertyear(self, year, century_specified=False):
        """Overrides convertyear in dateutil.parser.parserinfo."""
        return int(year)


def _rfc3339_time_to_timestamp(time_str):
    """Converts an RFC3339 time into a Unix timestamp.

    @param time_str: RFC3339-compatible time, e.g.
        '2018-02-25T07:45:35.916929332-07:00'.

    @returns Float number of seconds since the Unix epoch. Negative if the time
        precedes the epoch.
    """
    dt = dateutil.parser.parse(time_str, parserinfo=_LessBrokenParserInfo())
    return (dt - _UNIX_EPOCH).total_seconds()
