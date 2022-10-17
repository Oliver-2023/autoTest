# Lint as: python3
# Copyright 2022 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import kernel_utils
from autotest_lib.server.cros.minios import minios_test


class autoupdate_MiniOS(minios_test.MiniOsTest):
    """Tests MiniOS update. """

    version = 1

    _EXCLUSION_PREFS_DIR = "exclusion"
    _MINIOS_PREFS_DIR = "minios"

    def initialize(self, host=None, wifi_configs=None, running_at_desk=None):
        """
        Clear test related prefs on the DUT before starting the test.

        @param host: The DUT we will be running on.
        @param wifi_configs: List containing access point configuration dict and
            wifi client configuration dict.
        @param running_at_desk: indicates test is run locally from a
            workstation.

        """
        super(autoupdate_MiniOS, self).initialize(
            host=host, wifi_configs=wifi_configs,
            running_at_desk=running_at_desk,
            skip_provisioning='true')
        self._remove_minios_update_prefs()

    def cleanup(self):
        super(autoupdate_MiniOS, self).cleanup()
        self._save_extra_update_engine_logs(number_of_logs=2)
        self._remove_minios_update_prefs()
        # Set active miniOS partition back to the original one.
        try:
            kernel_utils.set_minios_priority(host=self._host,
                                             partition=self._active_minios)
        except AttributeError:
            logging.error("Skip restoring minios priority as the active minios "
                          "partition is not set.")

    def _remove_minios_update_prefs(self):
        for pref in ((self._EXCLUSION_PREFS_DIR, True),
                     (self._MINIOS_PREFS_DIR, True)):
            self._remove_update_engine_pref(pref=pref[0], is_dir=pref[1])

    def _setup_minios_update(self,
                             has_update,
                             with_exclusion=False,
                             build=None):
        # Get payload URL for the MiniOS update.
        # We'll always need a full payload for MiniOS update.
        payload_url = self.get_payload_for_nebraska(
                build=build,
                full_payload=True,
                payload_type=self._PAYLOAD_TYPE.MINIOS,
                public_bucket=self._running_at_desk)
        self._payload_urls.append(payload_url)

        # Test that MiniOS payload can be excluded by creating a pref file.
        # This simulates that the update engine tries to exclude MiniOS payload
        # after getting certain types of MiniOS update failure.
        if with_exclusion:
            self._create_update_engine_pref(
                    pref_name=self._get_exclusion_name(payload_url),
                    sub_dir=self._EXCLUSION_PREFS_DIR)

        # MiniOS booting to be verified.
        if has_update:
            self._verifications.append(self._boot_minios)

    def _setup_cros_update(self, has_update, build=None):
        if has_update:
            # Get payload URL for the platform (OS) update.
            self._payload_urls.append(
                    self.get_payload_for_nebraska(
                            build=build,
                            full_payload=self._full_payload,
                            public_bucket=self._running_at_desk))

        # Platform (OS) update to be verified.
        self._verifications.append(lambda: self._verify_cros_update(
                updated=has_update))

    def _setup_dlc_update(self, build=None):
        # Payload URLs for sample-dlc, a test DLC package.
        # We'll always need a full payload for DLC installation,
        # and optionally a delta payload if required by the test.
        self._payload_urls.append(
                self.get_payload_for_nebraska(
                        build=build,
                        full_payload=True,
                        payload_type=self._PAYLOAD_TYPE.DLC,
                        public_bucket=self._running_at_desk))
        if not self._full_payload:
            self._payload_urls.append(
                    self.get_payload_for_nebraska(
                            build=build,
                            full_payload=False,
                            payload_type=self._PAYLOAD_TYPE.DLC,
                            public_bucket=self._running_at_desk))

        # DLC update to be verified.
        self._verifications.append(self._verify_dlc_update)

    def _verify_cros_update(self, updated):
        if updated:
            # Verify the platform (OS) update completed successfully.
            kernel_utils.verify_boot_expectations(self._inactive_cros,
                                                  host=self._host)
            rootfs_hostlog, _ = self._create_hostlog_files()
            self.verify_update_events(self._FORCED_UPDATE, rootfs_hostlog)
        else:
            # Verify the Platform (OS) boot expectation unchanged.
            kernel_utils.verify_boot_expectations(self._active_cros,
                                                  host=self._host)

    def _verify_dlc_update(self):
        # Verify the DLC update completed successfully.
        dlc_rootfs_hostlog, _ = self._create_dlc_hostlog_files()
        logging.info('Checking DLC update events')
        self.verify_update_events(
                self._FORCED_UPDATE,
                dlc_rootfs_hostlog[self._dlc_util._SAMPLE_DLC_ID])
        # Verify the DLC was successfully installed.
        self._dlc_util.remove_preloaded(self._dlc_util._SAMPLE_DLC_ID)
        self._dlc_util.install(self._dlc_util._SAMPLE_DLC_ID,
                               omaha_url='fake_url')
        if not self._dlc_util.is_installed(self._dlc_util._SAMPLE_DLC_ID):
            raise error.TestFail('Test DLC was not installed.')

    def run_once(self,
                 full_payload=True,
                 with_os=False,
                 with_dlc=False,
                 with_exclusion=False,
                 running_at_desk=False,
                 build=None,
                 m2n=False):
        """
        Tests that we can successfully update MiniOS along with the OS.

        @param full_payload: True for full OS and DLC payloads. False for delta.
        @param with_os: True for MiniOS update along with Platform (OS)
                             update. False for MiniOS only update.
        @param with_dlc: True for MiniOS update with Platform (OS) and DLC.
                             False for turning off DLC update.
        @param with_exclusion: True for excluding MiniOS payload.
        @param running_at_desk: Indicates test is run locally from a
                                workstation.
        @param build: An optional parameter to specify the target build for the
                      update when running locally. If no build is supplied, the
                      current version on the DUT will be used.
        @m2n: M -> N update. This means we install the current stable version
              of this board before updating to ToT.

        """
        self._full_payload = full_payload
        self._running_at_desk = running_at_desk

        if not with_os and with_dlc:
            logging.info("DLC only updates with the platform (OS), "
                         "automatically set with_os to True.")
            with_os = True

        if m2n:
            skip_board_suffixes = ['-kernelnext', '-manatee']
            self.provision_dut(public_bucket=running_at_desk,
                               skip_board_suffixes=skip_board_suffixes,
                               with_minios=True)

        # Record DUT state before the update.
        (self._active_cros,
         self._inactive_cros) = kernel_utils.get_kernel_state(self._host)
        (self._active_minios,
         self._inactive_minios) = kernel_utils.get_minios_priority(self._host)

        minios_update = with_os and not with_exclusion
        # MiniOS update to be verified.
        self._verifications = [
                lambda: kernel_utils.verify_minios_priority_after_update(
                        self._host,
                        expected=self._inactive_minios if minios_update
                                                       else self._active_minios)
        ]

        # Get payload URLs and setup tests.
        self._payload_urls = []
        self._setup_cros_update(has_update=with_os, build=build)
        if with_dlc:
            self._setup_dlc_update(build=build)
        self._setup_minios_update(has_update=minios_update,
                                  with_exclusion=with_exclusion,
                                  build=build)

        # Update MiniOS.
        if with_dlc:
            self._run_client_test_and_check_result(
                    'autoupdate_InstallAndUpdateDLC',
                    payload_urls=self._payload_urls,
                    allow_failure=not with_os)
        else:
            self._run_client_test_and_check_result(
                    'autoupdate_CannedOmahaUpdate',
                    payload_url=self._payload_urls,
                    allow_failure=not with_os)

        if with_os:
            self._host.reboot()

        # Verify updates.
        for verify in self._verifications:
            verify()
