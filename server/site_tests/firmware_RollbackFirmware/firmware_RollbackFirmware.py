# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.server.cros import vboot_constants as vboot
from autotest_lib.server.cros.faft.firmware_test import FirmwareTest


class firmware_RollbackFirmware(FirmwareTest):
    """
    Servo based firmware rollback test.

    This test requires a USB disk plugged-in, which contains a Chrome OS test
    image (built by "build_image --test"). On runtime, this test rollbacks
    firmware A and results firmware B boot. It then rollbacks firmware B and
    results recovery boot.
    """
    version = 1

    def initialize(self, host, cmdline_args, dev_mode=False):
        super(firmware_RollbackFirmware, self).initialize(host, cmdline_args)
        self.backup_firmware()
        self.setup_dev_mode(dev_mode)
        self.setup_usbkey(usbkey=True, host=False)

    def cleanup(self):
        self.restore_firmware()
        super(firmware_RollbackFirmware, self).cleanup()

    def run_once(self, dev_mode=False):
        # Recovery reason RW_FW_ROLLBACK available after Alex/ZGB.
        if self.faft_client.system.get_platform_name() in (
                'Mario', 'Alex', 'ZGB'):
            recovery_reason = vboot.RECOVERY_REASON['RO_INVALID_RW']
        elif self.fw_vboot2:
            recovery_reason = vboot.RECOVERY_REASON['RO_INVALID_RW']
        else:
            recovery_reason = vboot.RECOVERY_REASON['RW_FW_ROLLBACK']

        logging.info("Rollback firmware A.")
        self.check_state((self.checkers.fw_tries_checker, 'A'))
        self.faft_client.bios.move_version_backward('a')
        self.reboot_warm()

        logging.info("Expected firmware B boot and rollback firmware B.")
        self.check_state((self.checkers.fw_tries_checker, ('B', False)))
        self.faft_client.bios.move_version_backward('b')
        self.reboot_warm(wait_for_dut_up=False)
        if not dev_mode:
            self.wait_fw_screen_and_plug_usb()
        self.wait_for_client(install_deps=True)

        logging.info("Expected recovery boot and restores firmware A and B.")
        self.check_state((self.checkers.crossystem_checker, {
                           'mainfw_type': 'recovery',
                           'recovery_reason': recovery_reason,
                           }))
        self.faft_client.bios.move_version_forward(('a', 'b'))
        self.reboot_warm()

        expected_slot = 'B' if self.fw_vboot2 else 'A'
        logging.info("Expected firmware " + expected_slot + " boot, done.")
        self.check_state((self.checkers.fw_tries_checker, expected_slot))
