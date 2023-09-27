# Copyright 2013 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# TODO(b/290823172) Remove this file when the test is no longer in any
# PVS plan

from autotest_lib.client.common_lib import error
from autotest_lib.server.cros.faft.firmware_test import FirmwareTest


class firmware_TPMVersionCheck(FirmwareTest):
    """
    crossystem check of reported TPM version.

    Replacement for test '1.1.9 TPM_version_in_Crossystem [tcm:6762253]'.
    """
    version = 1

    def initialize(self, host, cmdline_args, dev_mode=False):
        super(firmware_TPMVersionCheck, self).initialize(host, cmdline_args)
        self.switcher.setup_mode('dev' if dev_mode else 'normal',
                                 allow_gbb_force=True)
        self.setup_usbkey(usbkey=False)

    def run_once(self):
        """Runs a single iteration of the test."""
        if not self.checkers.crossystem_checker({
                    'tpm_fwver': '0x00010001',
                    'tpm_kernver': '0x00010001', }):
            raise error.TestFail('tpm version keys reported by '
                                 'crossystem are not as expected.')
