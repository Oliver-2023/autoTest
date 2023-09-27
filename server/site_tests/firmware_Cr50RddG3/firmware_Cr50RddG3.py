# Copyright 2019 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from autotest_lib.client.common_lib import error
from autotest_lib.server.cros.faft.cr50_test import Cr50Test


class firmware_Cr50RddG3(Cr50Test):
    """Verify Rdd connect and disconnect in G3."""
    version = 1

    WAIT_FOR_STATE = 20
    # Cr50 debounces disconnects. We need to wait before checking Rdd state
    RDD_DEBOUNCE = 3

    def initialize(self, host, cmdline_args, full_args):
        """Initialize the test"""
        if not host.servo.get_ccd_servo_device():
            raise error.TestNAError('Need ccd to run test')
        super(firmware_Cr50RddG3, self).initialize(host, cmdline_args,
                                                   full_args)

    def rdd_is_connected(self):
        """Return True if Cr50 detects Rdd."""
        time.sleep(2)
        if (
                self.servo.main_device_is_ccd()
                and not self.ccd_programmer_connected_to_servo_host(False)):
            return False
        return self.gsc.get_ccdstate()['Rdd'] == 'connected'

    def check_capabilities(self, capabilities):
        """Returns the matching capability or None."""
        if not capabilities:
            return None
        for capability in capabilities:
            if self.check_cr50_capability([capability]):
                return capability
        return None


    def check_rdd_status(self, dts_mode, err_desc, capabilities=None):
        """Check the rdd state.

        @param dts_mode: 'on' if Rdd should be connected. 'off' if it should be
                         disconnected.
        @param err_desc: Description of the rdd error.
        @param capabilities: ignore err_desc if any of the capabilities from
                             this list are found in the faft board config.
        @param raises TestFail if rdd state doesn't match the expected rdd state
                      or if it does and the board has the capability set.
        """
        time.sleep(self.RDD_DEBOUNCE)
        err_msg = None
        rdd_enabled = self.rdd_is_connected()
        logging.info('dts: %r rdd: %r', dts_mode,
                     'connected' if rdd_enabled else 'disconnected')
        board_cap = self.check_capabilities(capabilities)
        if rdd_enabled != (dts_mode == 'on'):
            if board_cap:
                logging.info('Board has %r. %r still applies to board.',
                             board_cap, err_desc)
            else:
                err_msg = err_desc
        elif board_cap:
            # Log a warning if the board has a Rdd issue, but it didn't show up
            # during this test run.
            logging.warning(
                    'Irregular Cap behavior: Board has %r, but %r did '
                    'not occur.', board_cap, err_desc)
            err_msg = None
        if err_msg:
            logging.warning(err_msg)
            self.rdd_failures.append(err_msg)


    def run_once(self):
        """Verify Rdd in G3."""
        self.rdd_failures = []
        if not hasattr(self, 'ec'):
            raise error.TestNAError('Board does not have an EC.')
        if not self.servo.dts_mode_is_valid():
            raise error.TestNAError('Run with type-c servo v4.')

        # Disable rddkeepalive.
        self.gsc.send_command('ccd testlab open')
        self.gsc.send_command('rddkeepalive disable')

        self.servo.set_dts_mode('on')
        self.check_rdd_status('on', 'Cr50 did not detect Rdd with dts mode on')

        self.servo.set_dts_mode('off')
        self.check_rdd_status('off', 'Cr50 did not detect Rdd disconnect in S0')

        logging.info('Checking Rdd is disconnected with the EC in G3')
        self.faft_client.system.run_shell_command('poweroff')
        time.sleep(self.WAIT_FOR_STATE)
        self.check_rdd_status('off', 'Rdd connected after poweroff',
                              ['rdd_leakage', 'ec_hibernate_breaks_rdd'])

        # Can't check hibernate if the board doesn't support it or if it powers
        # off the GSC.
        if (self.faft_config.hibernate and not self.faft_config.gsc_off_in_ulp
                    and not self.servo.main_device_is_ccd()):
            logging.info(
                    'Checking Rdd is disconnected with the EC in hibernate')
            self.ec.send_command('hibernate')
            time.sleep(self.WAIT_FOR_STATE)
            self.check_rdd_status('off', 'Rdd connected after EC hibernate',
                                  ['rdd_leakage', 'ec_hibernate_breaks_rdd'])

        logging.info('Checking Rdd can be connected in G3.')
        self.servo.set_dts_mode('on')
        self.check_rdd_status('on', 'Cr50 did not detect Rdd connect in G3')

        # Turn the DUT on, then reenter G3 to make sure the system handles Rdd
        # while entering G3 ok.
        self._try_to_bring_dut_up()
        self.check_rdd_status('on', 'Rdd disconnected entering S0')

        logging.info('Checking Rdd is connected with the EC in G3')
        self.faft_client.system.run_shell_command('poweroff')
        time.sleep(self.WAIT_FOR_STATE)
        self.check_rdd_status('on', 'Rdd disconnected after poweroff',
                              ['rdd_off_in_g3', 'ec_hibernate_breaks_rdd'])

        # Can't check hibernate if the board doesn't support it or if it powers
        # off the GSC.
        if (self.faft_config.hibernate and not self.faft_config.gsc_off_in_ulp
                    and not self.servo.main_device_is_ccd()):
            logging.info('Checking Rdd is connected with the EC in hibernate.')
            self.ec.send_command('hibernate')
            time.sleep(self.WAIT_FOR_STATE)
            self.check_rdd_status('on', 'Rdd disconnected after EC hibernate',
                                  ['rdd_off_in_g3', 'ec_hibernate_breaks_rdd'])

        logging.info('Checking Rdd can be disconnected in G3.')
        self.servo.set_dts_mode('off')
        self.check_rdd_status('off',
                              'Cr50 did not detect Rdd disconnect in G3',
                              ['rdd_leakage'])
        self.servo.set_dts_mode('on')
        self._try_to_bring_dut_up()
        if self.rdd_failures:
            raise error.TestFail('Found Rdd issues: %s' % (self.rdd_failures))
