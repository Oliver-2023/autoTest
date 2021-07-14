# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import dev_server
from autotest_lib.client.common_lib.cros import kernel_utils
from autotest_lib.server.cros import provisioner
from autotest_lib.server.cros.update_engine import update_engine_test

class autoupdate_Basic(update_engine_test.UpdateEngineTest):
    """Performs a simple AU using Nebraska."""
    version = 1

    def cleanup(self):
        super(autoupdate_Basic, self).cleanup()
        if self._m2n:
            # Ensure rootfs and stateful are on the same version.
            self._restore_stateful()


    def run_once(self,
                 full_payload,
                 job_repo_url=None,
                 m2n=False,
                 running_at_desk=False):
        """
        Performs a N-to-N autoupdate with Nebraska.

        @param full_payload: True for full payload, False for delta
        @param job_repo_url: A url pointing to the devserver where the autotest
            package for this build should be staged.
        @m2n: M -> N update. This means we install the current stable version
              of this board before updating to ToT.
        @param running_at_desk: Indicates test is run locally from workstation.
                                Flag does not work with M2N tests.

        """
        self._m2n = m2n
        if self._m2n:
            if self._host.get_board().endswith("-kernelnext"):
                raise error.TestNAError("Skipping test on kernelnext board")

            # Provision latest stable build for the current build.
            build_name = self._get_latest_serving_stable_build()

            # Install the matching build with quick provision.
            autotest_devserver = dev_server.ImageServer.resolve(
                    build_name, self._host.hostname)
            update_url = autotest_devserver.get_update_url(build_name)
            logging.info('Installing source image with update url: %s',
                         update_url)
            provisioner.ChromiumOSProvisioner(
                    update_url, host=self._host,
                    is_release_bucket=True).run_provision()

        # Get a payload to use for the test.
        payload_url = self.get_payload_for_nebraska(
                job_repo_url,
                full_payload=full_payload,
                public_bucket=running_at_desk)

        # Record DUT state before the update.
        active, inactive = kernel_utils.get_kernel_state(self._host)

        # Perform the update.
        self._run_client_test_and_check_result('autoupdate_CannedOmahaUpdate',
                                               payload_url=payload_url)

        # Verify the update completed successfully.
        self._host.reboot()
        kernel_utils.verify_boot_expectations(inactive, host=self._host)
        rootfs_hostlog, _ = self._create_hostlog_files()
        self.verify_update_events(self._FORCED_UPDATE, rootfs_hostlog)
