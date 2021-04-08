# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import itertools
import json
import logging
import os
import re
import shutil
import urlparse

from datetime import datetime, timedelta
from xml.etree import ElementTree

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib import utils
from autotest_lib.client.common_lib.cros import dev_server
from autotest_lib.client.cros.update_engine import dlc_util
from autotest_lib.client.cros.update_engine import update_engine_event as uee
from autotest_lib.client.cros.update_engine import update_engine_util
from autotest_lib.server import autotest
from autotest_lib.server import test
from autotest_lib.server.cros.dynamic_suite import tools
from autotest_lib.server.hosts.tls_client_aufork import connection
from autotest_lib.server.hosts.tls_client_aufork import fake_omaha
from chromite.lib import auto_updater
from chromite.lib import auto_updater_transfer
from chromite.lib import remote_access
from chromite.lib import retry_util


class UpdateEngineTest(test.test, update_engine_util.UpdateEngineUtil):
    """Base class for all autoupdate_ server tests.

    Contains useful functions shared between tests like staging payloads
    on devservers, verifying hostlogs, and launching client tests.

    """
    version = 1

    # Timeout periods, given in seconds.
    _INITIAL_CHECK_TIMEOUT = 12 * 60
    _DOWNLOAD_STARTED_TIMEOUT = 4 * 60
    _DOWNLOAD_FINISHED_TIMEOUT = 20 * 60
    _UPDATE_COMPLETED_TIMEOUT = 4 * 60
    _POST_REBOOT_TIMEOUT = 15 * 60

    # The names of the two hostlog files we will be verifying.
    _DEVSERVER_HOSTLOG_ROOTFS = 'devserver_hostlog_rootfs'
    _DEVSERVER_HOSTLOG_REBOOT = 'devserver_hostlog_reboot'

    # Name of the logfile generated by nebraska.py.
    _NEBRASKA_LOG = 'nebraska.log'

    # Version we tell the DUT it is on before update.
    _CUSTOM_LSB_VERSION = '0.0.0.0'

    _CELLULAR_BUCKET = 'gs://chromeos-throw-away-bucket/CrOSPayloads/Cellular/'

    _TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


    def initialize(self, host=None, hosts=None):
        """
        Sets default variables for the test.

        @param host: The DUT we will be running on.
        @param hosts: If we are running a test with multiple DUTs (eg P2P)
                      we will use hosts instead of host.

        """
        self._current_timestamp = None
        self._host = host
        # Some AU tests use multiple DUTs
        self._hosts = hosts

        # Define functions used in update_engine_util.
        self._run = self._host.run if self._host else None
        self._get_file = self._host.get_file if self._host else None

        # Utilities for DLC management
        self._dlc_util = dlc_util.DLCUtil(self._run)


    def cleanup(self):
        """Clean up update_engine autotests."""
        if self._host:
            self._host.get_file(self._UPDATE_ENGINE_LOG, self.resultsdir)


    def _get_expected_events_for_rootfs_update(self, source_release):
        """
        Creates a list of expected events fired during a rootfs update.

        There are 4 events fired during a rootfs update. We will create these
        in the correct order.

        @param source_release: The source build version.

        """
        return [
            uee.UpdateEngineEvent(
                version=source_release,
                timeout=self._INITIAL_CHECK_TIMEOUT),
            uee.UpdateEngineEvent(
                event_type=uee.EVENT_TYPE_DOWNLOAD_STARTED,
                event_result=uee.EVENT_RESULT_SUCCESS,
                version=source_release,
                timeout=self._DOWNLOAD_STARTED_TIMEOUT),
            uee.UpdateEngineEvent(
                event_type=uee.EVENT_TYPE_DOWNLOAD_FINISHED,
                event_result=uee.EVENT_RESULT_SUCCESS,
                version=source_release,
                timeout=self._DOWNLOAD_FINISHED_TIMEOUT),
            uee.UpdateEngineEvent(
                event_type=uee.EVENT_TYPE_UPDATE_COMPLETE,
                event_result=uee.EVENT_RESULT_SUCCESS,
                version=source_release,
                timeout=self._UPDATE_COMPLETED_TIMEOUT)
        ]


    def _get_expected_event_for_post_reboot_check(self, source_release,
                                                  target_release):
        """
        Creates the expected event fired during post-reboot update check.

        @param source_release: The source build version.
        @param target_release: The target build version.

        """
        return [
            uee.UpdateEngineEvent(
                event_type=uee.EVENT_TYPE_REBOOTED_AFTER_UPDATE,
                event_result=uee.EVENT_RESULT_SUCCESS,
                version=target_release,
                previous_version=source_release,
                timeout = self._POST_REBOOT_TIMEOUT)
        ]


    def _verify_event_with_timeout(self, expected_event, actual_event):
        """
        Verify an expected event occurred before its timeout.

        @param expected_event: an expected event.
        @param actual_event: an actual event from the hostlog.

        @return None if event complies, an error string otherwise.

        """
        logging.info('Expecting %s within %s seconds', expected_event,
                     expected_event._timeout)
        if not actual_event:
            return ('No entry found for %s event.' % uee.get_event_type
                (expected_event._expected_attrs['event_type']))
        logging.info('Consumed new event: %s', actual_event)
        # If this is the first event, set it as the current time
        if self._current_timestamp is None:
            self._current_timestamp = datetime.strptime(
                actual_event['timestamp'], self._TIMESTAMP_FORMAT)

        # Get the time stamp for the current event and convert to datetime
        timestamp = actual_event['timestamp']
        event_timestamp = datetime.strptime(timestamp,
                                            self._TIMESTAMP_FORMAT)

        # If the event happened before the timeout
        difference = event_timestamp - self._current_timestamp
        if difference < timedelta(seconds=expected_event._timeout):
            logging.info('Event took %s seconds to fire during the '
                         'update', difference.seconds)
            self._current_timestamp = event_timestamp
            mismatched_attrs = expected_event.equals(actual_event)
            if mismatched_attrs is None:
                return None
            else:
                return self._error_incorrect_event(
                    expected_event, actual_event, mismatched_attrs)
        else:
            return self._timeout_error_message(expected_event,
                                               difference.seconds)


    def _error_incorrect_event(self, expected, actual, mismatched_attrs):
        """
        Error message for when an event is not what we expect.

        @param expected: The expected event that did not match the hostlog.
        @param actual: The actual event with the mismatched arg(s).
        @param mismatched_attrs: A list of mismatched attributes.

        """
        et = uee.get_event_type(expected._expected_attrs['event_type'])
        return ('Event %s had mismatched attributes: %s. We expected %s, but '
                'got %s.' % (et, mismatched_attrs, expected, actual))


    def _timeout_error_message(self, expected, time_taken):
        """
        Error message for when an event takes too long to fire.

        @param expected: The expected event that timed out.
        @param time_taken: How long it actually took.

        """
        et = uee.get_event_type(expected._expected_attrs['event_type'])
        return ('Event %s should take less than %ds. It took %ds.'
                % (et, expected._timeout, time_taken))


    def _stage_payload_by_uri(self, payload_uri, properties_file=True):
        """Stage a payload based on its GS URI.

        This infers the build's label, filename and GS archive from the
        provided GS URI.

        @param payload_uri: The full GS URI of the payload.
        @param properties_file: If true, it will stage the update payload
                                properties file too.

        @return URL of the staged payload (and properties file) on the server.

        @raise error.TestError if there's a problem with staging.

        """
        archive_url, _, filename = payload_uri.rpartition('/')
        build_name = urlparse.urlsplit(archive_url).path.strip('/')
        filenames = [filename]
        if properties_file:
            filenames.append(filename + '.json')
        try:
            self._autotest_devserver.stage_artifacts(image=build_name,
                                                     files=filenames,
                                                     archive_url=archive_url)
            return (self._autotest_devserver.get_staged_file_url(f, build_name)
                    for f in filenames)
        except dev_server.DevServerException as e:
            raise error.TestError('Failed to stage payload: %s' % e)


    def _get_devserver_for_test(self, test_conf):
        """Find a devserver to use.

        We use the payload URI as the hash for ImageServer.resolve. The chosen
        devserver needs to respect the location of the host if
        'prefer_local_devserver' is set to True or 'restricted_subnets' is set.

        @param test_conf: a dictionary of test settings.

        """
        autotest_devserver = dev_server.ImageServer.resolve(
            test_conf['target_payload_uri'], self._host.hostname)
        devserver_hostname = urlparse.urlparse(
            autotest_devserver.url()).hostname
        logging.info('Devserver chosen for this run: %s', devserver_hostname)
        return autotest_devserver


    def _get_payload_url(self, build=None, full_payload=True, is_dlc=False):
        """
        Gets the GStorage URL of the full or delta payload for this build, for
        either platform or DLC payloads.

        @param build: build string e.g eve-release/R85-13265.0.0.
        @param full_payload: True for full payload. False for delta.
        @param is_dlc: True to get the payload URL for dummy-dlc.

        @returns the payload URL.

        """
        if build is None:
            if self._job_repo_url is None:
                self._job_repo_url = self._get_job_repo_url()
            ds_url, build = tools.get_devserver_build_from_package_url(
                self._job_repo_url)
            self._autotest_devserver = dev_server.ImageServer(ds_url)

        gs = dev_server._get_image_storage_server()

        # Example payload names (AU):
        # chromeos_R85-13265.0.0_eve_full_dev.bin
        # chromeos_R85-13265.0.0_R85-13265.0.0_eve_delta_dev.bin
        # Example payload names (DLC):
        # dlc_dummy-dlc_package_R85-13265.0.0_eve_full_dev.bin
        # dlc_dummy-dlc_package_R85-13265.0.0_R85-13265.0.0_eve_delta_dev.bin
        if is_dlc:
            payload_prefix = 'dlc_*%s*_%s_*' % (build.rpartition('/')[2], '%s')
        else:
            payload_prefix = 'chromeos_%s*_%s_*' % (build.rpartition('/')[2],
                                                    '%s')

        regex = payload_prefix % ('full' if full_payload else 'delta')

        payload_url_regex = gs + build + '/' + regex
        logging.debug('Trying to find payloads at %s', payload_url_regex)
        payloads = utils.gs_ls(payload_url_regex)
        if not payloads:
            raise error.TestFail('Could not find payload for %s', build)
        logging.debug('Payloads found: %s', payloads)
        return payloads[0]


    @staticmethod
    def _get_stateful_uri(build_uri):
        """Returns a complete GS URI of a stateful update given a build path."""
        return '/'.join([build_uri.rstrip('/'), 'stateful.tgz'])


    def _get_job_repo_url(self, job_repo_url=None):
        """Gets the job_repo_url argument supplied to the test by the lab."""
        if job_repo_url is not None:
            return job_repo_url
        if self._hosts is not None:
            self._host = self._hosts[0]
        if self._host is None:
            raise error.TestFail('No host specified by AU test.')
        info = self._host.host_info_store.get()
        return info.attributes.get(self._host.job_repo_url_attribute, '')


    def _stage_payloads(self, payload_uri, archive_uri):
        """
        Stages payloads on the devserver.

        @param payload_uri: URI for a GS payload to stage.
        @param archive_uri: URI for GS folder containing payloads. This is used
                            to find the related stateful payload.

        @returns URI of staged payload, URI of staged stateful.

        """
        if not payload_uri:
            return None, None
        staged_uri, _ = self._stage_payload_by_uri(payload_uri)
        logging.info('Staged %s at %s.', payload_uri, staged_uri)

        # Figure out where to get the matching stateful payload.
        if archive_uri:
            stateful_uri = self._get_stateful_uri(archive_uri)
        else:
            stateful_uri = self._payload_to_stateful_uri(payload_uri)
        staged_stateful = self._stage_payload_by_uri(stateful_uri,
                                                     properties_file=False)
        logging.info('Staged stateful from %s at %s.', stateful_uri,
                     staged_stateful)
        return staged_uri, staged_stateful



    def _payload_to_stateful_uri(self, payload_uri):
        """Given a payload GS URI, returns the corresponding stateful URI."""
        build_uri = payload_uri.rpartition('/payloads/')[0]
        return self._get_stateful_uri(build_uri)


    def _copy_payload_to_public_bucket(self, payload_url):
        """
        Copy payload and make link public.

        @param payload_url: Payload URL on Google Storage.

        @returns The payload URL that is now publicly accessible.

        """
        payload_filename = payload_url.rpartition('/')[2]
        utils.run(['gsutil', 'cp', '%s*' % payload_url, self._CELLULAR_BUCKET])
        new_gs_url = self._CELLULAR_BUCKET + payload_filename
        utils.run(['gsutil', 'acl', 'ch', '-u', 'AllUsers:R',
                   '%s*' % new_gs_url])
        return new_gs_url.replace('gs://', 'https://storage.googleapis.com/')


    def _suspend_then_resume(self):
        """Suspends and resumes the host DUT."""
        try:
            self._host.suspend(suspend_time=30)
        except error.AutoservSuspendError:
            logging.exception('Suspend did not last the entire time.')


    def _run_client_test_and_check_result(self, test_name, **kwargs):
        """
        Kicks of a client autotest and checks that it didn't fail.

        @param test_name: client test name
        @param **kwargs: key-value arguments to pass to the test.

        """
        client_at = autotest.Autotest(self._host)
        client_at.run_test(test_name, **kwargs)
        client_at._check_client_test_result(self._host, test_name)


    # TODO(ahassani): Move this to chromite so it can be used by endtoend tests
    # too so we don't have to rely on request_log API on nebraska.
    def _extract_request_logs(self, update_engine_log, is_dlc=False):
        """
        Extracts request logs from an update_engine log.

        @param update_engine_log: The update_engine log as a string.
        @param is_dlc: True to return the request logs for the DLC updates
                       instead of the platform update.
        @returns a list object representing the platform (OS) request logs, or
                 a dictionary of lists representing DLC request logs,
                 keyed by DLC ID, if is_dlc is True.

        """
        # Looking for all request XML strings in the log.
        pattern = re.compile(r'<request.*?</request>', re.DOTALL)
        requests = pattern.findall(update_engine_log)

        # We are looking for patterns like this:
        # [0324/151230.562305:INFO:omaha_request_action.cc(501)] Request:
        timestamp_pattern = re.compile(r'\[([0-9]+)/([0-9]+).*?\] Request:')
        timestamps = [
            # Just use the current year since the logs don't have the year
            # value. Let's all hope tests don't start to fail on new year's
            # eve LOL.
            datetime(datetime.now().year,
                     int(ts[0][0:2]),  # Month
                     int(ts[0][2:4]),  # Day
                     int(ts[1][0:2]),  # Hours
                     int(ts[1][2:4]),  # Minutes
                     int(ts[1][4:6]))  # Seconds
            for ts in timestamp_pattern.findall(update_engine_log)
        ]

        if len(requests) != len(timestamps):
            raise error.TestFail('Failed to properly parse the update_engine '
                                 'log file.')

        result = []
        dlc_results = {}
        for timestamp, request in zip(timestamps, requests):

            root = ElementTree.fromstring(request)

            # There may be events for multiple apps if DLCs are installed.
            # See below (trimmed) example request including DLC:
            #
            # <request requestid=...>
            #   <os version="Indy" platform=...></os>
            #   <app appid="{DB5199C7-358B-4E1F-B4F6-AF6D2DD01A38}"
            #       version="13265.0.0" track=...>
            #     <event eventtype="13" eventresult="1"></event>
            #   </app>
            #   <app appid="{DB5199C7-358B-4E1F-B4F6-AF6D2DD01A38}_dummy-dlc"
            #       version="0.0.0.0" track=...>
            #     <event eventtype="13" eventresult="1"></event>
            #   </app>
            # </request>
            #
            # The first <app> section is for the platform update. The second
            # is for the DLC update.
            #
            # Example without DLC:
            # <request requestid=...>
            #   <os version="Indy" platform=...></os>
            #   <app appid="{DB5199C7-358B-4E1F-B4F6-AF6D2DD01A38}"
            #       version="13265.0.0" track=...>
            #     <event eventtype="13" eventresult="1"></event>
            #   </app>
            # </request>

            apps = root.findall('app')
            for app in apps:
                event = app.find('event')

                event_info = {
                    'version': app.attrib.get('version'),
                    'event_type': (int(event.attrib.get('eventtype'))
                                  if event is not None else None),
                    'event_result': (int(event.attrib.get('eventresult'))
                                    if event is not None else None),
                    'timestamp': timestamp.strftime(self._TIMESTAMP_FORMAT),
                }

                previous_version = (event.attrib.get('previousversion')
                                    if event is not None else None)
                if previous_version:
                    event_info['previous_version'] = previous_version

                # Check if the event is for the platform update or for a DLC
                # by checking the appid. For platform, the appid looks like:
                #     {DB5199C7-358B-4E1F-B4F6-AF6D2DD01A38}
                # For DLCs, it is the platform app ID + _ + the DLC ID:
                #     {DB5199C7-358B-4E1F-B4F6-AF6D2DD01A38}_dummy-dlc
                id_segments = app.attrib.get('appid').split('_')
                if len(id_segments) > 1:
                    dlc_id = id_segments[1]
                    if dlc_id in dlc_results:
                        dlc_results[dlc_id].append(event_info)
                    else:
                        dlc_results[dlc_id] = [event_info]
                else:
                    result.append(event_info)

        if is_dlc:
            logging.info('Extracted DLC request logs: %s', dlc_results)
            return dlc_results
        else:
            logging.info('Extracted platform (OS) request log: %s', result)
            return result


    def _create_hostlog_files(self):
        """Create the two hostlog files for the update.

        To ensure the update was successful we need to compare the update
        events against expected update events. There is a hostlog for the
        rootfs update and for the post reboot update check.

        """
        # Each time we reboot in the middle of an update we ping omaha again
        # for each update event. So parse the list backwards to get the final
        # events.
        rootfs_hostlog = os.path.join(self.resultsdir, 'hostlog_rootfs')
        with open(rootfs_hostlog, 'w') as fp:
            # There are four expected hostlog events during update.
            json.dump(self._extract_request_logs(
                self._get_update_engine_log(1))[-4:], fp)

        reboot_hostlog = os.path.join(self.resultsdir, 'hostlog_reboot')
        with open(reboot_hostlog, 'w') as fp:
            # There is one expected hostlog events after reboot.
            json.dump(self._extract_request_logs(
                self._get_update_engine_log(0))[:1], fp)

        return rootfs_hostlog, reboot_hostlog


    def _create_dlc_hostlog_files(self):
        """Create the rootfs and reboot hostlog files for DLC updates.

        Each DLC has its own set of update requests in the logs together with
        the platform update requests. To ensure the DLC update was successful
        we will compare the update events against the expected events, which
        are the same expected events as for the platform update. There is a
        hostlog for the rootfs update and the post-reboot update check for
        each DLC.

        @returns two dictionaries, one for the rootfs DLC update and one for
                 the post-reboot check. The keys are DLC IDs and the values
                 are the hostlog filenames.

        """
        dlc_rootfs_hostlogs = {}
        dlc_reboot_hostlogs = {}

        dlc_rootfs_request_logs = self._extract_request_logs(
            self._get_update_engine_log(1), is_dlc=True)

        for dlc_id in dlc_rootfs_request_logs:
            dlc_rootfs_hostlog = os.path.join(self.resultsdir,
                                              'hostlog_' + dlc_id)
            dlc_rootfs_hostlogs[dlc_id] = dlc_rootfs_hostlog
            with open(dlc_rootfs_hostlog, 'w') as fp:
                # Same number of events for DLC updates as for platform
                json.dump(dlc_rootfs_request_logs[dlc_id][-4:], fp)

        dlc_reboot_request_logs = self._extract_request_logs(
            self._get_update_engine_log(0), is_dlc=True)

        for dlc_id in dlc_reboot_request_logs:
            dlc_reboot_hostlog = os.path.join(self.resultsdir,
                                              'hostlog_' + dlc_id + '_reboot')
            dlc_reboot_hostlogs[dlc_id] = dlc_reboot_hostlog
            with open(dlc_reboot_hostlog, 'w') as fp:
                # Same number of events for DLC updates as for platform
                json.dump(dlc_reboot_request_logs[dlc_id][:1], fp)

        return dlc_rootfs_hostlogs, dlc_reboot_hostlogs


    def _set_active_p2p_host(self, host):
        """
        Choose which p2p host device to run commands on.

        For P2P tests with multiple DUTs we need to be able to choose which
        host within self._hosts we want to issue commands on.

        @param host: The host to run commands on.

        """
        self._set_util_functions(host.run, host.get_file)


    def _set_update_over_cellular_setting(self, update_over_cellular=True):
        """
        Toggles the update_over_cellular setting in update_engine.

        @param update_over_cellular: True to enable, False to disable.

        """
        answer = 'yes' if update_over_cellular else 'no'
        cmd = [self._UPDATE_ENGINE_CLIENT_CMD,
               '--update_over_cellular=%s' % answer]
        retry_util.RetryException(error.AutoservRunError, 2, self._run, cmd)


    def _copy_generated_nebraska_logs(self, logs_dir, identifier):
        """Copies nebraska logs from logs_dir into job results directory.

        The nebraska process on the device generates logs (with the names:
        devserver_hostlog_rootfs, devserver_hostlog_reboot, nebraska.log)
        and stores those logs in a /tmp directory. The update engine generates
        update_engine.log during the auto-update which is also stored in the
        same /tmp directory. This method copies these logfiles from the /tmp
        directory into the job results directory.

        @param logs_dir: Directory containing paths to the log files generated
                         by the nebraska process.
        @param identifier: A string that is appended to the logfile when it is
                           saved so that multiple files with the same name can
                           be differentiated.
        """
        partial_filename = '%s_%s_%s' % ('%s', self._host.hostname, identifier)
        src_files = [
            self._DEVSERVER_HOSTLOG_ROOTFS,
            self._DEVSERVER_HOSTLOG_REBOOT,
            self._NEBRASKA_LOG,
            os.path.basename(self._UPDATE_ENGINE_LOG),
        ]

        for src_fname in src_files:
            source = os.path.join(logs_dir, src_fname)
            dest = os.path.join(self.resultsdir, partial_filename % src_fname)
            logging.debug('Copying logs from %s to %s', source, dest)
            try:
                shutil.copyfile(source, dest)
            except Exception as e:
                logging.error('Could not copy logs from %s into %s due to '
                              'exception: %s', source, dest, e)

    @staticmethod
    def _get_update_parameters_from_uri(payload_uri):
        """Extract vars needed to update with a Google Storage payload URI.

        The two values we need are:
        (1) A build_name string e.g dev-channel/samus/9583.0.0
        (2) A filename of the exact payload file to use for the update. This
        payload needs to have already been staged on the devserver.

        @param payload_uri: Google Storage URI to extract values from

        """

        # gs://chromeos-releases/dev-channel/samus/9334.0.0/payloads/blah.bin
        # build_name = dev-channel/samus/9334.0.0
        # payload_file = payloads/blah.bin
        build_name = payload_uri[:payload_uri.index('payloads/')]
        build_name = urlparse.urlsplit(build_name).path.strip('/')
        payload_file = payload_uri[payload_uri.index('payloads/'):]

        logging.debug('Extracted build_name: %s, payload_file: %s from %s.',
                      build_name, payload_file, payload_uri)
        return build_name, payload_file


    def _restore_stateful(self):
        """
        Restore the stateful partition after a destructive test.

        The stateful payload needs to already have been staged (e.g as part of
        get_update_url_for_test()).

        """
        logging.info('Restoring stateful partition...')
        _, build = tools.get_devserver_build_from_package_url(
            self._job_repo_url)

         # Setup local dir.
        self._run(['mkdir', '-p', '-m', '1777', '/usr/local/tmp'])

        # Download and extract the stateful payload.
        update_url = self._autotest_devserver.get_update_url(build)
        statefuldev_url = update_url.replace('update', 'static')
        statefuldev_url += '/stateful.tgz'
        cmd = ['curl', '--silent', '--max-time', '300',
               statefuldev_url, '|', 'tar', '--ignore-command-error',
               '--overwrite','--directory', '/mnt/stateful_partition', '-xz']
        self._run(cmd)

        # Touch a file so changes are picked up after reboot.
        update_file = '/mnt/stateful_partition/.update_available'
        self._run(['echo', '-n', 'clobber', '>', update_file])
        self._host.reboot()
        logging.info('Stateful restored successfully.')


    def verify_update_events(self, source_release, hostlog_filename,
                             target_release=None):
        """Compares a hostlog file against a set of expected events.

        In this class we build a list of expected events (list of
        UpdateEngineEvent objects), and compare that against a "hostlog"
        returned from update_engine from the update. This hostlog is a json
        list of events fired during the update.

        @param source_release: The source build version.
        @param hostlog_filename: The path to a hotlog returned from nebraska.
        @param target_release: The target build version.

        """
        if target_release is not None:
            expected_events = self._get_expected_event_for_post_reboot_check(
                source_release, target_release)
        else:
            expected_events = self._get_expected_events_for_rootfs_update(
                source_release)
        logging.info('Checking update against hostlog file: %s',
                     hostlog_filename)
        try:
            with open(hostlog_filename, 'r') as fp:
                hostlog_events = json.load(fp)
        except Exception as e:
            raise error.TestFail('Error reading the hostlog file: %s' % e)

        for expected, actual in itertools.izip_longest(expected_events,
                                                       hostlog_events):
            err_msg = self._verify_event_with_timeout(expected, actual)
            if err_msg is not None:
                raise error.TestFail(('Hostlog verification failed: %s ' %
                                     err_msg))


    def get_update_url_for_test(self, job_repo_url=None, full_payload=True,
                                stateful=False):
        """
        Returns a devserver update URL for tests that cannot use a Nebraska
        instance on the DUT for updating.

        This expects the test to set self._host or self._hosts.

        @param job_repo_url: string url containing the current build.
        @param full_payload: bool whether we want a full payload.
        @param stateful: bool whether we want to stage stateful payload too.

        @returns a valid devserver update URL.

        """
        self._job_repo_url = self._get_job_repo_url(job_repo_url)
        if not self._job_repo_url:
            raise error.TestFail('There was no job_repo_url so we cannot get '
                                 'a payload to use.')
        ds_url, build = tools.get_devserver_build_from_package_url(
            self._job_repo_url)

        # The lab devserver assigned to this test.
        lab_devserver = dev_server.ImageServer(ds_url)

        # Stage payloads on the lab devserver.
        self._autotest_devserver = lab_devserver
        artifacts = ['full_payload' if full_payload else 'delta_payload']
        if stateful:
            artifacts.append('stateful')
        self._autotest_devserver.stage_artifacts(build, artifacts)

        # Use the same lab devserver to also handle the update.
        url = self._autotest_devserver.get_update_url(build)

        # Delta payloads get staged into the 'au_nton' directory of the
        # build itself. So we need to append this at the end of the update
        # URL to get the delta payload.
        if not full_payload:
            url += '/au_nton'
        logging.info('Update URL: %s', url)
        return url


    def get_update_url_from_fake_omaha(self,
                                       job_repo_url=None,
                                       full_payload=True,
                                       payload_id='ROOTFS',
                                       critical_update=True,
                                       exposed_via_proxy=True,
                                       return_noupdate_starting=0):
        """
        Starts a FakeOmaha instance with TLS and returns is update url.

        Some tests that require an omaha instance to survive a reboot will use
        the FakeOmaha TLS.

        @param job_repo_url: string url containing the current build.
        @param full_payload: bool whether we want a full payload.
        @param payload_id: ROOTFS or DLC
        @param critical_update: True if we want a critical update response.
        @param exposed_via_proxy: True to tell TLS we want the fakeomaha to be
                                  accessible after a reboot.
        @param return_noupdate_starting: int of how many valid update responses
                                         to return before returning noupdate
                                        forever.

        @returns an update url on the FakeOmaha instance for tests to use.

        """
        self._job_repo_url = self._get_job_repo_url(job_repo_url)
        if not self._job_repo_url:
            raise error.TestFail('There was no job_repo_url so we cannot get '
                                 'a payload to use.')
        gs = dev_server._get_image_storage_server()
        _, build = tools.get_devserver_build_from_package_url(
                self._job_repo_url)
        target_build = gs + build
        payload_type = 'FULL' if full_payload else 'DELTA'
        tlsconn = connection.TLSConnection()
        self.fake_omaha = fake_omaha.TLSFakeOmaha(tlsconn)
        fake_omaha_url = self.fake_omaha.start_omaha(
                self._host.hostname,
                target_build=target_build,
                payloads=[{
                        'payload_id': payload_id,
                        'payload_type': payload_type,
                }],
                exposed_via_proxy=True,
                critical_update=critical_update,
                return_noupdate_starting=return_noupdate_starting)
        logging.info('Fake Omaha update URL: %s', fake_omaha_url)
        return fake_omaha_url

    def get_payload_url_on_public_bucket(self, job_repo_url=None,
                                         full_payload=True, is_dlc=False):
        """
        Get the google storage url of the payload in a public bucket.

        We will be copying the payload to a public google storage bucket
        (similar location to updates via autest command).

        @param job_repo_url: string url containing the current build.
        @param full_payload: True for full, False for delta.
        @param is_dlc: True to get the payload URL for dummy-dlc.

        """
        self._job_repo_url = self._get_job_repo_url(job_repo_url)
        payload_url = self._get_payload_url(full_payload=full_payload,
                                            is_dlc=is_dlc)
        url = self._copy_payload_to_public_bucket(payload_url)
        logging.info('Public update URL: %s', url)
        return url


    def get_payload_for_nebraska(self, job_repo_url=None, full_payload=True,
                                 public_bucket=False, is_dlc=False):
        """
        Gets a platform or DLC payload URL to be used with a nebraska instance
        on the DUT.

        @param job_repo_url: string url containing the current build.
        @param full_payload: bool whether we want a full payload.
        @param public_bucket: True to return a payload on a public bucket.
        @param is_dlc: True to get the payload URL for dummy-dlc.

        @returns string URL of a payload staged on a lab devserver.

        """
        if public_bucket:
            return self.get_payload_url_on_public_bucket(
                job_repo_url, full_payload=full_payload, is_dlc=is_dlc)

        self._job_repo_url = self._get_job_repo_url(job_repo_url)
        payload = self._get_payload_url(full_payload=full_payload,
                                        is_dlc=is_dlc)
        payload_url, _ = self._stage_payload_by_uri(payload)
        logging.info('Payload URL for Nebraska: %s', payload_url)
        return payload_url


    def update_device(self, payload_uri, clobber_stateful=False, tag='source'):
        """
        Updates the device.

        Used by autoupdate_EndToEndTest and autoupdate_StatefulCompatibility,
        which use auto_updater to perform updates.

        @param payload_uri: The payload with which the device should be updated.
        @param clobber_stateful: Boolean that determines whether the stateful
                                 of the device should be force updated. By
                                 default, set to False
        @param tag: An identifier string added to each log filename.

        @raise error.TestFail if anything goes wrong with the update.

        """
        cros_preserved_path = ('/mnt/stateful_partition/unencrypted/'
                               'preserve/cros-update')
        build_name, payload_filename = self._get_update_parameters_from_uri(
            payload_uri)
        logging.info('Installing %s on the DUT', payload_uri)
        with remote_access.ChromiumOSDeviceHandler(
            self._host.hostname, base_dir=cros_preserved_path) as device:
            updater = auto_updater.ChromiumOSUpdater(
                device, build_name, build_name,
                yes=True,
                payload_filename=payload_filename,
                clobber_stateful=clobber_stateful,
                do_stateful_update=True,
                staging_server=self._autotest_devserver.url(),
                transfer_class=auto_updater_transfer.LabEndToEndPayloadTransfer)

            try:
                updater.RunUpdate()
            except Exception as e:
                logging.exception('ERROR: Failed to update device.')
                raise error.TestFail(str(e))
            finally:
                self._copy_generated_nebraska_logs(
                    updater.request_logs_dir, identifier=tag)
