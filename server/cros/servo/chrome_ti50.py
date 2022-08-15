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
    NAME = 'ti50'

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

    # Ti50 interrupt numbers reported in taskinfo
    IRQ_DICT = {
        0 : 'UART0_GRP0',
        1 : 'UART1_GRP0',
        2 : 'UART2_GRP0',
        3 : 'UART3_GRP0',
        79 : 'I2CS0_GRP0',
        99 : 'RBOX0_GRP1',
        106 : 'TIMER0_TIMER0_MATCH1',
        108 : 'TIMER0_TIMER1_MATCH0',
        115 : 'USB0_USBINTR',
        257 : 'WAKEUP',
    }
    # USB should be disabled if ccd is disabled.
    CCD_IRQS = [ 115 ]
    # Each line relevant taskinfo output should be 13 characters long with only
    # digits or spaces. Use this information to make sure every taskinfo command
    # gets the full relevant output. There are 4 characters for the irq number
    # and 9 for the count.
    GET_TASKINFO = ['IRQ counts by type:\s+(([\d ]{13}[\r\n]+)+)>']
    # Ti50 has no periodic wake from regular sleep
    SLEEP_RATE = 0
    DS_RESETS_TIMER = False

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

    def set_ccd_level(self, level, password=''):
        if level == 'unlock':
            raise error.TestError(
                "Ti50 does not support privilege level unlock")
        super(ChromeTi50, self).set_ccd_level(level, password)

    def unlock_is_supported(self):
        return False

    def check_boot_mode(self, mode_exp='NORMAL'):
        """Query the Ti50 boot mode, and compare it against mode_exp.

        Args:
            mode_exp: expected boot mode. It should be either 'NORMAL'
                      or 'NO_BOOT'.
        Returns:
            True if the boot mode matches mode_exp.
            False, otherwise.
        Raises:
            TestError: Input parameter is not valid.
        """

        # Ti50 implements EFS 2.1, Cr50 implements EFS 2.0. This means
        # 'NORMAL' is renamed to 'VERIFIED'. Ti50 also changes the case.
        rv = self.send_command_retry_get_output('ec_comm',
                [r'boot_mode\s*:\s*(Verified|NoBoot)'], safe=True)
        if mode_exp == 'NORMAL':
            return rv[0][1] == 'Verified'
        elif mode_exp == 'NO_BOOT':
            return rv[0][1] == 'NoBoot'
        else:
            raise error.TestError('parameter, mode_exp is not valid: %s' %
                                  mode_exp)
