# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from autotest_lib.client.common_lib import error
from autotest_lib.server.cros.faft.firmware_test import FirmwareTest
from autotest_lib.server.cros.servo import servo


class firmware_ECCharging(FirmwareTest):
    """
    Servo based EC charging control test.
    """
    version = 1

    # Flags set by battery
    BATT_FLAG_WANT_CHARGE = 0x1
    STATUS_FULLY_CHARGED = 0x20

    # Threshold of trickle charging current in mA
    TRICKLE_CHARGE_THRESHOLD = 100

    # We wait for up to 30 minutes for the battery to allow charging.
    DISCHARGE_TIMEOUT = 60 * 30

    # The period to check battery state while discharging.
    CHECK_BATT_STATE_WAIT = 60

    # The delay to wait for the AC state to update.
    AC_STATE_UPDATE_DELAY = 3

    # Wait a few seconds after discharging for voltage to stabilize
    BEGIN_CHARGING_TIMEOUT = 60

    # Sleep for a second between retries when waiting for voltage to stabilize
    BEGIN_CHARGING_RETRY_TIME = 1

    # After the battery reports it is not full, keep discharging for this long.
    # This should be >= BEGIN_CHARGING_TIMEOUT
    EXTRA_DISCHARGE_TIME = BEGIN_CHARGING_TIMEOUT + 30

    # The dict to cache the battery information
    BATTERY_INFO = {}

    def initialize(self, host, cmdline_args):
        super(firmware_ECCharging, self).initialize(host, cmdline_args)
        # Don't bother if there is no Chrome EC.
        if not self.check_ec_capability():
            raise error.TestNAError(
                    "Nothing needs to be tested on this device")
        # Only run in normal mode
        self.switcher.setup_mode('normal')
        self.ec.send_command("chan 0")

    def cleanup(self):
        try:
            self.ec.send_command("chan 0xffffffff")
        except Exception as e:
            logging.error("Caught exception: %s", str(e))
        super(firmware_ECCharging, self).cleanup()

    def _update_battery_info(self):
        """Get the battery info we care for this test."""
        # The battery parameters we care for this test. The order must match
        # the output of EC battery command.
        battery_params = [
                'V', 'V-desired', 'I', 'I-desired', 'Charging', 'Remaining'
        ]
        regex_str_list = []

        for p in battery_params:
            if p == 'Remaining':
                regex_str_list.append(p + ':\s+(\d+)\s+')
            elif p == 'Charging':
                regex_str_list.append(p + r':\s+(Not Allowed|Allowed)\s+')
            else:
                regex_str_list.append(p +
                                      r':\s+0x[0-9a-f]*\s+=\s+([0-9-]+)\s+')

        # For unknown reasons, servod doesn't always capture the ec
        # command output. It doesn't happen often, but retry if it does.
        retries = 3
        while retries > 0:
            retries -= 1
            try:
                battery_regex_match = self.ec.send_command_get_output(
                        'battery', regex_str_list)
                break
            except (servo.UnresponsiveConsoleError,
                    servo.ResponsiveConsoleError) as e:
                if retries <= 0:
                    raise
                logging.warning('Failed to get battery status. %s', e)
        else:
            battery_regex_match = self.ec.send_command_get_output(
                    'battery', regex_str_list)

        for i in range(len(battery_params)):
            if battery_params[i] == 'Charging':
                self.BATTERY_INFO[
                        battery_params[i]] = battery_regex_match[i][1]
            else:
                self.BATTERY_INFO[battery_params[i]] = int(
                        battery_regex_match[i][1])
        logging.debug('Battery info: %s', self.BATTERY_INFO)

    def _get_battery_desired_voltage(self):
        """Get battery desired voltage value."""
        if not self.BATTERY_INFO:
            self._update_battery_info()
        logging.info('Battery desired voltage = %d mV',
                     self.BATTERY_INFO['V-desired'])
        return self.BATTERY_INFO['V-desired']

    def _get_battery_desired_current(self):
        """Get battery desired current value."""
        if not self.BATTERY_INFO:
            self._update_battery_info()
        logging.info('Battery desired current = %d mA',
                     self.BATTERY_INFO['I-desired'])
        return self.BATTERY_INFO['I-desired']

    def _get_battery_actual_voltage(self):
        """Get the actual voltage from charger to battery."""
        if not self.BATTERY_INFO:
            self._update_battery_info()
        logging.info('Battery actual voltage = %d mV', self.BATTERY_INFO['V'])
        return self.BATTERY_INFO['V']

    def _get_battery_actual_current(self):
        """Get the actual current from charger to battery."""
        if not self.BATTERY_INFO:
            self._update_battery_info()
        logging.info('Battery actual current = %d mA', self.BATTERY_INFO['I'])
        return self.BATTERY_INFO['I']

    def _get_battery_remaining(self):
        """Get battery charge remaining in mAh."""
        if not self.BATTERY_INFO:
            self._update_battery_info()
        logging.info("Battery charge remaining = %d mAh",
                     self.BATTERY_INFO['Remaining'])
        return self.BATTERY_INFO['Remaining']

    def _get_battery_charging_allowed(self):
        """Get the battery charging state.

        Returns True if charging is allowed.
        """
        if not self.BATTERY_INFO:
            self._update_battery_info()
        logging.info("Battery charging = %s", self.BATTERY_INFO['Charging'])
        if self.BATTERY_INFO['Charging'] == 'Allowed':
            return True
        return False

    def _get_charger_target_voltage(self):
        """Get target charging voltage set in charger."""
        voltage = int(
                self.ec.send_command_get_output("charger",
                                                ["V_batt:\s+(\d+)\s"])[0][1])
        logging.info("Charger target voltage = %d mV", voltage)
        return voltage

    def _get_charger_target_current(self):
        """Get target charging current set in charger."""
        current = int(
                self.ec.send_command_get_output("charger",
                                                ["I_batt:\s+(\d+)\s"])[0][1])
        logging.info("Charger target current = %d mA", current)
        return current

    def _get_trickle_charging(self):
        """Check if we are trickle charging battery."""
        return (self._get_battery_desired_current() <
                self.TRICKLE_CHARGE_THRESHOLD)

    def _check_target_value(self):
        """Check charger target values are correct.

        Raise:
          error.TestFail: Raised when check fails.
        """
        if (self._get_charger_target_voltage() >=
                1.05 * self._get_battery_desired_voltage()):
            raise error.TestFail(
                    "Charger target voltage is too high. %d/%d=%f" %
                    (self._get_charger_target_voltage(),
                     self._get_battery_desired_voltage(),
                     float(self._get_charger_target_voltage()) /
                     self._get_battery_desired_voltage()))
        if (self._get_charger_target_current() >=
                1.05 * self._get_battery_desired_current()):
            raise error.TestFail(
                    "Charger target current is too high. %d/%d=%f" %
                    (self._get_charger_target_current(),
                     self._get_battery_desired_current(),
                     float(self._get_charger_target_current()) /
                     self._get_battery_desired_current()))

    def _check_actual_value(self):
        """Check actual voltage/current values are correct.

        Raise:
          error.TestFail: Raised when check fails.
        """
        if (self._get_battery_actual_voltage() >=
                1.05 * self._get_charger_target_voltage()):
            raise error.TestFail(
                    "Battery actual voltage is too high. %d/%d=%f" %
                    (self._get_battery_actual_voltage(),
                     self._get_charger_target_voltage(),
                     float(self._get_battery_actual_voltage()) /
                     self._get_charger_target_voltage()))
        if (self._get_battery_actual_current() >=
                1.05 * self._get_charger_target_current()):
            raise error.TestFail(
                    "Battery actual current is too high. %d/%d=%f" %
                    (self._get_battery_actual_current(),
                     self._get_charger_target_current(),
                     float(self._get_battery_actual_current()) /
                     self._get_charger_target_current()))

    def _check_if_discharge_on_ac(self):
        """Check if DUT is performing discharge on AC"""
        match = self.ec.send_command_get_output("battery", [
                r"Status:\s*(0x[0-9a-f]+)\s", r"Param flags:\s*([0-9a-f]+)\s"
        ])
        status = int(match[0][1], 16)
        params = int(match[1][1], 16)

        if (not (params & self.BATT_FLAG_WANT_CHARGE) and
                (status & self.STATUS_FULLY_CHARGED)):
            return True

        return False

    def _check_battery_discharging(self):
        """Check if AC is attached and if charge control is normal."""
        retries = 3
        while retries > 0:
            retries -= 1
            try:
                output = self.ec.send_command_get_output(
                        "chgstate",
                        [r"ac\s*=\s*(\d)\s*", r"chg_ctl_mode\s*=\s*(\d)\s*"])
                break
            except (servo.UnresponsiveConsoleError,
                    servo.ResponsiveConsoleError) as e:
                if retries <= 0:
                    raise
                logging.warning('Failed to get chgstate. %s', e)
        ac_state = int(output[0][1])
        chg_ctl_mode = int(output[1][1])
        if ac_state == 0:
            return True
        if chg_ctl_mode == 2:  # CHARGE_CONTROL_DISCHARGE
            return True
        return False

    def _set_battery_discharge(self):
        """Instruct the EC to drain the battery."""
        # Ask EC to drain the battery
        self.ec.send_command("chgstate discharge on")
        time.sleep(self.AC_STATE_UPDATE_DELAY)

        # Verify discharging. Either AC off or charge control discharge is good.
        if not self._check_battery_discharging():
            raise error.TestFail("Battery is not discharging.")

    def _set_battery_normal(self):
        """Instruct the EC to charge the battery as normal."""
        self.ec.send_command("chgstate discharge off")
        time.sleep(self.AC_STATE_UPDATE_DELAY)

        # Verify AC is on and charge control is normal.
        if self._check_battery_discharging():
            raise error.TestFail("Fail to plug AC and enable charging.")
        self._update_battery_info()

    def _consume_battery(self, deadline):
        """Perform battery intensive operation to make the battery discharge faster."""
        # Switch to servo drain after b/140965614.
        stress_time = deadline - time.time()
        if stress_time > self.CHECK_BATT_STATE_WAIT:
            stress_time = self.CHECK_BATT_STATE_WAIT
        self._client.run("stressapptest -s %d " % stress_time,
                         ignore_status=True)

    def _discharge_below_100(self):
        """Remove AC power until the battery is not full."""
        self._set_battery_discharge()
        logging.info(
                "Keep discharging until the battery reports charging allowed.")

        try:
            # Wait until DISCHARGE_TIMEOUT or charging allowed
            deadline = time.time() + self.DISCHARGE_TIMEOUT
            while time.time() < deadline:
                self._update_battery_info()
                if self._get_battery_charging_allowed():
                    break
                logging.info("Wait for the battery to discharge (%d mAh).",
                             self._get_battery_remaining())
                self._consume_battery(deadline)
            else:
                raise error.TestFail(
                        "The battery does not report charging allowed "
                        "before timeout is reached.")

            # Wait another EXTRA_DISCHARGE_TIME just to be sure
            deadline = time.time() + self.EXTRA_DISCHARGE_TIME
            while time.time() < deadline:
                self._update_battery_info()
                logging.info(
                        "Wait for the battery to discharge even more (%d mAh).",
                        self._get_battery_remaining())
                self._consume_battery(deadline)
        finally:
            self._set_battery_normal()

        # For many devices, it takes some time after discharging for the
        # battery to actually start charging.
        deadline = time.time() + self.BEGIN_CHARGING_TIMEOUT
        while time.time() < deadline:
            self._update_battery_info()
            if self._get_battery_actual_current() >= 0:
                break
            logging.info(
                    'Battery actual current (%d) too low, wait a bit. (%d mAh)',
                    self._get_battery_actual_current(),
                    self._get_battery_remaining())
            time.sleep(self.BEGIN_CHARGING_RETRY_TIME)

    def run_once(self):
        """Execute the main body of the test.
        """
        if not self.check_ec_capability(['battery', 'charging']):
            raise error.TestNAError(
                    "Nothing needs to be tested on this device")
        if not self._get_battery_charging_allowed(
        ) or self._get_battery_actual_current() < 0:
            logging.info(
                    "Battery is full or discharging. Forcing battery discharge to test charging."
            )
            self._discharge_below_100()
            if not self._get_battery_charging_allowed():
                raise error.TestFail(
                        'Battery reports charging is not allowed, even after discharging.'
                )
        if self._check_if_discharge_on_ac():
            raise error.TestNAError(
                    "DUT is performing discharge on AC. Unable to test.")
        if self._get_trickle_charging():
            raise error.TestNAError(
                    "Trickling charging battery. Unable to test.")
        if self._get_battery_actual_current() < 0:
            raise error.TestFail(
                    "The device is not charging. Is the test run with AC plugged?"
            )

        logging.info("Checking charger target values...")
        self._check_target_value()

        logging.info("Checking battery actual values...")
        self._check_actual_value()
