# Lint as: python2, python3
# Copyright 2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from autotest_lib.server.cros.servo import chrome_cr50
from autotest_lib.client.common_lib import error


class ChromeTi50(chrome_cr50.ChromeCr50):
    """Manages control of a Chrome Ti50.

    We control the Chrome Ti50 via the console of a Servo board. Chrome Ti50
    provides many interfaces to set and get its behavior via console commands.
    This class is to abstract these interfaces.
    """

    WAKE_RESPONSE = ['(>|ti50_common)']
    START_STR = ['ti50_common']

    # List of all ti50 ccd capabilities. Same order of 'ccd' output.
    # This is not the same as cr50 list.
    CAP_NAMES = [
            'UartGscRxAPTx', 'UartGscTxAPRx', 'UartGscRxECTx', 'UartGscTxECRx',
            'UartGscRxFpmcuTx', 'UartGscTxFpmcuRx', 'FlashAP', 'FlashEC',
            'OverrideWP', 'RebootECAP', 'GscFullConsole', 'UnlockNoReboot',
            'UnlockNoShortPP', 'OpenNoTPMWipe', 'OpenNoLongPP',
            'BatteryBypassPP', 'I2C', 'FlashRead', 'OpenNoDevMode',
            'OpenFromUSB', 'OverrideBatt'
    ]

    def __init__(self, servo, faft_config):
        """Initializes a ChromeCr50 object.

        @param servo: A servo object.
        @param faft_config: A faft config object.
        """
        super(ChromeTi50, self).__init__(servo, 'cr50_uart')
        self.faft_config = faft_config
        # Update CCD_FORMAT to use ti50 version of CAP_NAMES.
        self.CCD_FORMAT['Capabilities'] = \
            '(Capabilities:.*(?P<Capabilities>%s))' % \
            (self.CAP_FORMAT.join(self.CAP_NAMES) + self.CAP_FORMAT)

    # Return None for now, until Ti50 version output is fixed to include
    # board_id info (b/215776772).
    def get_active_board_id_str(self):
        return None

    def set_ccd_level(self, level, password=''):
        if level == 'unlock':
            raise error.TestError(
                "Ti50 does not support privilege level unlock")
        super(ChromeTi50, self).set_ccd_level(level, password)

    def unlock_is_supported(self):
        return False
