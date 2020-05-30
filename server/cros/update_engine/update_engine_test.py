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
from autotest_lib.client.cros.update_engine import update_engine_event as uee
from autotest_lib.client.cros.update_engine import update_engine_util
from autotest_lib.server import autotest
from autotest_lib.server import test
from autotest_lib.server.cros.dynamic_suite import tools
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
        except dev_server.DevServerException, e:
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


    def _get_payload_url(self, build=None, full_payload=True):
        """
        Gets the GStorage URL of the full or delta payload for this build.

        @param build: build string e.g samus-release/R65-10225.0.0.
        @param full_payload: True for full payload. False for delta.

        @returns the payload URL.

        """
        if build is None:
            if self._job_repo_url is None:
                self._job_repo_url = self._get_job_repo_url()
            ds_url, build = tools.get_devserver_build_from_package_url(
                self._job_repo_url)
            self._autotest_devserver = dev_server.ImageServer(ds_url)

        gs = dev_server._get_image_storage_server()
        if full_payload:
            # Example: chromeos_R65-10225.0.0_samus_full_dev.bin
            regex = 'chromeos_%s*_full_*' % build.rpartition('/')[2]
        else:
            # Example: chromeos_R65-10225.0.0_R65-10225.0.0_samus_delta_dev.bin
            regex = 'chromeos_%s*_delta_*' % build.rpartition('/')[2]
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


    def _get_job_repo_url(self):
        """Gets the job_repo_url argument supplied to the test by the lab."""
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
        utils.run('gsutil cp %s* %s' % (payload_url, self._CELLULAR_BUCKET))
        new_gs_url = self._CELLULAR_BUCKET + payload_filename
        utils.run('gsutil acl ch -u AllUsers:R %s*' % new_gs_url)
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
    def _extract_request_logs(self, update_engine_log):
        """
        Extracts request logs from an update_engine log.

        @param update_engine_log: The update_engine log as a string.
        @returns a list object representing the request logs.

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
        for timestamp, request in zip(timestamps, requests):

            root = ElementTree.fromstring(request)
            app = root.find('app')
            event = app.find('event')

            result.append({
                'version': app.attrib.get('version'),
                'event_type': (int(event.attrib.get('eventtype'))
                              if event is not None else None),
                'event_result': (int(event.attrib.get('eventresult'))
                                if event is not None else None),
                'timestamp': timestamp.strftime(self._TIMESTAMP_FORMAT),
            })

            previous_version = (event.attrib.get('previousversion')
                                if event is not None else None)
            if previous_version:
                result[-1]['previous_version'] = previous_version

        logging.info('Extracted Request log: %s', result)
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


    def _set_active_p2p_host(self, host):
        """
        Choose which p2p host device to run commands on.

        For P2P tests with multiple DUTs we need to be able to choose which
        host within self._hosts we want to issue commands on.

        @param host: The host to run commands on.

        """
        self._create_update_engine_variables(host.run, host.get_file)


    def _change_cellular_setting_in_update_engine(self,
                                                  update_over_cellular=True):
        """
        Toggles the update_over_cellular setting in update_engine.

        @param update_over_cellular: True to enable, False to disable.

        """
        answer = 'yes' if update_over_cellular else 'no'
        cmd = 'update_engine_client --update_over_cellular=%s' % answer
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


    def get_update_url_for_test(self, job_repo_url, full_payload=True,
                                public=False, moblab=False):
        """
        Get the correct update URL for autoupdate tests to use.

        There are bunch of different update configurations that are required
        by AU tests. Some tests need a full payload, some need a delta payload.
        Some require the omaha response to be critical or be able to handle
        multiple DUTs etc. This function returns the correct update URL to the
        test based on the inputs parameters.

        This tests expects the test to set self._host or self._hosts.

        @param job_repo_url: string url containing the current build.
        @param full_payload: bool whether we want a full payload.
        @param public: url needs to be publicly accessible.
        @param moblab: True if we are running on moblab.

        @returns an update url string.

        """
        if job_repo_url is None:
            self._job_repo_url = self._get_job_repo_url()
        else:
            self._job_repo_url = job_repo_url
        if not self._job_repo_url:
            raise error.TestFail('There was no job_repo_url so we cannot get '
                                 'a payload to use.')
        ds_url, build = tools.get_devserver_build_from_package_url(
            self._job_repo_url)

        # The lab devserver assigned to this test.
        lab_devserver = dev_server.ImageServer(ds_url)

        if public:
            # Get the google storage url of the payload. We will be copying
            # the payload to a public google storage bucket (similar location
            # to updates via autest command).
            payload_url = self._get_payload_url(build,
                                                full_payload=full_payload)
            url = self._copy_payload_to_public_bucket(payload_url)
            logging.info('Public update URL: %s', url)
            return url

        # Stage payloads on the lab devserver.
        self._autotest_devserver = lab_devserver
        artifact = 'full_payload' if full_payload else 'delta_payload'
        self._autotest_devserver.stage_artifacts(build, [artifact])

        # Use the same lab devserver to also handle the update.
        url = self._autotest_devserver.get_update_url(build)

        # Delta payloads get staged into the 'au_nton' directory of the
        # build itself. So we need to append this at the end of the update
        # URL to get the delta payload.
        if not full_payload:
            url += '/au_nton'
        logging.info('Update URL: %s', url)
        return url

