# Copyright 2012 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from autotest_lib.client.common_lib import error
from autotest_lib.server.cros.faft.firmware_test import FirmwareTest


class firmware_ECSharedMem(FirmwareTest):
    """
    Servo based EC shared memory test.
    """
    version = 1

    def initialize(self, host, cmdline_args):
        super(firmware_ECSharedMem, self).initialize(host, cmdline_args)
        # Don't bother if there is no Chrome EC.
        if not self.check_ec_capability():
            raise error.TestNAError("Nothing needs to be tested on this device")
        # Only run in normal mode
        self.switcher.setup_mode('normal')
        self.ec.send_command("chan 0")

    def cleanup(self):
        try:
            self.ec.send_command("chan 0xffffffff")
        except Exception as e:
            logging.error("Caught exception: %s", str(e))
        super(firmware_ECSharedMem, self).cleanup()

    def shared_mem_checker(self):
        """Return whether there is still EC shared memory available.
        """
        match = self.ec.send_command_get_output("shmem",
                                                ["Size:\s*([0-9-]+)\r"])[0]
        shmem_size = int(match[1])
        logging.info("EC shared memory size is %d bytes", shmem_size)
        if shmem_size <= 0:
            return False
        elif shmem_size <= 256:
            logging.warning("EC shared memory is less than 256 bytes")
        return True

    def jump_checker(self):
        """Check for available EC shared memory after jumping to RW image, if
        necessary.

        Does not jump to RW if the EC is already in RW or RW_B.
        """
        ec_image = self.servo.get_ec_active_copy()
        # If we are not currently in RW, switch there first before testing.
        if ec_image != 'RW' and ec_image != 'RW_B':
            self.ec.send_command("sysjump RW")
            time.sleep(self.faft_config.ec_boot_to_console)
            ec_image = self.servo.get_ec_active_copy()
            if ec_image != 'RW':
                raise error.TestFail('Expected EC to be in RW, but was ' +
                                     ec_image)
        return self.shared_mem_checker()

    def run_once(self):
        """Execute the main body of the test.
        """
        logging.info("Check shared memory in normal operation and crash EC.")
        self.check_state(self.shared_mem_checker)
        self.switcher.mode_aware_reboot(
                'custom', lambda: self.ec.send_command('crash divzero'))

        logging.info("Check shared memory after crash and system jump.")
        self.check_state([self.shared_mem_checker, self.jump_checker])
        self.switcher.mode_aware_reboot('custom', self.sync_and_ec_reboot)
