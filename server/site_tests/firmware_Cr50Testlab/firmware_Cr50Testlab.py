# Copyright 2017 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.common_lib import error
from autotest_lib.server.cros.faft.cr50_test import Cr50Test
from autotest_lib.server.cros.servo import chrome_ti50


class firmware_Cr50Testlab(Cr50Test):
    """Verify cr50 testlab enable/disable."""
    version = 1
    ACCESS_DENIED = 'Access Denied'
    INVALID_PARAM = 'Parameter 1 invalid'
    BASIC_ERROR = 'Usage: ccd '

    def initialize(self, host, cmdline_args, full_args):
        """Initialize servo. Check that it can access cr50"""
        super(firmware_Cr50Testlab, self).initialize(host, cmdline_args,
                full_args)

        if not hasattr(self, 'gsc'):
            raise error.TestNAError('Test can only be run on devices with '
                                    'access to the GSC console')
        if self.servo.main_device_is_ccd():
            raise error.TestNAError('Use a flex cable instead of CCD cable.')
        if self.servo.main_device_uses_gsc_drv():
            raise error.TestNAError('Cannot run with c2d2 until cold_reset '
                                    'issue is resolved')

        if isinstance(self.gsc, chrome_ti50.ChromeTi50):
            self.BASIC_ERROR = 'Command \'ccd\' failed'
            self.INVALID_PARAM = 'Param2'

        # Get the current reset count, so we can check that there haven't been
        # any cr50 resets at any point during the test.
        self.start_reset_count = self.gsc.get_reset_count()

    def cleanup(self):
        """Reenable testlab mode."""
        try:
            self.fast_ccd_open(enable_testlab=True)
        finally:
            super(firmware_Cr50Testlab, self).cleanup()

    def try_testlab(self, mode, err=''):
        """Try to modify ccd testlab mode.

        Args:
            mode: The testlab command: 'on', 'off', or 'open'
            err: An empty string if the command should succeed or the error
                 message.

        Raises:
            TestFail if setting the ccd testlab mode doesn't match err
        """
        logging.info('Setting ccd testlab %s', mode)
        rv = self.gsc.send_command_get_output('ccd testlab %s' % mode,
                ['ccd.*>'])[0]
        logging.info(rv)
        if err not in rv or (not err and self.BASIC_ERROR in rv):
            raise error.TestFail('Unexpected result setting "%s": %r' % (mode,
                    rv))
        if err:
            return

        if mode == 'open':
            if mode != self.gsc.get_ccd_level():
                raise error.TestFail('ccd testlab open did not open the device')
        else:
            self.gsc.run_pp(self.gsc.PP_SHORT)
            if (mode == 'on') != self.gsc.testlab_is_on():
                raise error.TestFail('Testlab mode could not be turned %s' %
                        mode)
            logging.info('Set ccd testlab %s', mode)


    def check_reset_count(self):
        """Verify there haven't been any cr50 reboots"""
        reset_count = self.gsc.get_reset_count()
        if self.start_reset_count != reset_count:
            raise error.TestFail('Unexpected cr50 reboot')


    def reset_ccd(self):
        """Enable ccd testlab mode and set the privilege level to open"""
        logging.info('Resetting CCD state')
        self.fast_ccd_open(enable_testlab=True, reset_ccd=True)
        self.check_reset_count()


    def run_once(self):
        """Try to set testlab mode from different privilege levels."""
        # Bogus isn't a valid mode. Make sure it fails
        self.reset_ccd()
        self.try_testlab('bogus', err=self.INVALID_PARAM)

        # CCD can be opened without physical presence if testlab mode is enabled
        self.reset_ccd()
        self.try_testlab('on')
        self.try_testlab('open')
        self.check_reset_count()

        # You shouldn't be able to use testlab open if it is disabled
        self.reset_ccd()
        self.try_testlab('off')
        self.try_testlab('open', err=self.ACCESS_DENIED)
        self.check_reset_count()

        # You can't turn on testlab mode while ccd is locked
        self.reset_ccd()
        self.gsc.set_ccd_level('lock')
        self.try_testlab('on', err=self.ACCESS_DENIED)
        self.check_reset_count()

        # You can't turn off testlab mode while ccd is locked
        self.reset_ccd()
        self.gsc.set_ccd_level('lock')
        self.try_testlab('off', err=self.ACCESS_DENIED)
        self.check_reset_count()

        # If testlab mode is enabled, you can open the device without physical
        # presence by using 'ccd testlab open'.
        self.reset_ccd()
        self.try_testlab('on')
        self.gsc.set_ccd_level('lock')
        self.try_testlab('open')
        self.check_reset_count()

        # If testlab mode is disabled, testlab open should fail with access
        # denied.
        self.reset_ccd()
        self.try_testlab('off')
        self.gsc.set_ccd_level('lock')
        self.try_testlab('open', err=self.ACCESS_DENIED)
        self.check_reset_count()
        logging.info('ccd testlab is accessible')
